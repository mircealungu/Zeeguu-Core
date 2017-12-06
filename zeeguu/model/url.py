import re

import sqlalchemy.orm
from sqlalchemy import UniqueConstraint

import zeeguu
import time

db = zeeguu.db

from zeeguu.model.domain_name import DomainName


class Url(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(2083))

    path = db.Column(db.String(255))

    domain_name_id = db.Column(db.Integer, db.ForeignKey(DomainName.id))
    domain = db.relationship(DomainName)

    __table_args__ = (
        UniqueConstraint('path', 'domain_name_id', name='_path_domain_unique_constraint'),
        {'mysql_collate': 'utf8_bin'}
    )

    def __init__(self, url: str, title: str, domain: DomainName = None):

        self.path = Url.get_path(url)
        self.title = title
        if domain:
            self.domain = domain
        else:
            self.domain = DomainName.for_url_string(url)

    def make_new(self, session, url: str, title: str):
        self.domain = DomainName.for_url_string(url)
        self.title = title
        self.path = Url.get_path(url)
        self.domain = DomainName.find_or_create(Url.get_domain(url))

    def title_if_available(self):
        if self.title != "":
            return self.title
        return self.as_string()

    def as_string(self):
        return self.domain.domain_name + self.path

    def render_link(self, link_text = None):
        if not link_text:
            _title = self.title
        else:
            _title = link_text
        if self.as_string() != "":
            return '<a href="' + self.as_string() + '">' + _title + '</a>'
        else:
            return ""

    def domain_name(self):
        return self.domain.domain_name

    @classmethod
    def get_domain(cls, url):
        protocol_re = '(.*://)?'
        domain_re = '([^/?]*)'
        path_re = '(.*)'

        domain = re.findall(protocol_re + domain_re, url)[0]
        return domain[0] + domain[1]

    @classmethod
    def get_path(cls, url):
        protocol_re = '(.*://)?'
        domain_re = '([^/?]*)'
        path_re = '(.*)'

        domain = re.findall(protocol_re + domain_re + path_re, url)[0]
        return domain[2]

    @classmethod
    def find_or_create(cls, session: 'Session', _url: str, title: str = ""):

        domain = DomainName.find_or_create(session, _url)
        path = Url.get_path(_url)

        try:
            return cls.query.filter(cls.path == path).filter(cls.domain == domain).one()
        # except sqlalchemy.orm.exc.NoResultFound or sqlalchemy.exc.InterfaceError:
        except:
            try:
                new = cls(_url, title, domain)
                session.add(new)
                session.commit()
                return new
            # except sqlalchemy.exc.IntegrityError or sqlalchemy.exc.DatabaseError:
            except:

                for i in range(10):
                    try:
                        session.rollback()
                        u = cls.find(cls.path == path).filter(cls.domain == domain).first()
                        print("found url after recovering from race")
                        return u
                    except:
                        print("exception of second degree in url..." + str(i))
                        time.sleep(0.3)
                        continue
                    break

    @classmethod
    def find(cls, url, title=""):
        d = DomainName.find(Url.get_domain(url))
        return (cls.query.filter(cls.path == Url.get_path(url))
                .filter(cls.domain == d)
                .one())
