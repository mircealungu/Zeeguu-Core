from datetime import datetime

from zeeguu_core.model import User

from zeeguu_core.content_recommender.mixed_recommender import _find_articles_for_user


def test_performance():
    me = User.find('i@mir.lu')

    a = datetime.now()

    res = _find_articles_for_user(me)
    print(len(res))

    for each in res[0:20]:
        print(f"{each.topics} {each.published_time} {each.title}")


    b = datetime.now()

    print(b - a)


test_performance()
