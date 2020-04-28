"""

 Recommender that uses elasticsearch instead of mysql for searching. Based on mixed recommender.
 still uses MySQL to find relations between the user and things such as:
   - topics, language and user subscriptions.

"""

from elasticsearch import Elasticsearch
from sqlalchemy.orm.exc import NoResultFound

from zeeguu_core.model import Article, User, Bookmark, \
    UserLanguage, TopicFilter, TopicSubscription, SearchFilter, \
    SearchSubscription, UserArticle, Cohort, CohortArticleMap
from elastic.elastic_query_builder import build_elastic_query, build_more_like_this_query
from zeeguu_core.util.timer_logging_decorator import time_this
from zeeguu_core.settings import ES_CONN_STRING, ES_ZINDEX


def more_like_this_article(user, count, article_id):
    """
        Given a article ID find more articles like that one via Elasticsearchs "more_like_this" method

    """
    article = fetch_article_by_ID(article_id)

    query_body = build_more_like_this_query(count, article.content, article.language)

    es = Elasticsearch(ES_CONN_STRING)
    res = es.search(index=ES_ZINDEX, body=query_body)  # execute search
    hit_list = res['hits'].get('hits')

    # TODO need to make sure either that the searched on article is always a part of the list \
    #  or that it is never there.
    #  it could be used to show on website; you searched on X, here is what we found related to X

    final_article_mix = to_articles_from_ES_hits(hit_list)
    return [user_article_info(user, article) for article in final_article_mix]


def article_recommendations_for_user(user, count):
    """

            Retrieve :param count articles which are equally distributed
            over all the feeds to which the :param user is registered to.

            Fails if no language is selected.

    :return:

    """

    articles = article_search_for_user(user, count, "")

    return articles


@time_this
def article_search_for_user(user, count, search_terms):
    """
    Handles searching.
    Find the relational values from the database and use them to search in elasticsearch for relative articles.

    :param user:
    :param count: max amount of articles to return
    :param search_terms: the inputed search string by the user
    :return: articles

    """

    user_languages = UserLanguage.all_reading_for_user(user)

    if len(user_languages) == 0:
        return []

    per_language_article_count = count / len(user_languages)

    final_article_mix = []
    for language in user_languages:
        print(f"language: {language}")

        # 0. Ensure appropriate difficulty
        declared_level_min, declared_level_max = user.levels_for(language)
        lower_bounds = declared_level_min * 10
        upper_bounds = declared_level_max * 10

        # 1. Unwanted user topics
        # ==============================
        user_search_filters = SearchFilter.all_for_user(user)
        unwanted_user_topics = []
        for user_search_filter in user_search_filters:
            unwanted_user_topics.append(user_search_filter.search.keywords)
        print(f"keywords to exclude: {unwanted_user_topics}")

        # 2. Topics to exclude / filter out
        # =================================
        excluded_topics = TopicFilter.all_for_user(user)
        topics_to_exclude = [each.topic.title for each in excluded_topics]
        print(f"topics to exclude: {topics_to_exclude}")

        # 3. Topics subscribed, and thus to include
        # =========================================
        topic_subscriptions = TopicSubscription.all_for_user(user)
        topics_to_include = [subscription.topic.title for subscription in TopicSubscription.all_for_user(user)]
        print(f"topics to include: {topic_subscriptions}")

        # 4. Wanted user topics
        # =========================================
        user_subscriptions = SearchSubscription.all_for_user(user)

        wanted_user_topics = []
        for sub in user_subscriptions:
            wanted_user_topics.append(sub.search.keywords)
        print(f"keywords to include: {wanted_user_topics}")

        # build the query using elastic_query_builder
        query_body = build_elastic_query(per_language_article_count,
                                         search_terms,
                                         list_to_string(topics_to_include),
                                         list_to_string(topics_to_exclude),
                                         list_to_string(wanted_user_topics),
                                         list_to_string(unwanted_user_topics),
                                         language,
                                         upper_bounds,
                                         lower_bounds)

        es = Elasticsearch(ES_CONN_STRING)
        res = es.search(index=ES_ZINDEX, body=query_body)

        hit_list = res['hits'].get('hits')
        final_article_mix.extend(to_articles_from_ES_hits(hit_list))

    # convert to article_info and return
    return [user_article_info(user, article) for article in final_article_mix]


# exact same method as in mixed_recommender
def user_article_info(user: User, article: Article, with_content=False, with_translations=True):
    prior_info = UserArticle.find(user, article)

    ua_info = article.article_info(with_content=with_content)

    if not prior_info:
        ua_info['starred'] = False
        ua_info['opened'] = False
        ua_info['liked'] = False
        ua_info['translations'] = []
        return ua_info

    ua_info['starred'] = prior_info.starred is not None
    ua_info['opened'] = prior_info.opened is not None
    ua_info['liked'] = prior_info.liked

    if with_translations:
        translations = Bookmark.find_all_for_user_and_url(user, article.url)
        ua_info['translations'] = [each.serializable_dictionary() for each in translations]

    return ua_info


# exact same method as in mixed_recommender
def cohort_articles_for_user(user):
    try:
        cohort = Cohort.find(user.cohort_id)
        cohort_articles = CohortArticleMap.get_articles_info_for_cohort(cohort)
        return cohort_articles
    except NoResultFound as e:
        return []


def list_to_string(input_list):
    return ' '.join([each for each in input_list]) or ''


def to_articles_from_ES_hits(hits):
    articles = []
    for hit in hits:
        articles.append(fetch_article_by_ID(hit.get("_id")))
    return articles


def fetch_article_by_ID(id):
    return Article.query.filter(Article.id == id).first()
