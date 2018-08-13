import json

from zeeguu.model.user_activitiy_data import UserActivityData

import zeeguu

'''
    Script that loops through all the exeuser_activity_data actions in the database
    and computes the article_id for each entry.

    NOTE: It deletes and recreates the table
'''
# List of excluded ids that could not be recreated
EXCLUDED_IDS = [13787, 14215, 14217, 14218, 14222, 14223, 14224, 14225, 14226, 14227, 14228, 14229, \
                14230, 14231, 14232, 14233, 14234, 14235, 14236, 14237, 14238, 14239, 14240, 14241, \
                14242, 14243, 14244, 14245, 14246, 14247, 14248, 14249, 14250, 20108, 20109]


def fill_in_article_id(self, session):
    def _remove_url_and_title(data):
        d = json.loads(data)
        if isinstance(d, dict):
            d.pop('url', None)
            d.pop('title', None)
            d.pop('articleURL',None)
            return json.dumps(d)
        return data

    found_article_id = self._ugly_but_historically_relevant_find_or_create_article_id(session)
    self.has_article_id = False
    if found_article_id:
        self.article_id = found_article_id
        self.has_article_id = True
        self.extra_data = _remove_url_and_title(self.extra_data)
        if self.value.startswith('http'):
            self.value = ''

    session.add(self)
    session.commit()


db_session = zeeguu.db.session

all_data = UserActivityData.find()
data = [each for each in all_data if each.id > 77420]

for user_action in data:
    # Special cases that causes a DB exception because of non supported symbols from the article
    if user_action.id not in EXCLUDED_IDS:
        if user_action.has_article_id is None:
            print(user_action.id)
            fill_in_article_id(user_action, db_session)
            if user_action.has_article_id:
                print(user_action.article.url.as_string())
