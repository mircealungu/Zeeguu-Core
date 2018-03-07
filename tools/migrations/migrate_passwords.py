# script used to convert

import zeeguu
from zeeguu.model import User

session = zeeguu.db.session

for user in User.query.all():
    print (f'updating user {user}')
    user.password = user.password.hex()
    user.password_salt = user.password_salt.hex()
    session.add(user)

session.commit()

# now make sure to change the column type of the
# table to string.
