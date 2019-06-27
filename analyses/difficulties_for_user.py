#!/usr/local/bin/python3.6
from sqlalchemy.orm.exc import NoResultFound

from zeeguu_core.model import UserActivityData, User, Article

users = User.query.order_by(User.id.desc()).all()


def print_feedback_info(activity_data, user):
    try:
        art = Article.query.filter_by(id=activity_data.article_id).one()

        line = " , , "

        if "easy" in activity_data.value:
            line += f"{art.fk_difficulty}"
        line += ", "

        if "ok" in activity_data.value:
            line += f"{art.fk_difficulty}"
        line += ", "

        if ("finished_hard" in activity_data.value) or ("finished_difficulty_hard" in activity_data.value):
            line += f"{art.fk_difficulty}"
        line += ", "

        if activity_data.value == "finished_very_hard":
            line += f"{art.fk_difficulty}"
        line += ", "

        if activity_data.value == "not_finished_for_too_difficult":
            line += f"{art.fk_difficulty}"

        line += f", https://www.zeeguu.org/bookmarks_for_article/{art.id}/{user.id}"

        print(line)


    except NoResultFound:
        print(f"no art found for {activity_data.id}, {activity_data.value}")


print(f"User, language, easy, ok, hard, very hard, not_finished_for_too_difficult, link")

user_events = {}
for user in users:
    user_events [user] = UserActivityData.find(event_filter='UMR - USER FEEDBACK', user=user)


ordered_users = sorted(users, key=lambda x: len(user_events[x]), reverse=True)


for user in ordered_users:
    all_events = UserActivityData.find(event_filter='UMR - USER FEEDBACK', user=user)

    if len(all_events) < 5:
        continue

    if user.id == 534:
        continue

    print(f"{user.name}, {user.learned_language.code} , , , , , , ")
    for event_data in all_events:
        print_feedback_info(event_data, user)

    print(" ")
