"""
    The main two public methods of this package are:

           bookmarks_to_study
               returns a list of bookmarks to study

            update_bookmark_priority
                this can be time consuming, so the caller might want
                to call it separately; in theory they can also call
                it before every call to bookmarks_to_study by setting
                the corresponding method argument in that method to True

"""

from .arts_diff_fast import ArtsDiffFast
from .arts_diff_slow import ArtsDiffSlow
from .arts_rt import ArtsRT
from .arts_random import ArtsRandom
from . import words_to_study
from . import bookmark_priority_updater


def bookmarks_to_study(user, desired_bookmarks_count=10, db = None, compute_priority_before=False):

    """

        Note that updating bookmark priority might be slow; this is by default turned off...

    :param user:
    :param desired_bookmarks_count:
    :param db: can be none if one needs not update the priorities beforehand
    :param compute_priority_before: 
    :return:
    """

    if compute_priority_before:
        update_bookmark_priority(db, user)

    return words_to_study.bookmarks_to_study(user, desired_bookmarks_count)


def update_bookmark_priority(db, user):
    return bookmark_priority_updater.BookmarkPriorityUpdater.update_bookmark_priority(db, user)
