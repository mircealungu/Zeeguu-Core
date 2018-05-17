import json

from sqlalchemy.orm.exc import NoResultFound

import zeeguu

from sqlalchemy import Column, Integer, UnicodeText

from zeeguu.model import User, UserWord

db = zeeguu.db

MAX_EVENT_HISTORY_LENGTH = 50


class WordInteractionEvent(object):
    CLICKED = 0
    NOT_CLICKED = 1
    CORRECT_IN_EXERCISE = 2
    WRONG_IN_EX_EASY = 3
    WRONG_IN_EX_DIFFICULT = 4

    def __init__(self, event_type: int, seconds_since_epoch):
        self.event_type = event_type
        self.seconds_since_epoch = seconds_since_epoch

    def to_json(self):
        return (self.event_type, self.seconds_since_epoch)

    def __repr__(self):
        return f"(WordInteractionEvent: {self.event_type} - {self.seconds_since_epoch}) "


class WordInteractionHistory(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = Column(Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User)

    word_id = db.Column(db.Integer, db.ForeignKey(UserWord.id), nullable=False)
    word = db.relationship(UserWord, primaryjoin=word_id == UserWord.id)

    # should be between 0 and 100
    known_probability = db.Column(db.Integer, db.ForeignKey(User.id))

    # the interaction history stored as string
    interaction_history_json = Column(UnicodeText())

    def __init__(self):
        # never work with the self._interaction_history itself
        # always, work with the method interaction_history()
        self.interaction_history = None

    def add_event(self, event_type, timestamp):
        """
            add a new event
        :param event_type:
        :param timestamp:
        :return:
        """

        # json can't serialize timestamps, so we simply
        seconds_since_epoch = int(timestamp.strftime("%s"))

        self.interaction_history.insert(0, WordInteractionEvent(event_type, seconds_since_epoch))
        self.interaction_history = self.interaction_history()[0:MAX_EVENT_HISTORY_LENGTH]

    def reify_interaction_history(self):
        """

            after this the interaction_history object is synced from the interaction_history_json

        :return:
        """
        list_of_tuples = json.loads(self.interaction_history_json)
        self.interaction_history = [WordInteractionEvent(pair[0], pair[1]) for pair in list_of_tuples]

    def save_to_db(self, db_session):
        """

            after this the interaction_history_json will be the result of converting  interaction_history to json
        :return:
        """
        self.interaction_history_json = json.dumps([e.to_json() for e in self.interaction_history])
        db_session.add(self)
        db_session.commit()

    @classmethod
    def find(cls, user: User, word: UserWord):
        """

            get the data from db & convert the string  rep of the history
            to the object

        :param user:
        :param word:
        :return:
        """

        try:
            history = cls.query.filter_by(user=user, word=word).one()
            history.reify_interaction_history()
            return history

        except NoResultFound:
            return None

    @classmethod
    def find_all_word_histories_for_user(cls, user: User):
        """

            get the data from db & convert the string  rep of the history
            to the object

        :param user:
        :return:
        """

        histories = cls.query.filter_by(user=user).all()
        for history in histories:
            history.reify_interaction_history()
        return histories
