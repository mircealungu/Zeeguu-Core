from elasticsearch import Elasticsearch
from zeeguu_core.util.timer_logging_decorator import time_this


def full_query(count, search_terms, topics, unwanted_topics, user_topics, unwanted_user_topics, language, upper_bounds,
               lower_bounds):
    query_body = {"size": count, "query": {"bool": {}}}
    if language:
        query_body["query"]["bool"].update({"must":{"match":{"language": language.name}}})

    query_body["query"]["bool"].update({"should": []})
    if topics:
        query_body["query"]["bool"]["should"].append({"match": {"topics": topics}})

    if search_terms:
        if not user_topics:
            user_topics = ""
        query_body["query"]["bool"]["should"].append({"match":{"content": search_terms + " " + user_topics}})
        query_body["query"]["bool"]["should"].append({"match": {"title": search_terms + " " + user_topics}})

    query_body["query"]["bool"].update({"must_not": []})

    if unwanted_topics:
        query_body["query"]["bool"]["must_not"].append({"match":{"topics": unwanted_topics}})

    if unwanted_user_topics:
        query_body["query"]["bool"]["must_not"].append({"match": {"content": unwanted_user_topics}})
        query_body["query"]["bool"]["must_not"].append({"match": {"title": unwanted_user_topics}})

    query_body["query"]["bool"].update({"filter": {"range": {"fk_difficulty": {"gt": lower_bounds, "lt": upper_bounds}}}})

    return query_body
