import zeeguu

from zeeguu.model.user import User
from sqlalchemy import func
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
    
    def extradata_filter(self, attribute: str):
        """

            used to parse extra_data to find a specific attribute

        :return: value of attribute
        """
        start = str(self.extra_data).find("\""+attribute+"\":") + len(attribute) + 4
        end = str(self.extra_data)[start:].find("\"")
        return str(self.extra_data)[start:end+start]

    @classmethod
    def find(cls, user: User=None, extra_filter=None, extra_value=None, event_filter: str=None):
        """

            Find by userid

        :return: object or None if not found
        """
        qry = cls.query
        if event_filter is not None:
            qry = qry.filter(cls.event == event_filter)
        if user is not None:
            qry = qry.filter(cls.user == user)
        qry = qry.order_by('time')

        try:

            events = qry.all()
            if extra_filter is None or extra_value is None:
                return events
            else:
                events_exf = []
                #filter by extra_value

                for event in events:
                    extradata_value = event.extradata_filter(extra_filter)
                    if extradata_value == extra_value:
                        events_exf.append(event)

                return events_exf
        except:
            return None

    @classmethod
    def find_latest(cls, user: User=None, extra_filter=None, extra_value=None, event_filter: str=None):
        """

            Find by userid

        :return: object or None if not found
        """
        qry = cls.query
        if event_filter is not None:
            qry = qry.filter(cls.event == event_filter)
        if user is not None:
            qry = qry.filter(cls.user == user)
        qry = qry.order_by('time')

        try:

            events = qry.all()
            if extra_filter is None or extra_value is None:
                return events[0]
            else:
                events_exf = None
                #filter by extra_value
                for event in events:
                    extradata_value = event.extradata_filter(extra_filter)
                    if extradata_value == extra_value:
                        events_exf =  event
                        break
                return events_exf
        except:
            return None





