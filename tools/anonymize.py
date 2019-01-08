# Script:
#
# anonymize all users in the current DB
#
# works with the db that is defined in the configuration
# pointed by ZEEGUU_CORE_CONFIG
#
#
#
#


from zeeguu_core.model import User
from zeeguu_core import db
from faker import Faker
fake = Faker()


dbs = db.session

all_users = User.query.all()
for user in all_users:
    for i in range(10):
        try:
            print (f"renaming {user.name} - {user.email}")
            user.name = fake.name()
            user.email = fake.email()
            dbs.add(user)
            dbs.commit()
            print (f"... now we have {user.name} - {user.email}")
        except Exception as e:
            print (f"failed for {user.name} the {i}th time... will try again")
            print (e)

        break

