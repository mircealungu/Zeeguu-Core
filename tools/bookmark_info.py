from zeeguu_core.model import Bookmark

bookmark = Bookmark.query.filter_by(id=122228)[0]

print(
    bookmark.most_recent_correct_dates()
)