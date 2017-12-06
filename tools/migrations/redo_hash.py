# script used to convert the old binary hashes
# to their hex counterparts. binary can not be
# insured UNIQUE by a mysql constraint
import zeeguu
from zeeguu import util
from zeeguu.model import Text

session = zeeguu.db.session

texts = session.query(Text).all()
for t in texts:
    t.content_hash = util.text_hash(t.content)
    session.add(t)
    session.commit()
# input ("next?/")
