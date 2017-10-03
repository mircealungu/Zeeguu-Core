import zeeguu
from zeeguu.model.bookmark import Bookmark
from zeeguu.model.bookmark_priority_arts import BookmarkPriorityARTS
from zeeguu.util.timer_logging_decorator import time_this


@time_this
def bookmarks_to_study(user, desired_bookmarks_count=-1):
    zeeguu.log("preparing to query words_to_study")

    bookmarks = Bookmark.query. \
        filter_by(user_id=user.id). \
        filter_by(fit_for_study=True). \
        join(BookmarkPriorityARTS). \
        filter(BookmarkPriorityARTS.bookmark_id == Bookmark.id). \
        order_by(BookmarkPriorityARTS.priority.desc()). \
        all()

    zeeguu.log("about to return the words_to_study")
    return bookmarks[:desired_bookmarks_count]
