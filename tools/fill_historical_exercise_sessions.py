from zeeguu.model.exercise import Exercise
from zeeguu.model.user_exercise_session import UserExerciseSession

import zeeguu

db_session = zeeguu.db.session

data = Exercise.find()

for user_exercise in data:
    
    #Obtain the user_id
    user_id = user_exercise.find_user_id( db_session)
    time = user_exercise.time

    if user_id:
        UserExerciseSession.update_exercise_session(user_id,
                                                        db_session,
                                                        current_time = time
                                                    )
        print(user_exercise.id)
