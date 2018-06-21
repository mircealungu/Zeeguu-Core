"""

 Recommends a mix of articles from all the languages,
 sources, topics, filters, and searches.


"""
from zeeguu import log
from zeeguu.model import RSSFeedRegistration, UserArticle, Article, User, Bookmark, \
    UserLanguage, TopicSubscription, TopicFilter, SearchSubscription, SearchFilter, ArticleWord, ArticlesCache


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


def recompute_recommender_cash_if_needed(user, session):
    """

            This method first checks if there is an existing hash for the
            user's content selection, and if so, is done. It non-existent,
            it retrieves all the articles corresponding with this configuration
            and stores them as ArticlesCache objects.

    :param user: To retrieve the subscriptions of the user
    :param session: Needed to store in the db

    """
    articles_hash = reading_preferences_hash(user)
    articles_hash_obj = ArticlesCache.check_if_hash_exists(articles_hash)

    if articles_hash_obj is False:
        subscribed_articles = get_subscribed_articles_for_user(user)
        filter_articles = get_filtered_articles_for_user(user)
        all_articles = get_user_articles_sources_languages(user, 1000)

        # Get only the articles for the topics and searches subscribed
        if len(subscribed_articles) > 0:
            s = set(all_articles)
            all_articles = [article for article in subscribed_articles if article in s]

        # If there are any filters, filter out all these articles
        if len(filter_articles) > 0:
            s = set(all_articles)
            all_articles = [article for article in s if article not in filter_articles]

        if len(all_articles) < 10:
            all_articles = get_user_articles_sources_languages(user)

            # Get only the articles for the topics and searches subscribed
            if len(subscribed_articles) > 0:
                s = set(all_articles)
                all_articles = [article for article in subscribed_articles if article in s]

            # If there are any filters, filter out all these articles
            if len(filter_articles) > 0:
                s = set(all_articles)
                all_articles = [article for article in s if article not in filter_articles]

        for article in all_articles:
            cache_obj = ArticlesCache(article, articles_hash)
            session.add(cache_obj)
        session.commit()


def article_recommendations_for_user(user, count):
    """

            Retrieve :param count articles which are equally distributed
            over all the feeds to which the :param user is registered to.

    :return:

    """

    articles_hash = reading_preferences_hash(user)
    all_articles = ArticlesCache.get_articles_for_hash(articles_hash, count)

    log('Sorting articles...')
    all_articles.sort(key=lambda each: each.published_time, reverse=True)
    log('Sorted articles')

    return [user_article_info(user, article) for article in all_articles]


def article_search_for_user(user, count, search):
    """


    Retrieve the articles :param user: requested which fit the :param search:
    profile, for the selected sources of the user.

    :return:

    """

    all_articles = get_user_articles_sources_languages(user, 2500)

    # We are just using the first and second word of the user's search now
    search_articles = get_articles_for_search_term(search)

    if search_articles is None:
        final = []
    else:
        s = set(all_articles)
        final = [article for article in search_articles if article in s]
        if len(final) < 5:
            all_articles = get_user_articles_sources_languages(user)
            s = set(all_articles)
            final = [article for article in search_articles if article in s]

    # Sort them, so the first 'count' articles will be the most recent ones
    final.sort(key=lambda each: each.published_time)

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
            new_articles = get_articles_for_search_term(search)
            if new_articles is not None:
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
            new_articles = get_articles_for_search_term(search)
            if new_articles is not None:
                subscribed_articles.extend(new_articles)

    return subscribed_articles


def get_user_articles_sources_languages(user, limit=100000):
    """

    This method is used to get all the user articles for the sources if there are any
    selected sources for the user, and it otherwise gets all the articles for the
    current learning languages for the user.

    :param user: the user for which the articles should be fetched
    :param limit: the amount of articles for each source or language
    :return: a list of articles based on the parameters

    """

    user_sources = RSSFeedRegistration.feeds_for_user(user)
    user_languages = UserLanguage.all_reading_for_user(user)
    all_articles = []

    # If there are sources, get the articles from the sources
    if len(user_sources) > 0:
        for registration in user_sources:
            feed = registration.rss_feed
            new_articles = feed.get_articles(limit=limit, most_recent_first=True)
            all_articles.extend(new_articles)

    # If there are no sources available, get the articles based on the languages
    else:
        for language in user_languages:
            log(f'Getting articles for {language}')
            new_articles = language.get_articles(limit=limit, most_recent_first=True)
            all_articles.extend(new_articles)
            log(f'Added articles for {language}')

    return all_articles


def get_articles_for_search_term(search_term):
    search_terms = search_term.lower().split()

    if len(search_terms) > 1:
        search_articles_first = ArticleWord.get_articles_for_word(search_terms[0])
        search_articles_second = ArticleWord.get_articles_for_word(search_terms[1])
        if search_articles_first is None or search_articles_second is None:
            return []
        return [article for article in search_articles_first if article in search_articles_second]

    return ArticleWord.get_articles_for_word(search_terms[0])


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
    user_source_subscriptions = RSSFeedRegistration.feeds_for_user(user)
    sources = [rss_feed_id.rss_feed for rss_feed_id in user_source_subscriptions]
    languages = UserLanguage.all_reading_for_user(user)
    user_search_filters = SearchFilter.all_for_user(user)
    search_filters = [search_id.search for search_id in user_search_filters]
    user_searches = SearchSubscription.all_for_user(user)
    searches = [search_id.search for search_id in user_searches]

    # This is done because the articles are retrieved for sources if there are any sources,
    # the languages don't have any effect when there are sources selected.
    if len(user_source_subscriptions) > 0:
        articles_hash = ArticlesCache.calculate_hash(topics, filters, searches, search_filters, sources=sources)
    else:
        articles_hash = ArticlesCache.calculate_hash(topics, filters, searches, search_filters, languages=languages)

    return articles_hash
