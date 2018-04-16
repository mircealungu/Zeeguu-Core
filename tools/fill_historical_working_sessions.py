from zeeguu.model.user_activitiy_data import UserActivityData
from zeeguu.model.article import Article
from zeeguu.model.user_working_session import UserWorkingSession

import zeeguu
import json
from urllib.parse import urlparse

db_session = zeeguu.db.session


def _is_valid_url(a: str):
    return urlparse(a).netloc is not ''


def _get_article_id(event):
    if event.extra_data and event.extra_data != '{}' and event.extra_data != 'null':
        try:
            extra_event_data = json.loads(event.extra_data)

            if 'articleURL' in extra_event_data:
                url = extra_event_data['articleURL']
            elif 'url' in extra_event_data:
                url = extra_event_data['url']
            elif _is_valid_url(event.value):
                url = event.value
            else:  # There is no url
                return None

            try:
                return Article.find_or_create(db_session, url).id
            except:  # When the article cannot be downloaded anymore, either because the article is no longer available or the newspaper.parser() fails
                # When the langdetect is not able to detect a language, we get that exception here
                return None

        except ValueError:  # Some json strings are truncated, therefore cannot be parsed correctly and throw an exception
            return None
    else:  # The extra_data field is empty
        return None


data = UserActivityData.find()

for event in data:
    # NOTE: Not all scenarios include the url
    user = event.user_id
    time = event.time

    UserWorkingSession.update_working_session(db_session, user, _get_article_id(event), event.event, time)
    print(event.id)
