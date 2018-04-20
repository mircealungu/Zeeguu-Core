from zeeguu.model.user_activitiy_data import UserActivityData
from zeeguu.model.article import Article
from zeeguu.model.user_working_session import UserWorkingSession

import zeeguu
import json
from urllib.parse import urlparse

db_session = zeeguu.db.session

data = UserActivityData.find()

for event in data:
    # NOTE: Not all scenarios include the url
    user = event.user_id
    time = event.time

    working_session = UserWorkingSession(user, event.find_article_id(db_session), sys_time = time)
    working_session.update_working_session(db_session, event.event)
    print(event.id)
