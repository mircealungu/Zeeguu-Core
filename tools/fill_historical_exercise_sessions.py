from zeeguu.model.exercise import Exercise
from zeeguu.model.user_exercise_session import UserExerciseSession

import zeeguu

'''
    Script that loops through all the exercises in the database, and recomputes the history of
    exercise sessions.

    WARNING: Do not run twice or it will inserd duplicated data
'''
db_session = zeeguu.db.session

data = Exercise.find()

for user_exercise in data:
    
    UserExerciseSession.update_exercise_session(user_exercise, db_session)
    print(user_exercise.id)
