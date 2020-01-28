import zeeguu_core
from wordstats import Word
from zeeguu_core.bookmark_quality import quality_top_bookmark


def top_bookmarks(self, count=50, also_print=False):
    from zeeguu_core.model import Bookmark, UserWord

    def rank(b):
        return Word.stats(b.origin.word, b.origin.language.code).rank

    query = zeeguu_core.db.session.query(Bookmark)
    all_bookmarks = (query.
                     join(UserWord, Bookmark.origin_id == UserWord.id).
                     filter(UserWord.language_id == self.learned_language_id).
                     filter(Bookmark.user_id == self.id).
                     filter(Bookmark.learned == False).order_by(
        Bookmark.time.desc()).limit(400))

    single_word_bookmarks = [each for each in all_bookmarks if quality_top_bookmark(each)]

    sorted_bookmarks = sorted(single_word_bookmarks,
                              key=lambda b: rank(b))
    sorted_bookmarks = sorted_bookmarks[:count]

    if also_print:
        for b in sorted_bookmarks:
            print(f"{b.origin.word} ({b.origin.language.code})- {rank(b)} (id: {b.id})")

    return sorted_bookmarks
