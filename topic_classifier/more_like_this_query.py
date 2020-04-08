def match(key, value):
    return {"match": {key: value}}


def add_to_dict(dict, key, value):
    dict.update({key: value})


# def find_empty_topics():
#     query_body = {"query": {"more_like_this": {"match": {"topics": []}}}}  # initial empty query
#     return query_body


# def more_like_this_query_build(search_terms):
#     query_body = {"query": {"more_like_this": {}}}  # initial empty query
#
#     more_like_this = {}
#     add_to_dict(more_like_this, "fields", ["content", "title"])
#     add_to_dict(more_like_this, "like", search_terms)
#     add_to_dict(more_like_this, "min_term_freq", 5)
#     add_to_dict(more_like_this, "max_query_terms", 100)
#
#     query_body["query"]["more_like_this"].update(more_like_this)
#
#     return query_body

def build_more_like_this_query(count, search_terms, language):
    query_body = {"size": count, "query": {"bool": {}}}  # initial empty query

    must = []

    if language:
        more_like_this = {}
        add_to_dict(more_like_this, "fields", ["content", "title"])
        add_to_dict(more_like_this, "like", search_terms)
        add_to_dict(more_like_this, "min_term_freq", 1)
        add_to_dict(more_like_this, "max_query_terms", 25)
        must.append({'more_like_this': more_like_this})

        must.append(match("language", language.name))

    query_body["query"]["bool"].update({"must": must})
    return query_body