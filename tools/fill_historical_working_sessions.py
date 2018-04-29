from zeeguu.model.user_activitiy_data import UserActivityData
from zeeguu.model.user_working_session import UserWorkingSession

import zeeguu

db_session = zeeguu.db.session

data = UserActivityData.find()

for user_action in data:
    # NOTE: Not all scenarios include the url
    user = user_action.user_id
    time = user_action.time

    UserWorkingSession.update_working_session(db_session, 
                                                user_action.event, 
                                                user, 
                                                user_action.find_or_create_article_id(db_session),
                                                sys_time = time
                                            )
    print(user_action.id)
