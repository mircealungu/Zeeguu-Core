def match(key, value):
    return {"match": {key: value}}


def add_to_dict(dict, key, value):
    dict.update({key: value})


def build_more_like_this_query(count, content, language):
    query_body = {"size": count, "query": {"bool": {}}}  # initial empty query

    must = []

    if language:
        more_like_this = {}
        add_to_dict(more_like_this, "fields", ["content", "title"])
        add_to_dict(more_like_this, "like", content)
        add_to_dict(more_like_this, "min_term_freq", 2)
        add_to_dict(more_like_this, "max_query_terms", 25)
        must.append({'more_like_this': more_like_this})

        must.append(match("language", language))

    query_body["query"]["bool"].update({"must": must})
    return query_body