import zeeguu
from zeeguu.model import Article, UserArticle
from zeeguu.model.starred_article import StarredArticle

session = zeeguu.db.session

for starart in StarredArticle.query.all():
    try:
        article = Article.find_or_create(session, starart.url.as_string())
        ua = UserArticle.find_or_create(session, starart.user, article, starred=starart.starred_date)
        session.add(ua)
        session.commit()
        print(ua)
    except Exception as ex:
        print(f'could not import {starart.url.as_string()}')
        print(ex)
