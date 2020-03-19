"""

 Mixed recommender that uses elasticsearch for searching.
 still uses MySQL to find relations, between the user and things such as:
    topics, language and user subscriptions.


"""

from elasticsearch import Elasticsearch

from zeeguu_core.model import Article, User, Bookmark, \
    UserLanguage, TopicFilter, TopicSubscription, SearchFilter, \
    SearchSubscription, ArticleWord, ArticlesCache, full_query
from sortedcontainers import SortedList
from zeeguu_core.util.timer_logging_decorator import time_this


def article_recommendations_for_user(user, count):
    """

            Retrieve :param count articles which are equally distributed
            over all the feeds to which the :param user is registered to.

            Fails if no language is selected.

    :return:

    """

    import zeeguu_core

    user_languages = UserLanguage.all_reading_for_user(user)
    if not user_languages:
        return []

    reading_pref_hash = reading_preferences_hash(user)
    recompute_recommender_cache_if_needed(user, zeeguu_core.db.session)

    all_articles = ArticlesCache.get_articles_for_hash(reading_pref_hash, count)
    all_articles = [each for each in all_articles if (not each.broken
                                                      and each.published_time)]
    all_articles = SortedList(all_articles, lambda x: x.published_time)

    return [user_article_info(user, article) for article in reversed(all_articles)]


def recompute_recommender_cache_if_needed(user, session):
    """

            This method first checks if there is an existing hash for the
            user's content selection, and if so, is done. If non-existent,
            it retrieves all the articles corresponding with this configuration
            and stores them as ArticlesCache objects.

    :param user: To retrieve the subscriptions of the user
    :param session: Needed to store in the db

    """

    reading_pref_hash = reading_preferences_hash(user)
    print(f"Pref hash: {reading_pref_hash}")

    articles_hash_obj = ArticlesCache.check_if_hash_exists(reading_pref_hash)

    if articles_hash_obj is False:
        print("recomputing recommender cache!")
        recompute_recommender_cache(reading_pref_hash, session, user)
    else:
        print("no need to recomputed recommender cache!")


def recompute_recommender_cache(reading_preferences_hash_code, session, user):
    """

    :param reading_preferences_hash_code:
    :param session:
    :param user:

    :return:
    """
    all_articles = find_articles_for_user(user)

    for art in all_articles:
        cache_obj = ArticlesCache(art, reading_preferences_hash_code)
        session.add(cache_obj)
        session.commit()


def find_articles_for_user(user):
    """
    This method gets all the topic and search subscriptions for a user.
    It then returns all the articles that are associated with these.

    :param user:
    :return:
    """

    user_languages = UserLanguage.all_reading_for_user(user)

    topic_subscriptions = TopicSubscription.all_for_user(user)

    search_subscriptions = SearchSubscription.all_for_user(user)

    subscribed_articles = filter_subscribed_articles(search_subscriptions, topic_subscriptions, user_languages, user)

    return subscribed_articles


@time_this
def article_search_for_user(user, count, search_terms):
    """
    A method that handles all types of searches.
    Retrieve the articles from elasticsearch and find the relational values from the DB and return them
    :param user: requested which fit the
    :param search: profile, for the selected sources of the user.

    :return: articles

    """

    es = Elasticsearch(["127.0.0.1:9200"])

    user_languages = UserLanguage.all_reading_for_user(user)

    topic_subscriptions = TopicSubscription.all_for_user(user)

    search_subscriptions = SearchSubscription.all_for_user(user)
    user_search_filters = SearchFilter.all_for_user(user)

    if len(user_languages) == 0:
        return []

    # TODO: shouldn't this be passed down from upstream?
    per_language_article_count = count / len(user_languages)

    final_article_mix = []
    for language in user_languages:
        print(f"language: {language}")

        # 0. Ensure appropriate difficulty
        declared_level_min, declared_level_max = user.levels_for(language)
        lower_bounds = declared_level_min * 10
        upper_bounds = declared_level_max * 10

        # 1. Keywords to exclude
        # ==============================
        keywords_to_avoid = []
        for user_search_filter in user_search_filters:
            keywords_to_avoid.append(user_search_filter.search.keywords)
        print(f"keywords to exclude: {keywords_to_avoid}")

        # 2. Topics to exclude / filter out
        # =================================
        user_filters = TopicFilter.all_for_user(user)
        to_exclude_topic_ids = [each.topic.id for each in user_filters]
        print(f"to exlcude topic ids: {to_exclude_topic_ids}")
        print(f"topics to exclude: {user_filters}")

        # 3. Topics subscribed, and thus to include
        # =========================================
        ids_of_topics_to_include = [subscription.topic.id for subscription in topic_subscriptions]
        print(f"topics to include: {topic_subscriptions}")
        print(f"topics ids to include: {ids_of_topics_to_include}")

        # queries through ElasticSearch with the original parameters and criteria.
        #
        string_of_topics = list_to_string(ids_of_topics_to_include)
        string_of_unwanted_topics = list_to_string(to_exclude_topic_ids)
        string_of_user_topics = list_to_string(search_subscriptions)
        string_of_unwanted_user_topics = list_to_string(user_search_filters)
        query_body = full_query(per_language_article_count, search_terms, string_of_topics, string_of_unwanted_topics,
                                string_of_user_topics, string_of_unwanted_user_topics, language, upper_bounds,
                                lower_bounds)

        res = es.search(index="zeeguu", body=query_body)

        hit_list = res['hits'].get('hits')
        final_article_mix.extend(to_articles_from_ES_hits(hit_list))

    # Sort them, so the first 'count' articles will be the most recent ones
    final_article_mix.sort(key=lambda each: each.published_time, reverse=True)
    # convert to result Dicts and return
    return [user_article_info(user, article) for article in final_article_mix]


