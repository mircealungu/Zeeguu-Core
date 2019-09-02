from zeeguu_core.model import User
from zeeguu_core.word_scheduling.arts.words_to_study import bookmarks_to_study

me = User.find("i@mir.lu")

print(bookmarks_to_study(me))

