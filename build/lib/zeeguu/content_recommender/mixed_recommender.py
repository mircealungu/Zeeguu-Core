"""

 Recommends a mix of articles from all the sources


"""
from zeeguu import log
from zeeguu.model import RSSFeedRegistration, UserArticle, Article, User, Bookmark, Language, \
    UserLanguage, TopicSubscription, TopicFilter, SearchSubscription, SearchFilter, article_word


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

    user_topics = TopicSubscription.topics_for_user(user)
    user_filters = TopicFilter.topics_for_user(user)
    user_searches = SearchSubscription.search_subscriptions_for_user(user)
    user_search_filters = SearchFilter.search_filters_for_user(user)

    topic_articles = []
    if len(user_topics) > 0:
        for sub in user_topics:
            topic = sub.topic
            new_articles = topic.all_articles()
            topic_articles.extend(new_articles)

    filter_articles = []
    if len(user_filters) > 0:
        for filt in user_filters:
            topic = filt.topic
            new_articles = topic.all_articles()
            filter_articles.extend(new_articles)

    search_articles = []
    if len(user_searches) > 0:
        for user_search in user_searches:
            search = user_search.search
            new_articles = search.all_articles()
            search_articles.extend(new_articles)

    search_filter_articles = []
    if len(user_search_filters) > 0:
        for user_search_filter in user_search_filters:
            search = user_search_filter.search
            new_articles = search.all_articles()
            search_filter_articles.extend(new_articles)

    filter_articles.extend(search_filter_articles)

    if len(topic_articles) > 0:
        if len(search_articles) > 0:
            all_filter_articles = [article for article in topic_articles if article in search_articles]
        else:
            all_filter_articles = topic_articles
    else:
        all_filter_articles = search_articles
    all_articles = get_user_articles_sources_languages(user)

    if len(all_filter_articles) > 0:
        filtered_articles = [article for article in all_filter_articles if article in all_articles]
    else:
        filtered_articles = all_articles

    final = [article for article in filtered_articles if article not in filter_articles]

    log('Sorting articles...')
    #final.sort(key=lambda each: each.published_time, reverse=True)
    final.sort(key=lambda each: each.content, reverse=False)
    log('Sorted articles')

    return [user_article_info(user, article) for article in final[:count]]


def article_search_for_user(user, count, search):
    """


    Retrieve the articles :param user: requested which fit the :param search:
    profile, for the selected sources of the user.

    :return:

    """

    all_articles = get_user_articles_sources_languages(user)
    # Sort them, so the first 'count' articles will be the most recent ones
    all_articles.sort(key=lambda each: each.published_time)

    # For now we just look in the url and title, url being first, title being second.
    search_articles = article_word.get_articles_for_word(search)

    final = [article for article in search_articles if article in all_articles]
    return [user_article_info(user, article) for article in final[:count]]


def search_render_articles(user, count, search):

    all_articles = get_user_articles_sources_languages(user)
    # Sort them, so the first 'count' articles will be the most recent ones
    all_articles.sort(key=lambda each: each.published_time)

    search_filtered_articles = []
    log(f'Getting articles with {search} in url')
    counter = 0
    for article in all_articles:
        if search in article.url.as_string() or search in article.title:
            search_filtered_articles.append(article)
            counter += 1
        if counter > count:
            break

    return [user_article_info(user, article) for article in search_filtered_articles[:count]]


def filter_render_articles(user, count, search):

    all_articles = get_user_articles_sources_languages(user)
    # Sort them, so the first 'count' articles will be the most recent ones
    all_articles.sort(key=lambda each: each.published_time)

    search_filtered_articles = []
    log(f'Getting articles with {search} in url')
    counter = 0
    for article in all_articles:
        if search not in article.url.as_string() and search not in article.title:
            search_filtered_articles.append(article)
            counter += 1
        if counter > count:
            break

    return [user_article_info(user, article) for article in search_filtered_articles[:count]]


def get_user_articles_sources_languages(user):
    """

    This method is used to get all the user articles for the sources if there are any
    selected sources for the user, and it otherwise gets all the articles for the
    current learning languages for the user.

    :param user: the user for which the articles should be fetched
    :return: a list of articles based on the parameters
    """

    user_sources = RSSFeedRegistration.feeds_for_user(user)
    user_languages = UserLanguage.get_all_user_languages(user)
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
