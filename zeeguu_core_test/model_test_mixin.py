import requests_mock
import zeeguu_core.model

from faker import Faker

from unittest import TestCase

from .urls_for_test import mock_requests_get


class ModelTestMixIn(TestCase):
    db = zeeguu_core.db

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

    def run(self, result=None):

        # For the unit tests we use several pages
        # that are stored locally, so we mock requests.get
        # to return the content of the
        with requests_mock.Mocker() as m:
            mock_requests_get(m)
            super(ModelTestMixIn, self).run(result)
