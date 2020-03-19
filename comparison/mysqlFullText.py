from sqlalchemy import or_, desc, not_
from sqlalchemy_fulltext import FullText, FullTextMode, FullTextSearch
from zeeguu_core.model import Article


def build_mysql_query(mysql, count, search_terms, topics, unwanted_topics, user_topics, unwanted_user_topics, language,
                      upper_bounds,
                      lower_bounds):
    class FulltextContext(FullText):
        __fulltext_columns__ = ('article.content', 'article.title')

    query = mysql.query(Article)
    # if no user topics wanted or un_wanted we can do NATURAL LANGUAGE mode
    # otherwise do BOOLEAN MODE
    if not unwanted_user_topics and not user_topics:
        boolean_query = False
        if search_terms:
            search = search_terms
            query = mysql.query(Article).filter(FullTextSearch(search, FulltextContext, FullTextMode.NATURAL))
    else:  # build a boolean query instead
        boolean_query = True
        unwanted_user_topics = add_symbol_in_front_of_words('-', unwanted_user_topics)
        user_topics = add_symbol_in_front_of_words('', user_topics)
        search_terms = add_symbol_in_front_of_words('', search_terms)
        search = search_terms + " " + user_topics.strip() + " " + unwanted_user_topics.strip()
        query = mysql.query(Article).filter(FullTextSearch(search, FulltextContext, FullTextMode.BOOLEAN))

    # Language
    query = query.filter(Article.language_id == language.id)

    # Topics
    topic_IDs = split_numbers_in_string(topics)
    topic_conditions = []
    if topic_IDs:
        for ID in topic_IDs:
            topic_conditions.append(Article.Topic.id == ID)
        query = query.filter(or_(*topic_conditions))

    # Unwanted topics
    unwanted_topic_IDs = split_numbers_in_string(unwanted_topics)
    untopic_conditions = []

    if unwanted_topic_IDs:
        for ID in unwanted_topic_IDs:
            untopic_conditions.append(Article.Topic.id != ID)
        query = query.filter(or_(*untopic_conditions))

    # difficulty, upper and lower
    query = query.filter(lower_bounds < Article.fk_difficulty)
    query = query.filter(upper_bounds > Article.fk_difficulty)
    # if boolean search mode in fulltext then order by relevance score
    if boolean_query:
        query = query.order_by(desc(FullTextSearch(search, FulltextContext, FullTextMode.BOOLEAN)))

    return query.limit(count)


def old_mysql_query(mysql, count, search_terms, topics, unwanted_topics, user_topics, unwanted_user_topics, language,
                    upper_bounds,
                    lower_bounds):
    query = mysql.query(Article)

    # unwanted user topics
    if unwanted_user_topics:
        keywords_to_avoid = unwanted_user_topics.split()
        for keyword_to_avoid in keywords_to_avoid:
            query = query.filter(not_(or_(Article.title.contains(keyword_to_avoid),
                                          Article.content.contains(
                                              keyword_to_avoid))))
    # wanted user topics
    if user_topics:
        keywords_to_include = user_topics.split()
        for word in keywords_to_include:
            query = query.filter(or_(Article.title.contains(word),
                                     Article.content.contains(word)))
    # like clause on search terms
    # todo, maybe split terms into seperate like conditions.
    if search_terms:
        search_str = "%" + search_terms + "%"
        query = query.filter(or_(Article.title.like(search_str), Article.content.like(search_str)))

    # Language
    query = query.filter(Article.language_id == language.id)

    # Topics
    topic_IDs = split_numbers_in_string(topics)
    topic_conditions = []
    if topic_IDs:
        for ID in topic_IDs:
            topic_conditions.append(Article.Topic.id == ID)
        query = query.filter(or_(*topic_conditions))

    # Unwanted topics
    unwanted_topic_IDs = split_numbers_in_string(unwanted_topics)
    untopic_conditions = []

    if unwanted_topic_IDs:
        for ID in unwanted_topic_IDs:
            untopic_conditions.append(Article.Topic.id != ID)
        query = query.filter(or_(*untopic_conditions))

    # difficulty, upper and lower
    query = query.filter(lower_bounds < Article.fk_difficulty)
    query = query.filter(upper_bounds > Article.fk_difficulty)

    return query.limit(count)


def add_symbol_in_front_of_words(symbol, input_string):
    words = input_string.split()
    acc = ""
    for word in words:
        acc += symbol + word + " "
    return acc


def split_numbers_in_string(input_string):
    numbers = input_string.split()
    acc = []
    for number in numbers:
        acc.append(int(number))
    return acc
