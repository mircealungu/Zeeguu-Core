
def match(key, value):
    return {"match": {key: value}}


def build_elastic_query(count, search_terms, topics, unwanted_topics, user_topics, unwanted_user_topics, language, upper_bounds,
                        lower_bounds):
    """

        Builds an elastic search query.
        Does this by building a big JSON object.

        Example of a final query body:
        {'size': 20.0, 'query':
            {'bool':
                {
                'filter':
                    {
                    'range':
                        {
                        'fk_difficulty':
                            {
                            'gt': 0,
                             'lt': 100
                             }
                        }
                    },
                'should': [
                    {'match': {'topics': 'Sport'}},
                    {'match': {'content': 'soccer ronaldo'}},
                    {'match': {'title': 'soccer ronaldo'}}
                ],
                'must': [
                    {'match': {'language': 'English'}}
                ],
                'must_not': [
                    {'match': {'topics': 'Health'}},
                    {'match': {'content': 'messi'}},
                    {'match': {'title': 'messi'}}
                    ]
                }
            }
        }

    """

    # must = mandatory, has to occur
    # must not = has to not occur
    # should = nice to have (extra points if it matches)
    must = []
    must_not = []
    should = []

    query_body = {"size": count, "query": {"bool": {}}}  # initial empty query

    if language:
        must.append(match("language", language.name))

    if topics:
        should.append(match("topics", topics))

    if not search_terms:
        search_terms = ""

    if not user_topics:
        user_topics = ""

    if search_terms or user_topics:
        search_string = search_terms + " " + user_topics
        should.append(match("content", search_string))
        should.append(match("title", search_string))

    if unwanted_topics:
        must_not.append(match("topics", unwanted_topics))

    if unwanted_user_topics:
        must_not.append(match("content", unwanted_user_topics))
        must_not.append(match("title", unwanted_user_topics))

    # add the must, must_not and should lists to the query body
    query_body["query"]["bool"].update({"filter": {"range": {"fk_difficulty": {"gt": lower_bounds, "lt": upper_bounds}}}})

    query_body["query"]["bool"].update({"should": should})
    query_body["query"]["bool"].update({"must": must})
    query_body["query"]["bool"].update({"must_not": must_not})

    return query_body
