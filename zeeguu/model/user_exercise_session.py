import sqlalchemy
import zeeguu

from datetime import datetime, timedelta
from zeeguu.model.user import User

db = zeeguu.db

# Parameter that controls after how much time (in minutes) the session is expired
EXERCISE_SESSION_TIMEOUT = 5


class UserExerciseSession(db.Model):
    """
    This class keeps track of the user's exercise sessions.

    So we can study how much time and when the user has done exercises.
    """

    __table_args__ = dict(mysql_collate="utf8_bin")
    __tablename__ = 'user_exercise_session'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User)

    start_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # Duration time in miliseconds
    last_action_time = db.Column(db.DateTime)

    is_active = db.Column(db.Boolean)

    def __init__(self, user_id, current_time=None):
        self.user_id = user_id
        self.is_active = True
        # Instance variable to override the system datetime, instead of the current server datetime
        if current_time is None:
            current_time = datetime.now()
        self.start_time = current_time
        self.last_action_time = current_time
        self.duration = 0

    @classmethod
    def get_exercise_session_timeout(cls):
        return EXERCISE_SESSION_TIMEOUT

    @classmethod
    def _find(cls, user_id, db_session):
        """
            Queries and returns if there is an open exercise session for that user

            Parameters: 
            user_id = user identifier
            db_session = database session

            returns: the active exercise_session record for the specific user or None if none is found
        """
        query = cls.query
        query = query.filter(cls.user_id == user_id)
        query = query.filter(cls.is_active == True)
        try:
            return query.one()

        except sqlalchemy.orm.exc.MultipleResultsFound:
            # Close all open sessions except last one
            query.order_by(cls.last_action_time)
            open_sessions = query.all()
            for exercise_session in open_sessions[:-1]:
                exercise_session._close_exercise_session(db_session)
            return open_sessions[-1]

        except sqlalchemy.orm.exc.NoResultFound:
            return None

    def _is_still_active(self, current_time=datetime.now()):
        """
            Validates if the exercise session is still valid (according to the exercise_session_timeout control variable)

            Parameters:
            current_time = when this parameter is sent, instead of using the datetime.now() value for the current time
                        we use the provided value as the system time (only used for filling in historical data)

            returns: True if the time between the exercise session's last action and the current time
                    is less or equal than the exercise_session_timeout
        """
        time_difference = current_time - self.last_action_time
        w_exercise_session_timeout = timedelta(minutes=EXERCISE_SESSION_TIMEOUT)

        return time_difference <= w_exercise_session_timeout

    @staticmethod
    def _create_new_session(db_session, user_id, current_time=None):
        """
            Creates a new exercise session

            Parameters:
            db_session = database session
            user_id = user identifier
            current_time = when this parameter is sent, instead of using the datetime.now() value for the current time
                        we use the provided value as the system time (only used for filling in historical data)

            returns: The new exercise session
        """
        exercise_session = UserExerciseSession(user_id, current_time)
        db_session.add(exercise_session)
        db_session.commit()
        return exercise_session

    def _update_last_action_time(self, db_session, current_time=datetime.now()):
        """
            Updates the last_action_time field. 

            Parameters:
            db_session = database session
            current_time = when this parameter is sent, instead of using the datetime.now() value for the current time
                        we use the provided value as the system time (only used for filling in historical data)

            returns: The exercise session
        """
        self.last_action_time = current_time
        db_session.add(self)
        db_session.commit()
        return self

    def _close_exercise_session(self, db_session):
        """
            Computes the duration of the exercise session and sets the is_active field to False

            Parameters:
            db_session = database session

            returns: The exercise session if everything went well otherwise probably exceptions related to the DB
        """
        self.is_active = False
        time_diff = self.last_action_time - self.start_time
        self.duration = time_diff.total_seconds() * 1000  # Convert to miliseconds
        db_session.add(self)
        db_session.commit()
        return self

    @classmethod
    def update_exercise_session(cls, user_id, db_session, current_time=None):
        """

            Main callable method that keeps track of the exercise sessions.

            It does:

            Parameters:
            user_id = user identifier
            db_session = database session

            current_time = when this parameter is sent, instead of using the datetime.now() value for the current time
                        we use the provided value as the system time (only used for filling in historical data)

            returns: The exercise session or None
        """
        active_exercise_session = cls._find(user_id, db_session)

        if active_exercise_session:  # If there is an active exercise session for the user
            if active_exercise_session._is_still_active():  # Verify if the session is not expired (according to session timeout)
                return active_exercise_session._update_last_action_time(db_session)
            else:  # If the session is expired, close it and create a new one
                active_exercise_session._close_exercise_session(db_session)
                return cls._create_new_session(db_session, user_id, current_time=current_time)
        else:
            return cls._create_new_session(db_session, user_id, current_time=current_time)

    @classmethod
    def find_by_user(cls,
                     user_id,
                     from_date: str = '2000-01-01T00:00:00',
                     to_date: str = '9999-12-31T23:59:59',
                     is_active: bool = None):
        """

            Get exercise sessions by user

            return: object or None if not found
        """
        query = cls.query
        query = query.filter(cls.user_id == user_id)
        query = query.filter(cls.start_time >= from_date)
        query = query.filter(cls.start_time <= to_date)

        if is_active is not None:
            query = query.filter(cls.is_active == is_active)
        query = query.order_by('start_time')

        sessions = query.all()
        return sessions

    @classmethod
    def find_by_cohort(cls,
                       cohort_id,
                       from_date: str = '2000-01-01T00:00:00',
                       to_date: str = '9999-12-31T23:59:59',
                       is_active: bool = None):
        """
            Get exercise sessions by cohort
            return: object or None if not found
        """
        query = cls.query.join(User).filter(User.cohort_id == cohort_id)
        query = query.filter(cls.start_time >= from_date)
        query = query.filter(cls.start_time <= to_date)

        if is_active is not None:
            query = query.filter(cls.is_active == is_active)
        query = query.order_by('start_time')

        sessions = query.all()
        return sessions
