from zeeguu.model.user_activitiy_data import UserActivityData
from zeeguu.model.user_reading_session import UserReadingSession

import zeeguu

'''
    Script that loops through all the exeuser_activity_data actions in the database, and recomputes the history of
    reading sessions.

    WARNING: Do not run twice or it will inserd duplicated data
'''
#List of excluded ids that could not be recreated
EXCLUDED_IDS = [20108]

db_session = zeeguu.db.session

data = UserActivityData.find()

for user_action in data:
    #Special case that causes a DB exception because of non supported symbols from the article
    if user_action.id not in EXCLUDED_IDS: 
        
        # NOTE: Not all scenarios include the url
        user = user_action.user_id
        time = user_action.time

        UserReadingSession.update_reading_session(db_session, 
                                                    user_action.event, 
                                                    user, 
                                                    user_action.find_or_create_article_id(db_session),
                                                    current_time = time
                                                )
        print(user_action.id)
