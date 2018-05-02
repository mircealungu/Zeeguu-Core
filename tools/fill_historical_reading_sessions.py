from zeeguu.model.user_activitiy_data import UserActivityData
from zeeguu.model.user_reading_session import UserReadingSession

import zeeguu

db_session = zeeguu.db.session

data = UserActivityData.find()

for user_action in data:
    if user_action.id >20108:
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
