import itertools
import traceback

import zeeguu

from zeeguu.model.bookmark_priority_arts import BookmarkPriorityARTS
from zeeguu.model.exercise import Exercise
from zeeguu.model.exercise_source import ExerciseSource

from zeeguu.algos.algorithm_wrapper import AlgorithmWrapper
from zeeguu.algos.analysis.normal_distribution import NormalDistribution
from zeeguu.algos.arts.arts_rt import ArtsRT
from zeeguu.model.learner_stats.exercise_stats import ExerciseStats
from zeeguu.util.timer_logging_decorator import time_this

db = zeeguu.db


class PriorityInfo:
    MAX_PRIORITY = 1000
    NO_PRIORITY = -1000

    def __init__(self, bookmark, exercise, priority=MAX_PRIORITY):
        self.bookmark = bookmark
        self.exercise = exercise
        self.priority = priority


class AlgoService:
    """
        
        service calls the wrapper that calls the algorithm 
        
    """
    algorithm_wrapper = AlgorithmWrapper(ArtsRT)

    @classmethod
    def update_exercise_source_stats(cls):
        exercise_sources = list(ExerciseSource.query.all())
        for source in exercise_sources:
            exercises = Exercise.query.filter_by(source_id=source.id)
            reaction_times = map(lambda x: x.solving_speed, exercises)
            mean, sd = NormalDistribution.calc_normal_distribution(
                reaction_times)
            exercise_stats = ExerciseStats(source, mean, sd)
            db.session.merge(exercise_stats)

        db.session.commit()

    @classmethod
    @time_this
    def update_bookmark_priority(cls, db, user):

        try:
            print ("in update bookmark priority...")
            bookmarks_for_user = [b for b in user.all_bookmarks() if b.fit_for_study]
            if len(bookmarks_for_user) == 0:
                return

            # tuple(0=bookmark, 1=exercise)
            bookmark_exercise_of_user = map(cls._get_exercise_of_bookmark, bookmarks_for_user)
            b1, b2 = itertools.tee(bookmark_exercise_of_user, 2)

            max_iterations = max(pair.exercise.id if pair.exercise is not None else 0 for pair in b1)
            exercises_and_priorities = [cls._calculate_bookmark_priority(x, max_iterations) for x in b2]

            with db.session.no_autoflush:  # might not be needed, but just to be safe
                for each in exercises_and_priorities:
                    entry = BookmarkPriorityARTS.find_or_create(each.bookmark, each.priority)
                    entry.priority = each.priority
                    db.session.add(entry)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print('Error during updating bookmark priority')
            print(e)
            print(traceback.format_exc())

    @classmethod
    def _calculate_bookmark_priority(cls, x, max_iterations):
        if x.exercise is not None:

            if x.exercise.solving_speed > 0:
                x.priority = cls.algorithm_wrapper.calculate(x.exercise, max_iterations)

            else:
                # solving speed is -1 for the cases where there was some feedback
                # from the user (either that it's too easy, or that there's something
                # wrong with it. we shouldn't schedule the bookmark in this case.
                # moreover, even if we wanted we can't since there's a log of reaction
                # time somewhere and it won't work with -1!
                x.priority = PriorityInfo.NO_PRIORITY
        else:
            x.priority = PriorityInfo.MAX_PRIORITY
        return x

    @staticmethod
    def _get_exercise_of_bookmark(bookmark):
        if 0 < len(bookmark.exercise_log):
            return PriorityInfo(bookmark=bookmark, exercise=bookmark.exercise_log[-1])

        return PriorityInfo(bookmark=bookmark, exercise=None)
