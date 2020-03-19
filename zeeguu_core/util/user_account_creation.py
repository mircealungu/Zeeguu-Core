import sqlalchemy

import zeeguu_core
from zeeguu_core.emailer.user_activity import send_new_user_account_email
from zeeguu_core.model import Cohort, User, Teacher


def valid_invite_code(invite_code):
    if (zeeguu_core.app.config.get("INVITATION_CODES") and
            invite_code in zeeguu_core.app.config.get("INVITATION_CODES")):
        return True

    if Cohort.exists_with_invite_code(invite_code):
        return True

    return False


def create_account(db_session, username, password, invite_code, email, learned_language=None, native_language=None):
    cohort_name = ""
    if password is None or len(password) < 4:
        raise Exception("Password should be at least 4 characters long")

    if not valid_invite_code(invite_code):
        raise Exception("Invitation code is not recognized. Please contact us.")

    try:

        cohort = Cohort.query.filter_by(inv_code=invite_code).first()

        if cohort:
            # if the invite code is from a cohort, then there has to be capacity
            if not cohort.cohort_still_has_capacity():
                return "No more places in this class. Please contact us (zeeguu.team@gmail.com)."

            cohort_name = cohort.name

        new_user = User(email, username, password, invitation_code=invite_code, cohort=cohort,
                        learned_language=learned_language, native_language=native_language)
        db_session.add(new_user)

        if cohort:
            if cohort.is_cohort_of_teachers:
                teacher = Teacher(new_user)
                db_session.add(teacher)

        db_session.commit()

        send_new_user_account_email(username, invite_code, cohort_name)

        return new_user

    except sqlalchemy.exc.IntegrityError:
        raise Exception("There is already an account for this email.")
    except Exception as e:
        raise Exception("Could not create the account")
