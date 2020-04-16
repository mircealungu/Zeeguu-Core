import csv
import os

import zeeguu_core
from elastic import elastic_query_builder
from operator import itemgetter
from elasticsearch import Elasticsearch
from topic_classifier.more_like_this_query import build_more_like_this_query
from elastic.converting_from_mysql import find_topics
from zeeguu_core.model import article, Topic
from elastic.elastic_query_builder import build_elastic_query
from sqlalchemy.orm import sessionmaker
from zeeguu_core.settings import ES_ZINDEX, ES_CONN_STRING
import sqlalchemy as database
from zeeguu_core.model.article import article_topic_map, Article

es = Elasticsearch([ES_CONN_STRING])
DB_URI = zeeguu_core.app.config["SQLALCHEMY_DATABASE_URI"]
engine = database.create_engine(DB_URI, encoding='utf8')
Session = sessionmaker(bind=engine)
session = Session()


def find_articles_with_topics(topic='', combine=False):
    # find articles for a specific topic,
    found_topic = session.query(Topic).filter(Topic.title == topic).first()
    articles = session.query(Article).filter(
         Article.id.in_(session.query(article_topic_map.c.article_id).filter(article_topic_map.c.topic_id == found_topic.id))).all()

    # group articles by language
    article_dict = {}
    for art in articles:
        if art.language.name in article_dict.keys():
            article_dict[art.language.name].append(art)
        else:
            article_dict[art.language.name] = [art]

    if not combine:
        for key in article_dict.keys():
            for art in article_dict[key]:
                get_more_like_this_results(art.content, art.language, art.topics, art.id)

    else:
        # combine content from all articles into one big
        for key in article_dict.keys():
            (content, language, topics) = combine_articles_into_one(article_dict[key][:50])
            get_more_like_this_results(content, language, topics, 50)


def combine_articles_into_one(articles):
    new_content = ""
    first_article = articles[0]
    for i in range(0, len(articles)):
        new_content = new_content + " " + articles[i].content
    return new_content, first_article.language, first_article.topics,


def get_more_like_this_results(content, language, topics, original_id=0, count=10):
    query_body = build_more_like_this_query(count, content, language.name)

    res = es.search(index=ES_ZINDEX, body=query_body)
    for result in res['hits']['hits']:
        # if more_like_this result DONT have a topic, assign topic to it based on the article
        #if not result['_source']['topics']:
        assign_topic(result, topics, original_id)


def assign_topic(result, input_topics, original_id):
    topics = ""

    for t in input_topics:
        topics = topics + str(t.title) + " "
        # topics = topics + str(t["title"]) + " "

    topics = topics.rstrip()

    # update elastic_search doc with the topics
    res = es.update(index=ES_ZINDEX, doc_type='_doc', id=result['_id'], body={"doc": {"elastic_topics": topics}})
    print(res['result'] + ": " + str(result['_id']))

    write_results_to_csv(result['_id'], topics, result['_score'], result['_source']['title'], original_id)


def write_results_to_csv(article_id, best_topic, best_score, title, original_id):
    file_name = 'best_topics_title.csv'
    file_exists = os.path.isfile(file_name)

    with open("best_topics_title.csv", 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Original ID', 'Article ID', "Best Topic", "Best Topic Score", "Title"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        writer.writerow({'Original ID': original_id,
            'Article ID': article_id,
                         'Best Topic': best_topic, 'Best Topic Score': best_score, 'Title': title})


# def get_best_topic(response):
#     topics = {}
#     for hit in response['hits']['hits']:
#         score = hit['_score']
#         if 'topics' in hit['_source']:
#             for topic in hit['_source']['topics'].split():
#                 if topic not in topics:
#                     topics[topic] = score
#                 else:
#                     topics[topic] += score
#
#     sorted_topics = {}
#     if len(topics) > 0:
#         sorted_topics = sorted(topics.items(), key=itemgetter(1), reverse=True)
#
#     return sorted_topics


# def assign_topic(article, sorted_topics):
#     if not sorted_topics:
#         return
#
#     if len(sorted_topics) is 1:
#         best_topic = sorted_topics[0][0]
#         best_score = sorted_topics[0][1]
#         second_best_topic = 0
#         second_best_topic_score = 0
#     else:
#         best_topic = sorted_topics[0][0]
#         best_score = sorted_topics[0][1]
#         second_best_topic = sorted_topics[1][0]
#         second_best_topic_score = sorted_topics[1][1]
#
#     res = es.update(index=ES_ZINDEX, doc_type='_doc', id=article.id, body={"doc": {"topics": sorted_topics[0][0]}})
#     print(res['result'] + str(article.id))
#
#
#     write_results_to_csv(article.id, best_topic, best_score,
#                          second_best_topic, second_best_topic_score)


# def write_results_to_csv(article_id, best_topic, best_score, second_best_topic, second_best_topic_score):
#     file_name = 'best_topics_title_music_many_small.csv'
#     file_exists = os.path.isfile(file_name)
#
#     with open("best_topics_title_music_many_small.csv", 'a', newline='', encoding='utf-8') as csvfile:
#         fieldnames = ['Article ID', "Best Topic", "Best Topic Score", "Second Best Topic",
#                       "Second Best Topic Score"]
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#         if not file_exists:
#             writer.writeheader()
#
#         writer.writerow({'Article ID': article_id,
#                          'Best Topic': best_topic, 'Best Topic Score': best_score,
#                          'Second Best Topic': second_best_topic, 'Second Best Topic Score': second_best_topic_score})


