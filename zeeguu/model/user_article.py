from datetime import datetime

from sqlalchemy.orm.exc import NoResultFound

import zeeguu
from sqlalchemy import Column, UniqueConstraint, Integer, ForeignKey, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from zeeguu.model import Article, User


class UserArticle(zeeguu.db.Model):
    """

        A user and an article.
        It's simple.

        Did she open it?
        Did she like it?

        This is the kind of info that's in here.

    """
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = Column(Integer, primary_key=True)


    user_id = Column(Integer, ForeignKey(User.id))
    user = relationship(User)

    article_id = Column(Integer, ForeignKey(Article.id))
    article = relationship(Article)

    # Together an url_id and user_id are UNIQUE :)
    UniqueConstraint(article_id, user_id)

    # once an article has been opened, we display it
    # in a different way in the article list; we might
    # also, just as well not even show it anymore
    # we don't keep only the boolean here, since it is
    # more informative to have the time when opened;
    # could turn out to be useful for showing the
    # user reading history for example
    opened = Column(DateTime)

    # There's a star icon at the top of an article;
    # Reader can use it to mark the article in any way
    # they like.
    starred = Column(DateTime)

    # There's a button at the bottom of every article
    # this tracks the state of that button
    liked = Column(Boolean)

    def __init__(self, user, article, opened=None, starred=None, liked=False):
        self.user = user
        self.article = article
        self.opened = opened
        self.starred = starred
        self.liked = liked

    def __repr__(self):
        return f'{self.user} and {self.article}: Opened: {self.opened}, Starred: {self.starred}, Liked: {self.liked}'

    def set_starred(self, state=True):
        if state:
            self.starred = datetime.now()
        else:
            self.starred = None

    @classmethod
    def find_or_create(cls, session, user: User, article: Article, opened=None, liked=False, starred=None):
        """

            create a new object and add it to the db if it's not already there
            otherwise retrieve the existing object and update

        """
        try:
            return cls.query.filter_by(
                user=user,
                article=article
            ).one()
        except NoResultFound:
            try:
                new = cls(user, article, opened=opened, liked=liked, starred=starred)
                print (f'starred: {starred}')
                session.add(new)
                session.commit()
                return new
            except Exception as e:
                print("seems we avoided a race condition")
                session.rollback()
                return cls.query.filter_by(
                    user=user,
                    article=article
                ).one()

    @classmethod
    def all_starred_articles_of_user(cls, user):
        return cls.query.filter_by(user=user).filter(UserArticle.starred.isnot(None)).all()

    @classmethod
    def all_starred_articles_of_user_info(cls, user):

        """

            prepares info as it is promised by /get_starred_articles

        :param user:
        :return:
        """

        user_articles = cls.all_starred_articles_of_user(user)

        dicts = [dict(
            user_id=each.user.id,
            url=each.article.url.as_string(),
            title=each.article.title,
            language=each.article.language.code,
            starred_date=each.starred.strftime("%Y-%m-%dT%H:%M:%S%z")
        ) for each in user_articles]

        return dicts

    @classmethod
    def exists(cls, obj):
        try:
            cls.query.filter(
                cls.id == obj.id
            ).one()
            return True
        except NoResultFound:
            return False
