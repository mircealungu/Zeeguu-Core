from zeeguu.model import UserActivityData

all_events = UserActivityData.find(event_filter='UMR - USER FEEDBACK')

nicer = {
    '"not_finished_for_broken"': "BROKEN",
    '"maybe_finish_later"': "Later",
    '"finished_difficulty_ok"': "OK",
    '"finished_difficulty_hard"': "HARD",
    '"finished_difficulty_easy"': "EASY",
    '"not_finished_for_other"': "Not Finished/ OTHER"
}

prev_user = ''

for each in all_events:
    if each.user_id != 534:
        if prev_user != each.user.name:
            print(each.user.name)
            print(each.time)
            prev_user = each.user.name

        print("  " + nicer[each.extra_data] + " " + each.value)
