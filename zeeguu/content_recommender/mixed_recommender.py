"""

 Recommends a mix of articles from all the languages,
 sources, topics, filters, and searches.


"""
from zeeguu import log
from zeeguu.model import RSSFeedRegistration, UserArticle, Article, User, Bookmark, \
    UserLanguage, TopicSubscription, TopicFilter, SearchSubscription, SearchFilter, ArticleWord, ArticlesCache
from sortedcontainers import SortedList


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


def recompute_recommender_cache_if_needed(user, session):
    """

            This method first checks if there is an existing hash for the
            user's content selection, and if so, is done. It non-existent,
            it retrieves all the articles corresponding with this configuration
            and stores them as ArticlesCache objects.

    :param user: To retrieve the subscriptions of the user
    :param session: Needed to store in the db

    """

    reading_pref_hash = reading_preferences_hash(user)
    print(f"pref hash: {reading_pref_hash}")

    articles_hash_obj = ArticlesCache.check_if_hash_exists(reading_pref_hash)

    if articles_hash_obj is False:
        print("recomputing recommender cache!")
        recompute_recommender_cache(reading_pref_hash, session, user)

    print("no need to recomputed recommender cache!")


def recompute_recommender_cache(reading_preferences_hash_code, session, user, article_limit=42):
    """

    :param reading_preferences_hash_code:
    :param session:
    :param user:

    :param article_limit: set to something low ... say 42 when working in real time... ti's
    a bit slow otherwise. however, when caching offline you can save

    :return:
    """
    all_articles = find_articles_for_user(user)

    print("caching the stuff... ")
    count = 0
    while count < article_limit:
        count += 1
        try:
            art = next(all_articles)
            print(art)
            cache_obj = ArticlesCache(art, reading_preferences_hash_code)
            session.add(cache_obj)
        except StopIteration as e:
            print("couldn't find even ten...")
        finally:
            session.commit()
    print("cached all these things...")


def article_recommendations_for_user(user, count):
    """

            Retrieve :param count articles which are equally distributed
            over all the feeds to which the :param user is registered to.

            Fails if no language is selected.

    :return:

    """

    import zeeguu

    user_languages = UserLanguage.all_reading_for_user(user)
    if not user_languages:
        return []

    reading_pref_hash = reading_preferences_hash(user)
    recompute_recommender_cache_if_needed(user, zeeguu.db.session)
    all_articles = ArticlesCache.get_articles_for_hash(reading_pref_hash, count)

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
    final.sort(key=lambda each: each.published_time, reverse=True)

    return [user_article_info(user, article) for article in final[:count]]


def find_articles_for_user(user):
    """

    This method gets all the topic and search subscriptions for a user.
    It then returns all the articles that are associated with these.

    :param user:
    :return:

    """

    user_languages = UserLanguage.all_reading_for_user(user)
    print(user_languages)

    topic_subscriptions = TopicSubscription.all_for_user(user)
    print(topic_subscriptions)

    search_subscriptions = SearchSubscription.all_for_user(user)
    print(search_subscriptions)

    user_search_filters = SearchFilter.all_for_user(user)
    print(user_search_filters)

    user_filters = TopicFilter.all_for_user(user)
    print(user_filters)

    subscribed_articles = get_subscribed_articles_list(search_subscriptions, topic_subscriptions)

    subscribed_articles = filter_subscribed_articles(subscribed_articles, user_filters, user_languages,
                                                     user_search_filters)

    return subscribed_articles


def filter_subscribed_articles(subscribed_articles, user_filters, user_languages, user_search_filters):
    """
    :param subscribed_articles:
    :param user_filters:
    :param user_languages:
    :param user_search_filters:
    :return:

            a generator which retrieves articles as needed

    """
    keywords_to_avoid = []
    for user_search_filter in user_search_filters:
        keywords_to_avoid.append(user_search_filter.search.keywords)

    subscribed_articles = (each for each in subscribed_articles if
                           (each.language in user_languages)
                           and (each.topics not in user_filters)
                           and not (each.contains_any_of(keywords_to_avoid)))
    return subscribed_articles


def get_subscribed_articles_list(search_subscriptions, topic_subscriptions):

    subscribed_articles = SortedList(key=lambda x: -x.id)
    if not topic_subscriptions and not search_subscriptions:

        print("no user topics or searches... we considerall the possible articles ... actually 2K should suffice")
        subscribed_articles.update([each for each in Article.query.order_by(Article.published_time.desc()).limit(2000)])
    else:

        for sub in topic_subscriptions:
            subscribed_articles.update(sub.topic.all_articles())

        for user_search in search_subscriptions:
            search = user_search.search.keywords
            subscribed_articles.update(get_articles_for_search_term(search))

    return subscribed_articles


def get_user_articles_sources_languages(user, limit=1000):
    """

    This method is used to get all the user articles for the sources if there are any
    selected sources for the user, and it otherwise gets all the articles for the
    current learning languages for the user.

    :param user: the user for which the articles should be fetched
    :param limit: the amount of articles for each source or language
    :return: a list of articles based on the parameters

    """

    user_languages = UserLanguage.all_reading_for_user(user)
    all_articles = []

    for language in user_languages:
        log(f'Getting articles for {language}')
        new_articles = language.get_articles(most_recent_first=True)
        all_articles.extend(new_articles)
        log(f'Added {len(new_articles)} articles for {language}')

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

    articles_hash = ArticlesCache.calculate_hash(topics, filters, searches, search_filters, languages=languages,
                                                 sources=sources)

    return articles_hash
