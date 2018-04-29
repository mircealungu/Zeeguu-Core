import sqlalchemy
import zeeguu

from datetime import datetime, timedelta
from zeeguu.model.user import User
from zeeguu.model.article import Article

db = zeeguu.db

# Parameter that controls after how much time (in minutes) the session is expired
WORKING_SESSION_TIMEOUT = 5

OPENING_ACTIONS = [
    "UMR - OPEN ARTICLE",
    "UMR - OPEN STARRED ARTICLE",
    "UMR - ARTICLE FOCUSED"
]
INTERACTION_ACTIONS = ["UMR - TRANSLATE TEXT",
                       "UMR - SPEAK TEXT",
                       "UMR - OPEN ALTERMENU",
                       "UMR - CLOSE ALTERMENU", "UMR - UNDO TEXT TRANSLATION",
                       "UMR - SEND SUGGESTION", "UMR - CHANGE ORIENTATION"
                       ]
CLOSING_ACTIONS = ["UMR - LIKE ARTICLE",
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

    def __init__(self, user_id, article_id, sys_time=None):
        self.user_id = user_id
        self.article_id = article_id
        self.is_active = True
        if sys_time is None:# Instance variable to override the system datetime, instead of the current server datetime
            sys_time = datetime.now()
        self.start_time = sys_time
        self.last_action_time = sys_time
        self.duration = 0

    @staticmethod
    def get_working_session_timeout():
        return WORKING_SESSION_TIMEOUT

    @classmethod
    def _find(cls, user_id, article_id, db_session):
        """
            Queries and returns if there is an open working session for that user and article

            parameters: 
            user_id = user identifier
            article_id = article identifier
            db_session = database session

            returns: the active working_session record for the specific user and article or None if none is found
        """
        query = cls.query
        query = query.filter(cls.user_id == user_id)
        query = query.filter(cls.article_id == article_id)
        query = query.filter(cls.is_active == True)
        
        try:
            return query.one()

        except sqlalchemy.orm.exc.MultipleResultsFound:
            query.order_by(UserWorkingSession.last_action_time)
            # Close all open sessions except last one
            open_sessions = query.all()
            for working_session in open_sessions[:-1]:
                working_session._close_working_session(db_session)
            return open_sessions[-1]

        except sqlalchemy.orm.exc.NoResultFound:
            return None

    def _is_same_working_session(self, sys_time=datetime.now()):
        """
            Validates if the working session is still valid (according to the working_session_timeout control variable)

            Parameters:
            sys_time = when this parameter is sent, instead of using the datetime.now() value for the current time
                        we use the provided value as the system time (only used for filling in historical data)

            returns: True if the time between the working session's last action and the current time
                    is less or equal than the working_session_timeout
        """
        time_difference = sys_time - self.last_action_time
        w_working_session_timeout = timedelta(minutes=WORKING_SESSION_TIMEOUT)

        return time_difference <= w_working_session_timeout

    @staticmethod
    def _create_new_session(db_session, user_id, article_id, sys_time=None):
        """
            Creates a new working session

            Parameters:
            user_id = user identifier
            article_id = article identifier
            sys_time = when this parameter is sent, instead of using the datetime.now() value for the current time
                        we use the provided value as the system time (only used for filling in historical data)
        """
        working_session = UserWorkingSession(user_id, article_id, sys_time)
        db_session.add(working_session)
        db_session.commit()
        return working_session

    def _update_last_use(self, db_session, add_grace_time=False, sys_time=datetime.now()):
        """
            Updates the last_action_time field. For sessions that were left open, since we cannot know exactly
            when the user stopped using it, we give an additional (working_session_timeout) time benefit

            Parameters:
            db_session = database session
            add_grace_time = True/False boolean value to add an extra working_session_timeout minutes after the last_action_datetime
            sys_time = when this parameter is sent, instead of using the datetime.now() value for the current time
                        we use the provided value as the system time (only used for filling in historical data)

            returns: The working session or None if none or multiple results are found
        """

        if add_grace_time:
            self.last_action_time += timedelta(minutes=WORKING_SESSION_TIMEOUT)
        else:
            self.last_action_time = sys_time
        db_session.add(self)
        db_session.commit()
        return self


    def _close_working_session(self, db_session):
        """
            Computes the duration of the working session and sets the is_active field to False

            Parameters:
            db_session = database session

            returns: The working session or None if none is found
        """
        self.is_active = False
        time_diff = self.last_action_time - self.start_time
        self.duration = time_diff.total_seconds() * 1000  # Convert to miliseconds
        db_session.add(self)
        db_session.commit()
        return self

    # NOTE:  Because not all opening session actions end with a closing action,
    # whenever we open a new session, we call this method to close all other active sessions,
    # and to avoid having active sessions forever (or until the user re-opens the same article)
    @classmethod
    def _close_user_working_sessions(cls, db_session, user_id):
        """
            Finds and closes all open sessions from a specific user

            Parameters:
            db_session = database session
            user_id = user identifier to close his sessions

            returns: None

        """
        query = cls.query
        query = query.filter(cls.user_id == user_id)
        query = query.filter(cls.is_active == True)
        working_sessions = query.all()
        for working_session in working_sessions:
            working_session.is_active = False
            time_diff = working_session.last_action_time - working_session.start_time
            working_session.duration = time_diff.total_seconds() * 1000  # Convert to miliseconds
            db_session.add(working_session)
        db_session.commit()
        return None

    @classmethod
    def update_working_session(cls, db_session, event, user_id, article_id, sys_time=None):
        """
            Main callable method that keeps track of the working sessions.
            Depending if the event belongs to the opening, interaction or closing list of events
            the method creates, updates or closes a working session

            Parameters:
            db_session = database session
            event = event string (based on the user_activity_data events,
                                    check list at the beginning of this python file)
            user_id = user identifier
            article_id = article identifier
            sys_time = when this parameter is sent, instead of using the datetime.now() value for the current time
                        we use the provided value as the system time (only used for filling in historical data)

            returns: The working session  or None if none is found
        """
        active_working_session = cls._find(user_id, article_id,db_session)

        # If the event is an opening or interaction type
        if event in OPENING_ACTIONS or event in INTERACTION_ACTIONS:
            if not active_working_session:  # If there is no active working session
                UserWorkingSession._close_user_working_sessions(db_session, user_id)
                return cls._create_new_session(db_session, user_id, article_id, sys_time)
                
            else:  # Is there an active working session
                # If the open working session is still valid (within the working_session_timeout window)
                if active_working_session._is_same_working_session(sys_time):  
                    return active_working_session._update_last_use(db_session, add_grace_time=False, sys_time=sys_time)
                # There is an open working session but the elapsed time is larger than the working_session_timeout
                else:  
                    active_working_session._update_last_use(db_session, add_grace_time=True, sys_time=sys_time)
                    active_working_session._close_working_session(db_session)
                    UserWorkingSession._close_user_working_sessions(db_session, user_id)
                    return cls._create_new_session(db_session, user_id, article_id, sys_time)

        elif event in CLOSING_ACTIONS:  # If the event is of a closing type
            if active_working_session:  # If there is an open working session
                # If the elapsed time is shorter than the timeout parameter
                if active_working_session._is_same_working_session(sys_time):  
                    return active_working_session._update_last_use(db_session, add_grace_time=False, sys_time=sys_time)
                # When the elapsed time is larger than the working_session_timeout, 
                # we add the grace time (which is n extra minutes where n=working_session_timeout)
                else: 
                    active_working_session._update_last_use(db_session, add_grace_time=True, sys_time=sys_time)
                    return active_working_session._close_working_session(db_session)
            else:
                return None
        else:
            return None

    @classmethod
    def find_by_user(cls,
                     user,
                     from_date: str = '2000-01-01T00:00:00',
                     to_date: str = '9999-12-31T23:59:59',
                     is_active: bool = None):
        """

            Get working sessions by user

            return: object or None if not found
        """
        query = cls.query
        query = query.filter(cls.user_id == user)
        query = query.filter(cls.start_time >= from_date)
        query = query.filter(cls.start_time <= to_date)

        if is_active is not None:
            query = query.filter(cls.is_active == is_active)
        query = query.order_by('start_time')

        sessions = query.all()
        return sessions

    @classmethod
    def find_by_cohort(cls,
                       cohort,
                       from_date: str = '2000-01-01T00:00:00',
                       to_date: str = '9999-12-31T23:59:59',
                       is_active: bool = None):
        """
            Get working sessions by cohort
            return: object or None if not found
        """
        query = cls.query.join(User).filter(User.cohort_id == cohort)
        query = query.filter(UserWorkingSession.start_time >= from_date)
        query = query.filter(UserWorkingSession.start_time <= to_date)

        if is_active is not None:
            query = query.filter(cls.is_active == is_active)
        query = query.order_by('start_time')

        sessions = query.all()
        return sessions

    @classmethod
    def find_by_article(cls,
                        article,
                        from_date: str = '2000-01-01T00:00:00',
                        to_date: str = '9999-12-31T23:59:59',
                        is_active: bool = None,
                        cohort: bool = None):
        """
            Get working sessions by article
            return: object or None if not found
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

        sessions = query.all()
        return sessions

    @classmethod
    def find_by_user_and_article(cls,
                                 user,
                                 article):
        """
            Get working sessions by user and article
            return: object or None if not found
        """
        query = cls.query
        query = query.filter(cls.user_id == user)
        query = query.filter(cls.article_id == article)

        query = query.order_by('start_time')

        sessions = query.all()
        return sessions
