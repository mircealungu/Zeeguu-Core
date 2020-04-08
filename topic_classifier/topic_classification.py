from operator import itemgetter

def get_best_category(response):
    topics = {}
    for hit in response['hits']['hits']:
        score = hit['_score']
        for topic in hit['_source']['topic']:
            if topic not in topics:
                topics[topic] = score
            else:
                topics[topic] += score

    if len(topics) > 0:
        sorted_categories = sorted(topics.items(), key=itemgetter(1), reverse=True)
        topic = sorted_categories[0][0]

    return topic