import os

# Before we load the zeeguu module
# If the configuration file path is not set, try to load it from the default location

if "ZEEGUU_CORE_CONFIG" not in os.environ:
    os.environ["ZEEGUU_CORE_CONFIG"] = os.path.expanduser('~/.config/zeeguu/core_test.cfg')

if "WORD_SCHEDULING_ALGORITHM_CONFIG" not in os.environ:
    os.environ["WORD_SCHEDULING_ALGORITHM_CONFIG"] = os.path.expanduser('~/.config/zeeguu/word_scheduling_algorithms.ini')

import zeeguu.model

from faker import Faker

from unittest import TestCase


class ModelTestMixIn(TestCase):
    db = zeeguu.db

    def setUp(self):
        self.faker = Faker()
        self.db.create_all()

    def tearDown(self):
        super(ModelTestMixIn, self).tearDown()
        self.faker = None

        # sometimes the tearDown freezes on drop_all
        # and it seems that it's because there's still
        # a session open somewhere. Better call first:
        self.db.session.close()

        self.db.drop_all()
