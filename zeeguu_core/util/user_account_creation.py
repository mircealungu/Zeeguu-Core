import sqlalchemy

import zeeguu_core
from zeeguu_core.emailer.user_activity import send_new_user_account_email
from zeeguu_core.model import Cohort, User, Teacher


def valid_invite_code(invite_code):
    return (invite_code in zeeguu_core.app.config.get("INVITATION_CODES")
            or Cohort.exists_with_invite_code(invite_code))


def create_account(db_session, username, password, invite_code, email):
    cohort_name = ""
    if password is None or len(password) < 4:
        return "Password should be at least 4 characters long"

    if not valid_invite_code(invite_code):
        return "Invitation code is not recognized. Please contact us."

    try:

        cohort = Cohort.query.filter_by(inv_code=invite_code).first()

        if cohort:
            # if the invite code is from a cohort, then there has to be capacity
            if not cohort.cohort_still_has_capacity():
                return "No more places in this class. Please contact us (zeeguu.team@gmail.com)."

            cohort_name = cohort.name

        new_user = User(email, username, password, invitation_code=invite_code, cohort=cohort)
        db_session.add(new_user)

        if cohort:
            if cohort.is_cohort_of_teachers:
                teacher = Teacher(new_user)
                db_session.add(teacher)

        db_session.commit()

        send_new_user_account_email(username, invite_code, cohort_name)


    except sqlalchemy.exc.IntegrityError:
        return "There is already an account for this email."
    except Exception as e:
        return "Could not create the account"

    return "OK"
