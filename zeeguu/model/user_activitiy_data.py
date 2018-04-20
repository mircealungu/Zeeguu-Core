import json
from datetime import datetime
from urllib.parse import urlparse

import zeeguu
from zeeguu.model import Article

from zeeguu.model.user import User
from zeeguu.constants import JSON_TIME_FORMAT
from zeeguu.model.user_working_session import UserWorkingSession

db = zeeguu.db


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

    def __init__(self, user, time, event, value, extra_data):
        self.user = user
        self.time = time
        self.event = event
        self.value = value
        self.extra_data = extra_data

    def data_as_dictionary(self):
        return dict(
            user_id=self.user_id,
            time=self.time.strftime("%Y-%m-%dT%H:%M:%S"),
            event=self.event,
            value=self.value,
            extra_data=self.extra_data
        )

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

    def _find_url_in_extra_data(self):

        """
            DB structure is a mess!
            There is no convention where the url associated with an event is.
            Thus...

        """

        def _is_valid_url(a: str):
            return urlparse(a).netloc is not ''

        if self.extra_data and self.extra_data != '{}' and self.extra_data != 'null':
            try:
                extra_event_data = json.loads(self.extra_data)

                if 'articleURL' in extra_event_data:
                    url = extra_event_data['articleURL']
                elif 'url' in extra_event_data:
                    url = extra_event_data['url']
                elif _is_valid_url(self.value):
                    url = self.value
                else:  # There is no url
                    return None
                return url

            except ValueError:  # Some json strings are truncated, therefore cannot be parsed correctly and throw an exception
                return None
        else:  # The extra_data field is empty
            return None

    def find_article_id(self, db_session):
        """
            Finds or creates an article_id

            return: article ID or NONE
        """
        try:
            url = self._find_url_in_extra_data()
            if url: #If url exists
                return Article.find_or_create(db_session, url).id
            else:
                return None
        except:  # When the article cannot be downloaded anymore, either because the article is no longer available or the newspaper.parser() fails
            return None

    @classmethod
    def create_from_post_data(cls, session, data, user):
        time = data['time']
        event = data['event']
        value = data['value']
        extra_data = data['extra_data']

        zeeguu.log(f'{event} value[:42]: {value[:42]} extra_data[:42]: {extra_data[:42]}')

        new_entry = UserActivityData(user,
                                     datetime.strptime(time, JSON_TIME_FORMAT),
                                     event,
                                     value,
                                     extra_data)
        session.add(new_entry)
        session.commit()

        working_session = UserWorkingSession(user, new_entry.find_article_id(session))
        working_session.update_working_session(session, event)
