import flask_sqlalchemy

import zeeguu
from flask import Flask

from zeeguu.configuration.configuration import load_configuration_or_abort

# If zeeguu.app is already defined we use that object
# as the app for the db_init that we do later. If not,
# we create the app and load the corresponding configuration
if not hasattr(zeeguu, "app"):
    zeeguu.app = Flask("Zeeguu-Core")
    load_configuration_or_abort(zeeguu.app, 'ZEEGUU_CORE_CONFIG',
                                ['SQLALCHEMY_DATABASE_URI', 'MAX_SESSION', 'SQLALCHEMY_TRACK_MODIFICATIONS'])

# Create the zeeguu.db object, which will be the superclass
# of all the model classes
zeeguu.db = flask_sqlalchemy.SQLAlchemy(zeeguu.app)
# Note, that if we pass the app here, then we don't need later
# to push the app context

from .article import Article
from .bookmark import Bookmark
from .cohort import Cohort
from .domain_name import DomainName
from .exercise import Exercise
from .exercise_outcome import ExerciseOutcome
from .exercise_source import ExerciseSource
from .feed import RSSFeed
from .feed_registrations import RSSFeedRegistration
from .knowledge_estimator import SimpleKnowledgeEstimator
from .language import Language
from .session import Session
from .smartwatch.watch_event_type import WatchEventType
from .smartwatch.watch_interaction_event import WatchInteractionEvent
from .teacher import Teacher
from .teacher_cohort_map import TeacherCohortMap
from .text import Text
from .topic import Topic
from .url import Url
from .user import User
from .user import User
from .user_activitiy_data import UserActivityData
from .user_article import UserArticle
from .user_preference import UserPreference
from .user_preference import UserPreference
from .user_word import UserWord

# Creating the DB tables if needed
# Note that this must be called after all the model classes are loaded
zeeguu.db.init_app(zeeguu.app)
zeeguu.db.create_all(app=zeeguu.app)

print(('ZEEGUU: Linked model with: ' + zeeguu.app.config["SQLALCHEMY_DATABASE_URI"]))
