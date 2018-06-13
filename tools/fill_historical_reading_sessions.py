from zeeguu.model.user_activitiy_data import UserActivityData
from zeeguu.model.user_reading_session import UserReadingSession

import zeeguu

'''
    Script that loops through all the exeuser_activity_data actions in the database, and recomputes the history of
    reading sessions.

    NOTE: It deletes and recreates the table
'''
#List of excluded ids that could not be recreated
EXCLUDED_IDS = [13787, 14215, 14217, 14218, 14222, 14223, 14224, 14225, 14226, 14227, 14228, 14229,\
                14230, 14231, 14232, 14233, 14234, 14235, 14236, 14237, 14238, 14239, 14240, 14241,\
                14242, 14243, 14244, 14245, 14246, 14247, 14248, 14249, 14250, 20108, 20109]

db_session = zeeguu.db.session

#Clear table before starting
# UserReadingSession.query.delete()
db_session.commit()

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
