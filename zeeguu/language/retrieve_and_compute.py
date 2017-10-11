from zeeguu.content_retriever.parallel_retriever import get_content_for_urls
import zeeguu


def retrieve_urls_and_compute_metrics(urls, language, user, timeout=10):
    urls_and_metrics = {}
    content_and_urls = get_content_for_urls(urls, language.id, timeout)

    for each in content_and_urls:
        try:

            if len(each['content']) > 300:
                # this 500 characters limit assumes that shorter
                # articles are not actually "articles" but probably
                # parser mistakes
                difficulty = user.text_difficulty(each['content'], language)
                # print(f'url: {each} / diff: {difficulty}')
                urls_and_metrics[each['url']] = {
                    'difficulty': {
                        'normalized': difficulty['normalized'],
                        'discrete': difficulty['discrete'],
                        'average': difficulty['score_average']
                    }
                }
            else:
                zeeguu.log("ATTN!: since size is only {0} will not return {1}".
                           format(len(each['content']), each['url']))
        except Exception as e:
            print("Failed while trying to compute difficulty for " + each['url'])
            print(str(e))

    return urls_and_metrics
