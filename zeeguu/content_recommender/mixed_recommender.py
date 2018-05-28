"""

 Recommends a mix of articles from all the languages,
 sources, topics, filters, and searches.


"""
from zeeguu import log
import time
from zeeguu.model import RSSFeedRegistration, UserArticle, Article, User, Bookmark, \
    UserLanguage, TopicSubscription, TopicFilter, SearchSubscription, SearchFilter, ArticleWord


def user_article_info(user: User, article: Article, with_content=False):
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

    translations = Bookmark.find_all_for_user_and_url(user, article.url)
    ua_info['translations'] = [each.serializable_dictionary() for each in translations]

    return ua_info


def article_recommendations_for_user(user, count):
    """

            Retrieve :param count articles which are equally distributed
            over all the feeds to which the :param user is registered to.

    :return:

    """
    subscribed_articles = get_subscribed_articles_for_user(user)
    filter_articles = get_filtered_articles_for_user(user)
    all_articles = get_user_articles_sources_languages(user)

    # Get only the articles for the topics and searches subscribed
    if len(subscribed_articles) > 0:
        all_articles = [article for article in subscribed_articles if article in all_articles]

    # If there are any filters, filter out all these articles
    if len(filter_articles) > 0:
        all_articles = [article for article in all_articles if article not in filter_articles]

    log('Sorting articles...')
    all_articles.sort(key=lambda each: each.content, reverse=False)
    log('Sorted articles')

    return [user_article_info(user, article) for article in all_articles[:count]]


def article_search_for_user(user, count, search):
    """


    Retrieve the articles :param user: requested which fit the :param search:
    profile, for the selected sources of the user.

    :return:

    """

    all_articles = get_user_articles_sources_languages(user)
    # Sort them, so the first 'count' articles will be the most recent ones
    all_articles.sort(key=lambda each: each.published_time)

    # We are just using the first word of the user's search now
    search_term = search.split()[0]
    search_articles = ArticleWord.get_articles_for_word(search_term)

    final = [article for article in search_articles if article in all_articles]
    return [user_article_info(user, article) for article in final[:count]]


def get_filtered_articles_for_user(user):
    """

    This method gets all topic and search filters for a user.
    It then returns all the articles that are associated with these.
    :param user:
    :return:

    """
    user_filters = TopicFilter.all_for_user(user)
    user_search_filters = SearchFilter.all_for_user(user)

    filter_articles = []
    if len(user_filters) > 0:
        for filt in user_filters:
            topic = filt.topic
            new_articles = topic.all_articles()
            filter_articles.extend(new_articles)

    if len(user_search_filters) > 0:
        for user_search_filter in user_search_filters:
            search = user_search_filter.search.keywords
            search_term = search.split()[0]
            new_articles = ArticleWord.get_articles_for_word(search_term)
            filter_articles.extend(new_articles)

    return filter_articles


def get_subscribed_articles_for_user(user):
    """

    This method gets all the topic and search subscriptions for a user.
    It then returns all the articles that are associated with these.

    :param user:
    :return:

    """
    user_topics = TopicSubscription.all_for_user(user)
    user_searches = SearchSubscription.all_for_user(user)

    subscribed_articles = []
    if len(user_topics) > 0:
        for sub in user_topics:
            topic = sub.topic
            new_articles = topic.all_articles()
            subscribed_articles.extend(new_articles)

    if len(user_searches) > 0:
        for user_search in user_searches:
            search = user_search.search.keywords
            search_term = search.split()[0]
            new_articles = ArticleWord.get_articles_for_word(search_term)
            subscribed_articles.extend(new_articles)

    return subscribed_articles


def get_user_articles_sources_languages(user):
    """

    This method is used to get all the user articles for the sources if there are any
    selected sources for the user, and it otherwise gets all the articles for the
    current learning languages for the user.

    :param user: the user for which the articles should be fetched
    :return: a list of articles based on the parameters

    """

    user_sources = RSSFeedRegistration.feeds_for_user(user)
    user_languages = UserLanguage.all_for_user(user)
    all_articles = []

    # If there are sources, get the articles from the sources
    if len(user_sources) > 0:
        for registration in user_sources:
            feed = registration.rss_feed
            new_articles = feed.get_articles(user, most_recent_first=True)
            all_articles.extend(new_articles)

    # If there are no sources available, get the articles based on the languages
    else:
        for language in user_languages:
            log(f'Getting articles for {language}')
            new_articles = language.get_articles(most_recent_first=True)
            all_articles.extend(new_articles)
            log(f'Added articles for {language}')

    return all_articles
