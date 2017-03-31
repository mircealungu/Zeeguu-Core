import zeeguu
print ('Importing the zeeguu model linked with DB : ' + zeeguu.app.config["SQLALCHEMY_DATABASE_URI"])

from .bookmark import Bookmark
from .domain_name import DomainName
from .user import User
from .exercise import Exercise
from .exercise_outcome import ExerciseOutcome
from .exercise_source import ExerciseSource
from .feeds import RSSFeed, RSSFeedRegistration
from .knowledge_estimator import SimpleKnowledgeEstimator
from .language import Language
from .session import Session
from .text import Text
from .url import Url
from .user import User
from .user_activitiy_data import UserActivityData
from .user_word import UserWord
from .smartwatch.watch_event_type import WatchEventType
from .smartwatch.watch_interaction_event import WatchInteractionEvent