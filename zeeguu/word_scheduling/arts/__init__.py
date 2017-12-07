"""
    The main two public methods of this package are:

           bookmarks_to_study
               returns a list of bookmarks to study

            update_bookmark_priority
                this can be time consuming, so the caller might want
                to call it separately; in theory they can also call
                it before every call to bookmarks_to_study

"""

from .arts_diff_fast import ArtsDiffFast
from .arts_diff_slow import ArtsDiffSlow
from .arts_rt import ArtsRT
from .arts_random import ArtsRandom
from . import words_to_study
from . import bookmark_priority_updater


def bookmarks_to_study(user, desired_bookmarks_count=10):
    return words_to_study.bookmarks_to_study(user, desired_bookmarks_count)


def update_bookmark_priority(db, user):
    return bookmark_priority_updater.BookmarkPriorityUpdater.update_bookmark_priority(db, user)