@time_this
def filter_subscribed_articles(search_subscriptions, topic_subscriptions, user_languages, user):
    """
    :param search_subscriptions:
    :param topic_subscriptions:
    :param user_languages:
    :param user:
    :return:

            finds all relevant topics, user subs, language and searches in elasticsearch with this information

    """

    user_search_filters = SearchFilter.all_for_user(user)

    if len(user_languages) == 0:
        return []

    # TODO: shouldn't this be passed down from upstream?
    total_article_count = 30
    per_language_article_count = total_article_count / len(user_languages)

    final_article_mix = []
    for language in user_languages:
        print(f"language: {language}")

        # 0. Ensure appropriate difficulty
        declared_level_min, declared_level_max = user.levels_for(language)
        lower_bounds = declared_level_min * 10
        upper_bounds = declared_level_max * 10

        # 1. Keywords to exclude
        # ==============================
        keywords_to_avoid = []
        for user_search_filter in user_search_filters:
            keywords_to_avoid.append(user_search_filter.search.keywords)
        print(f"keywords to exclude: {keywords_to_avoid}")

        # 2. Topics to exclude / filter out
        # =================================
        user_filters = TopicFilter.all_for_user(user)
        to_exclude_topic_ids = [each.topic.id for each in user_filters]
        print(f"to exlcude topic ids: {to_exclude_topic_ids}")
        print(f"topics to exclude: {user_filters}")

        # 3. Topics subscribed, and thus to include
        # =========================================
        ids_of_topics_to_include = [subscription.topic.id for subscription in topic_subscriptions]
        print(f"topics to include: {topic_subscriptions}")
        print(f"topics ids to include: {ids_of_topics_to_include}")

        # TODO is this needed? it updates articleword but have nothing to do with the search
        # 4. Searches to include
        # ======================
        print(f"Search subscriptions: {search_subscriptions}")
        ids_for_articles_containing_search_terms = set()
        for user_search in search_subscriptions:
            search_string = user_search.search.keywords.lower()
            print(search_string)

            articles_for_word = ArticleWord.get_articles_for_word(search_string)
            print(articles_for_word)
            ids_for_articles_containing_search_terms.update([article.id for article in articles_for_word])
        print(ids_for_articles_containing_search_terms)

        # queries through ElasticSearch with the original parameters and criteria.
        topic_ids_include = list_to_string(ids_of_topics_to_include)
        topic_ids_exclude = list_to_string(to_exclude_topic_ids)
        user_subscriptions = list_to_string(search_subscriptions)
        user_filters_string = list_to_string(user_filters)

        query_body = full_query(20, None, topic_ids_include, topic_ids_exclude, user_subscriptions,
                                user_filters_string, language, upper_bounds, lower_bounds)

        es = Elasticsearch(["127.0.0.1:9200"]) #TODO dont use localhost IP
        res = es.search(index="zeeguu_articles", body=query_body)

        hit_list = res['hits'].get('hits')
        final_article_mix.extend(to_articles_from_ES_hits(hit_list))
    return set(final_article_mix)
    # return final_article_mix


def user_article_info(user: User, article: Article, with_content=False, with_translations=True):
    from zeeguu_core.model import UserArticle
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


def list_to_string(list):
    tmp = ""
    for ele in list:
        tmp = tmp + str(ele) + " "
    return tmp.rstrip()


def to_articles_from_ES_hits(hits):
    articles = []
    for hit in hits:
        articles.append(from_article_id_to_article(hit.get("_id")))
    return articles


def from_article_id_to_article(id):
    return Article.query.filter(Article.id == id).first()


def reading_preferences_hash(user):
    """

            Method to retrieve the hash, as this is done several times.

    :param user:
    :return: articles_hash: ArticlesHash

    """
    user_filter_subscriptions = TopicFilter.all_for_user(user)
    filters = [topic_id.topic for topic_id in user_filter_subscriptions]

    user_topic_subscriptions = TopicSubscription.all_for_user(user)
    topics = [topic_id.topic for topic_id in user_topic_subscriptions]

    user_languages = UserLanguage.all_user_languages__reading_for_user(user)

    user_search_filters = SearchFilter.all_for_user(user)

    search_filters = [search_id.search for search_id in user_search_filters]
    user_searches = SearchSubscription.all_for_user(user)

    searches = [search_id.search for search_id in user_searches]

    articles_hash = ArticlesCache.calculate_hash(topics, filters, searches, search_filters, user_languages)

    return articles_hash
