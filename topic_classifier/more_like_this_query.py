def match(key, value):
    return {"match": {key: value}}


def add_to_dict(dict, key, value):
    dict.update({key: value})


def more_like_this_query_build(count, search_terms):
    query_body = {"size": count, "query": {"more_like_this": {}}}  # initial empty query

    more_like_this = {}
    add_to_dict(more_like_this, "fields", ["content", "title"])
    add_to_dict(more_like_this, "like", search_terms)
    add_to_dict(more_like_this, "min_term_freq", 1)
    add_to_dict(more_like_this, "max_query_terms", 25)

    query_body["query"]["bool"].update(more_like_this)

    return query_body