def main():
     find_articles_with_topics("Sport", combine=True)

    # MEGA HARDCODED
    # content = "2018 was the year that Big Tech’s mission statements came back to haunt it. When employees felt that their products were damaging the world and that management wouldn't listen, they went public with their protests. At Google and Amazon, they challenged contracts to sell artificial intelligence and facial-recognition technology to the Pentagon and police. At Microsoft and Salesforce, workers argued against selling cloud computing services to agencies separating families at the border.\n\nTechnology’s unintended consequences were also central to the most disruptive labor action in the Bay Area this year, a strike by nearly 8,000 Marriott employees, including many in downtown San Francisco, just a dockless scooter ride from the headquarters of many major tech firms. Unite Here, the union representing strikers in eight cities, including San Jose and Oakland, demanded limits on automation like facial recognition at the front desk or the use of Alexa in lieu of a concierge. Marriott agreed to notify workers 150 days before implementing new technology and to give workers committee representation while the technology is still in development, among other protections.\n\nUnion organizers say they wouldn’t have won the changes without the strike, which lasted two months. When Google employees and contractors briefly stepped away from their desks to protest the company’s policies on sexual harassment on November 1, Marriott workers in San Francisco had already been striking for 27 days, with 32 days still ahead of them—just like Marriott workers in San Jose, where Google plans to build a controversial new mega-campus.\n\nBoth the highly paid engineers and the low-paid housekeepers want a seat at the table when it comes to deploying technology. Both sets of workers are also demanding changes in how their employers handle sexual harassment. A week after the walkout, Google tweaked its arbitration policy for sexual harassment claims. Facebook, Airbnb, and Square soon followed. In Marriott’s case, the union secured GPS-enabled silent panic buttons for all workers and policy changes, like removing and banning guests who harass women, and the right not to serve a guest who they believe harassed them.\n\nIn fact, the parallels between the two high-profile movements—despite vast differences in market power, class, and income—suggest that Google employees’ sense of exceptionalism may be starting to crack, along with illusions about how Google operates. If tech’s moment of reckoning has taught us that Silicon Valley is the same old capitalism, then perhaps Googlers are not a new kind of worker, and maybe some traditional labor rules apply: like the need for collective action in order to make structural change. But the proximity of the Marriott strike also brings into focus both the potential and the limits of the fledgling revolt within Big Tech.\n\nWhen tech workers see that people who get paid way, way, way, way less than they do strike for months, it makes them realize, ‘What the fuck are we doing when we walk out for half an hour?’ says a former Google employee of the Marriott workers. The difference in the last few months has been more people realizing that we are actually better if we organize.\n\nThe public actions that started the year—open letters, petitions, and Medium posts—are ultimately an appeal to a company’s values. But after The New York Times reported that Google gave a $90 million exit package to Android founder Andy Rubin after he was accused of sexual harassment, employees lost faith. Then at a company-wide meeting, executives offered business-as-usual pablum. Disgust was universal enough that the 20,000-person walkout was arranged in just three days.\n\nWant more? Read all of WIRED’s year-end coverage\n\nLast year feels like it was a century ago. So much has changed, says Stephanie Parker, one of the walkout organizers. Seeing the cafeteria workers and security guards at Silicon Valley companies bravely demand access to benefits and respect was a deeply inspiring experience for me and many other tech workers this past year. It helped me to see parallels between the struggles of these service workers and my own experience as a black woman in tech, and also prepared me to identify with the struggles happening in other local industries, like the Marriott hotel strike.\n\nNelson Lichtenstein, a history professor and director of the Center for the Study of Work, Labor, and Democracy at UC Santa Barbara, says that over time, corporate success and growing size tend to create divisions and inequalities. It takes a while. Sometimes it takes a generation, or a little less, for the ordinary person—not the person who’s hired on day one with stock options—to say, ‘Wait a minute, this thing isn’t working for me, and I can see some corruption in the institution.'\n\nSo far, tech-worker activism has been most visible at Google. Might workers elsewhere adopt similar tactics?\n\nTake Amazon, a company known for its aggressive anti-union tactics. This spring, white-collar employees told WIRED that their colleagues are too pragmatic and fearful of retaliation to go the way of Google activists. In December, however, employees said workers have been more vocal and restless over issues like the facial-recognition service Amazon sells to police departments and Amazon’s fierce opposition to a proposed Seattle tax on the company that would have funded homeless programs. We’re just beginning to challenge the fear that drives what looks from the outside to be apathy, says one Amazon employee.\n\nSocial movements are funny creatures. They sometimes pop up in unexpected places with unexpected rapidity, says Joshua Freeman, a professor at CUNY’s School of Labor and Urban Studies. He sees in the recent protests some echoes of the 1930s, when workers who had seen themselves as individualists—most notably news reporters—realized they needed union support as much as blue-collar workers. Then, too, society was in tumult. \"There was a general radicalization of American society in response to the Great Depression, in the sense that the corporate economy had failed most Americans, he says. Reporters were also unhappy with their employers using their pages to promote conservative political positions, Freeman says.\n\nRachel Gumpert, Unite Here’s head of communications, was not surprised to see both sets of workers organize around an issue like sexual harassment. Sometimes your base salary doesn’t protect you, says Gumpert. Everybody needs to have voice in their job and dignity at work.\n\nMore Great WIRED Stories"
    # language = "English"
    # topics = [{"title": "Technology"}]
    # original_id = 500120
    # get_more_like_this_results(content, language, topics, original_id, count=50)


if __name__ == '__main__':
    main()