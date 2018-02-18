import zeeguu
from sqlalchemy import Column, Integer, String


class Cohort(zeeguu.db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = Column(Integer, primary_key=True)

    name = Column(String(255))

    invitation_code = Column(String(255))

    def __init__(self, name, invitation_code=""):
        self.name = name
        self.invitation_code = invitation_code

    def get_students(self):
        from zeeguu.model.user import User

        # compatibility reasons: if there is an associated invitation code
        # use it; otherwise fallback on the cohort that's associated with the User
        if len(self.invitation_code) > 1:
            return User.query.filter(User.invitation_code == self.invitation_code).all()

        return User.query.filter(User.cohort == self).all()

    def get_teachers(self):
        from zeeguu.model.teacher_cohort_map import TeacherCohortMap
        return TeacherCohortMap.get_teachers_for(self)

    @classmethod
    def find(cls, id):
        return cls.query.filter_by(id=id).one()
