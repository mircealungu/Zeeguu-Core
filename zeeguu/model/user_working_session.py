import sqlalchemy
import zeeguu

from datetime import datetime, timedelta
from zeeguu.model.user import User
from zeeguu.model.article import Article

db = zeeguu.db

# Parameter that controls after how much time (in minutes) the session is expired
working_session_timeout = 5

opening_actions = [
    "UMR - OPEN ARTICLE",
    "UMR - OPEN STARRED ARTICLE",
    "UMR - ARTICLE FOCUSED"
]
interaction_actions = ["UMR - TRANSLATE TEXT",
                       "UMR - SPEAK TEXT",
                       "UMR - OPEN ALTERMENU",
                       "UMR - CLOSE ALTERMENU", "UMR - UNDO TEXT TRANSLATION",
                       "UMR - SEND SUGGESTION", "UMR - CHANGE ORIENTATION"
                       ]
closing_actions = ["UMR - LIKE ARTICLE",
                   "UMR - ARTICLE CLOSED",
                   "UMR - ARTICLE LOST FOCUS"
                   ]


class UserWorkingSession(db.Model):
    """
    This class keeps track of the user's reading sessions.

    So we can study how much time, when and which articles the user has read.
    """

    __table_args__ = dict(mysql_collate="utf8_bin")
    __tablename__ = 'user_working_session'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User)

    article_id = db.Column(db.Integer, db.ForeignKey(Article.id))
    article = db.relationship(Article)

    start_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # Duration time in miliseconds
    last_action_time = db.Column(db.DateTime)

    is_active = db.Column(db.Boolean)

    session_type = db.Column(db.Integer)  # 1=reading / 2=exercise

    def __init__(self, user_id, article_id, start_time, duration, last_action_time, is_active, sys_time=None):
        self.user_id = user_id
        self.article_id = article_id
        self.start_time = start_time
        self.duration = duration
        self.last_action_time = last_action_time
        self.is_active = is_active
        if sys_time is None:
            self.sys_time = datetime.now()

    @classmethod
    def get_working_session_timeout(cls):
        return working_session_timeout

    def _get_active_working_session(self, db_session, user_id, article_id):
        """
            parameters: user_id and article_id

            returns: the active working_session record for the specific user and article or None if none is found
        """
        query = db_session.query(UserWorkingSession)
        query = query.filter(UserWorkingSession.user_id == user_id)
        query = query.filter(UserWorkingSession.article_id == article_id)
        query = query.filter(UserWorkingSession.is_active == True)
        query.order_by(UserWorkingSession.last_action_time)
        try:
            return query.one()

        except sqlalchemy.orm.exc.MultipleResultsFound:
            # Close all open sessions except last one
            open_sessions = query.all()
            for working_session in open_sessions[:-1]:
                self._close_working_session(db_session, working_session)
            return working_session

        except sqlalchemy.orm.exc.NoResultFound:
            return None

    def _is_active_session(self, working_session):
        """
            Validates if the working session is still valid (according to the working_session_timeout control variable)

            returns: True if the time between the working session's last action and the current time
                    is less or equal than the working_session_timeout
        """
        time_difference = working_session.sys_time - working_session.last_action_time
        w_working_session_timeout = timedelta(minutes=working_session_timeout)

        return time_difference <= w_working_session_timeout

    @classmethod
    def _create_new_session(cls, db_session, user_id, article_id):
        new_entry = UserWorkingSession(user_id,
                                       article_id,
                                       cls.sys_time,
                                       0,
                                       cls.sys_time,
                                       True)
        db_session.add(new_entry)
        db_session.commit()
        return new_entry

    def _update_last_use(cls, db_session, user_id, article_id, add_grace_time=False):
        """
            Updates the last_action_time field. For sessions that were left open, since we cannot know exactly
            when the user stopped using it, we give an additional (working_session_timeout) time benefit

            Parameters:
            db_session = database session
            user_id = user identifier
            article_id = article identifier
            add_grace_time = True/False boolean value to add an extra working_session_timeout minutes after the last_action_datetime

            returns: The working session or None if none is found
        """
        query = cls.query
        query = query.filter(cls.user_id == user_id)
        query = query.filter(cls.article_id == article_id)
        query = query.filter(cls.is_active == True)
        try:
            working_session = query.one()
            if add_grace_time:
                working_session.last_action_time += timedelta(minutes=working_session_timeout)
            else:
                working_session.last_action_time = working_session.sys_time
            db_session.commit()
            return working_session

        except sqlalchemy.orm.exc.MultipleResultsFound:
            # If for some reason we get here, it means we have many open sessions for the same
            # user and article, in this case we leave the last_action_time unchanged
            import traceback
            traceback.print_exc()
            return None

        except sqlalchemy.orm.exc.NoResultFound:
            return None

    def _close_working_session(cls, db_session, working_session):
        """
            Computes the duration of the working session and sets the is_active field to False

            returns: The working session or None if none is found
        """
        query = cls.query
        query = query.filter(UserWorkingSession.id == working_session.id)
        try:
            working_session = query.one()
            working_session.is_active = False
            time_diff = working_session.last_action_time - working_session.start_time
            working_session.duration = time_diff.total_seconds() * 1000  # Convert to miliseconds
            db_session.commit()
            return working_session

        except sqlalchemy.orm.exc.MultipleResultsFound:
            # This scenario should never happen, it means the working_session.id is duplicated
            return None

        except sqlalchemy.orm.exc.NoResultFound:
            return None

    # NOTE:  Because not all opening session actions end with a closing action,
    # whenever we open a new session, we call this method to close all other active sessions,
    # and to avoid having active sessions forever (or until the user re-opens the same article)
    def _close_user_working_sessions(cls, db_session, user_id):
        query = cls.query
        query = query.filter(cls.user_id == user_id)
        query = query.filter(cls.is_active == True)
        try:
            working_sessions = query.all()
            for working_session in working_sessions:
                working_session.is_active = False
                time_diff = working_session.last_action_time - working_session.start_time
                working_session.duration = time_diff.total_seconds() * 1000  # Convert to miliseconds
                db_session.add(working_session)
            db_session.commit()
            return working_sessions

        except sqlalchemy.orm.exc.NoResultFound:
            return None

    @classmethod
    def update_working_session(cls, db_session, user_id, article_id, event, event_time):
        """
            Main callable method that keeps track of the working sessions.
            Depending if the event belongs to the opening, interaction or closing list of events
            the method creates, updates or closes a working session

            Parameters:
            db_session = database session
            user = user id
            article = article id
            event = event string (based on the user_activity_data events,
                                    check list at the beginning of this python file)
            event_time = system overwriting datetime value

            returns: The working session  or None if none is found
        """
        cls.sys_time = event_time  # Global variable to emulate the system datetime, instead of the current server datetime

        current_working_session = cls._get_active_working_session(cls, db_session, user_id, article_id)

        # If the event is an opening or interaction type
        if event in opening_actions or event in interaction_actions:
            if not current_working_session:  # If there is no active working session
                cls._close_user_working_sessions(cls, db_session, user_id)
                new_session = cls._create_new_session(cls, db_session, user_id, article_id)
                return new_session
            else:  # Is there an open working session
                if cls._is_active_session(db_session,
                                          current_working_session):  # If the open working session is still valid (within the working_session_timeout window)
                    active_session = cls._update_last_use(cls, db_session, user_id, article_id, add_grace_time=False)
                else:  # There is an open working session but the elapsed time is larger than the working_session_timeout
                    cls._update_last_use(cls, db_session, user_id, article_id, add_grace_time=True)
                    cls._close_working_session(cls, db_session, current_working_session)
                    cls._close_user_working_sessions(cls, db_session, user_id)
                    active_session = cls._create_new_session(cls, db_session, user_id, article_id)
                return active_session

        elif event in closing_actions:  # If the event is of a closing type
            if current_working_session:  # If there is an open working session
                if cls._is_active_session(db_session,
                                          current_working_session):  # If the elapsed time is shorter than the timeout parameter
                    active_session = cls._update_last_use(cls, db_session, user_id, article_id, add_grace_time=False)
                else:  # When the elapsed time is larger than the working_session_timeout, we add the grace time (which is n extra minutes where n=working_session_timeout)
                    active_session = cls._update_last_use(cls, db_session, user_id, article_id, add_grace_time=True)
                cls._close_working_session(cls, db_session, current_working_session)
                return active_session

    @classmethod
    def find_by_user(cls,
                     user,
                     from_date: str = '2000-01-01T00:00:00',
                     to_date: str = '9999-12-31T23:59:59',
                     is_active: bool = None):
        """

            Get working sessions by user

        :return: object or None if not found
        """
        query = cls.query
        query = query.filter(cls.user_id == user)
        query = query.filter(cls.start_time >= from_date)
        query = query.filter(cls.start_time <= to_date)

        if is_active is not None:
            query = query.filter(cls.is_active == is_active)
        query = query.order_by('start_time')

        try:
            sessions = query.all()
            return sessions
        except sqlalchemy.orm.exc.NoResultFound:
            return None

    @classmethod
    def find_by_cohort(cls,
                       cohort,
                       from_date: str = '2000-01-01T00:00:00',
                       to_date: str = '9999-12-31T23:59:59',
                       is_active: bool = None):
        """

            Get working sessions by cohort

        :return: object or None if not found
        """
        query = cls.query.join(User).filter(User.cohort_id == cohort)
        query = query.filter(UserWorkingSession.start_time >= from_date)
        query = query.filter(UserWorkingSession.start_time <= to_date)

        if is_active is not None:
            query = query.filter(cls.is_active == is_active)
        query = query.order_by('start_time')

        try:
            sessions = query.all()
            return sessions
        except sqlalchemy.orm.exc.NoResultFound:
            return None

    @classmethod
    def find_by_article(cls,
                        article,
                        from_date: str = '2000-01-01T00:00:00',
                        to_date: str = '9999-12-31T23:59:59',
                        is_active: bool = None,
                        cohort: bool = None):
        """

        Get working sessions by article

        :return: object or None if not found
        """
        if cohort is not None:
            query = cls.query.join(User).filter(User.cohort_id == cohort)
        else:
            query = cls.query
        query = query.filter(cls.article_id == article)
        query = query.filter(cls.start_time >= from_date)
        query = query.filter(cls.start_time <= to_date)

        if is_active is not None:
            query = query.filter(cls.is_active == is_active)

        query = query.order_by('start_time')

        try:
            sessions = query.all()
            return sessions
        except sqlalchemy.orm.exc.NoResultFound:
            return None

    @classmethod
    def find_by_user_and_article(cls,
                                 user,
                                 article):
        """

        Get working sessions by user and article

        :return: object or None if not found
        """
        query = cls.query
        query = query.filter(cls.user_id == user)
        query = query.filter(cls.article_id == article)

        query = query.order_by('start_time')

        try:
            sessions = query.all()
            return sessions
        except sqlalchemy.orm.exc.NoResultFound:
            return None
