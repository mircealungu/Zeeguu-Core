import json
from datetime import datetime
from urllib.parse import urlparse

import zeeguu
from zeeguu.model import Article

from zeeguu.model.user import User
from zeeguu.constants import JSON_TIME_FORMAT, UMR_LIKE_ARTICLE_ACTION, UMR_USER_FEEDBACK_ACTION
from zeeguu.model.user_reading_session import UserReadingSession

db = zeeguu.db


def _is_valid_url(a: str):
    return urlparse(a).netloc is not ''


class UserActivityData(db.Model):
    __table_args__ = dict(mysql_collate="utf8_bin")
    __tablename__ = 'user_activity_data'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User)

    time = db.Column(db.DateTime)

    event = db.Column(db.String(255))
    value = db.Column(db.String(255))
    extra_data = db.Column(db.String(4096))

    # question... should article_id be a FK? or just a number?
    # if it's a FK what do we do about those types of events
    # that are not associated with a given ID?
    # let's say that we'll leave the thing NULL / None for those
    article_id = db.Column(db.Integer, db.ForeignKey(Article.id))
    article = db.relationship(Article)

    def __init__(self, user, time, event, value, extra_data, article_id: int = None):
        self.user = user
        self.time = time
        self.event = event
        self.value = value
        self.extra_data = extra_data
        self.article_id = article_id

    def data_as_dictionary(self):
        data = dict(
            user_id=self.user_id,
            time=self.time.strftime("%Y-%m-%dT%H:%M:%S"),
            event=self.event,
            value=self.value,
            extra_data=self.extra_data
        )
        if self.article_id:
            data['article_id'] = self.article_id
        return data

    def is_like(self):
        return self.event == UMR_LIKE_ARTICLE_ACTION

    def is_feedback(self):
        return self.event == UMR_USER_FEEDBACK_ACTION

    def _extra_data_filter(self, attribute_name: str):
        """
            required by .find()
            used to parse extra_data to find a specific attribute

            example of extra_data:

                 {"80":[{"title":"Tour de France - Pourquoi n'ont-ils pas attaqué Froome après son tout-droit","url":"https://www.lequipe.fr/Cyclisme-sur-route/Actualites/Pourquoi-n-ont-ils-pas-attaque-froome-apres-son-tout-droit/818035#xtor=RSS-1","content":"","summary"…

        :param attribute_name -- e.g. "title" in the above exaxmple
        :return: value of attribute
        """
        start = str(self.extra_data).find("\"" + attribute_name + "\":") + len(attribute_name) + 4
        end = str(self.extra_data)[start:].find("\"")
        return str(self.extra_data)[start:end + start]

    @classmethod
    def _filter_by_extra_value(cls, events, extra_filter, extra_value):
        """

            required by .find()

        :param events:
        :param extra_filter:
        :param extra_value:
        :return:
        """
        filtered_results = []

        for event in events:
            extradata_value = event._extra_data_filter(extra_filter)
            if extradata_value == extra_value:
                filtered_results.append(event)
        return filtered_results

    @classmethod
    def find(cls,
             user: User = None,
             extra_filter: str = None,
             extra_value: str = None,
             event_filter: str = None,
             only_latest=False):
        """

            Find one or more user_activity_data by any of the above filters

        :return: object or None if not found
        """
        query = cls.query
        if event_filter is not None:
            query = query.filter(cls.event == event_filter)
        if user is not None:
            query = query.filter(cls.user == user)
        query = query.order_by('time')

        try:
            events = query.all()
            if extra_filter is None or extra_value is None:
                if only_latest:
                    return events[0]
                else:
                    return events

            filtered = cls._filter_by_extra_value(events, extra_filter, extra_value)
            if only_latest:
                return filtered[0]
            else:
                return filtered
        except:
            return None

    def find_url_in_extra_data(self):

        """
            DB structure is a mess!
            There is no convention where the url associated with an event is.
            Thu we need to look for it in different places

            NOTE: This can be solved by creating a new column called url and write the url only there

            returns: url if found or None otherwise
        """

        if _is_valid_url(self.value):
            return self.value.split('articleURL=')[-1]

        if self.extra_data and self.extra_data != '{}' and self.extra_data != 'null':
            try:
                extra_event_data = json.loads(self.extra_data)

                if 'articleURL' in extra_event_data:
                    url = extra_event_data['articleURL']
                elif 'url' in extra_event_data:
                    url = extra_event_data['url']
                else:  # There is no url
                    return None
                return url.split('articleURL=')[-1]

            except:  # Some json strings are truncated and some other times extra_event_data is an int
                # therefore cannot be parsed correctly and throw an exception
                return None
        else:  # The extra_data field is empty
            return None

    def find_or_create_article_id(self, db_session):
        """
            Finds or creates an article_id

            return: article ID or NONE

            NOTE: When the article cannot be downloaded anymore, 
            either because the article is no longer available or the newspaper.parser() fails

        """
        try:
            url = self.find_url_in_extra_data()

            if url:  # If url exists
                return Article.find_or_create(db_session, url).id
            else:  # If url is empty
                return None
        except Exception as e:  # When the article cannot be downloaded anymore, either because the article is no longer available or the newspaper.parser() fails
            import traceback
            traceback.print_exc()

            return None

    @classmethod
    def create_from_post_data(cls, session, data, user):
        _time = data['time']
        time = datetime.strptime(_time, JSON_TIME_FORMAT)

        event = data['event']
        value = data['value']

        article_id = None
        if data['article_id'] != '':
            article_id = int(data['article_id'])

        extra_data = data['extra_data']

        zeeguu.log(f'{event} value[:42]: {value[:42]} extra_data[:42]: {extra_data[:42]} art_id: {article_id}')

        new_entry = UserActivityData(user,
                                     time,
                                     event,
                                     value,
                                     extra_data,
                                     article_id)

        session.add(new_entry)
        session.commit()

        if not article_id:
            article_id = new_entry.find_or_create_article_id(session)

        UserReadingSession.update_reading_session(session,
                                                  event,
                                                  user.id,
                                                  article_id,
                                                  current_time=time
                                                  )
