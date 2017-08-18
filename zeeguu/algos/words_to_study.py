import zeeguu
from zeeguu.model.bookmark import Bookmark
from zeeguu.model.bookmark_priority_arts import BookmarkPriorityARTS


def bookmarks_to_study(user, desired_bookmarks_count=-1):

    _bookmarks = Bookmark.query. \
        filter_by(user_id=user.id). \
        join(BookmarkPriorityARTS). \
        filter(BookmarkPriorityARTS.bookmark_id == Bookmark.id). \
        order_by(BookmarkPriorityARTS.priority.desc()). \
        all()

    bookmarks = []
    for each in _bookmarks:
        if each.good_for_study():
            bookmarks.append(each)
        else:
            zeeguu.log("rejected bookmark {0} since it is not good for study: {1}".format(each.id, each.origin.word))


    return bookmarks[:desired_bookmarks_count]


