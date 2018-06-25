#!/usr/bin/env python

"""

   Script that updates the ArticlesCache

   To be called from a cron job.

"""

import zeeguu
from zeeguu.content_recommender.mixed_recommender import reading_preferences_hash, recompute_recommender_cache_if_needed
from zeeguu.model import User, ArticlesCache

session = zeeguu.db.session


def hashes_of_existing_cached_preferences():
    """

        goes through the ArticleCache table and gets
        the distinct content_hashes

    :return:
    """
    query = session.query(ArticlesCache.content_hash.distinct())
    distinct_hashes = [each[0] for each in query.all()]
    return distinct_hashes


def clean_the_cache():
    ArticlesCache.query.delete()
    session.commit()


def recompute_for_users(existing_hashes):
    """

        recomputes only those caches that are already in the table
        and belong to a user. if multiple users have the same preferences
        the computation is donne only for the first because this is how
        recompute_recommender_cache_if_needed does.

        To think about:
        - what happens when this script is triggered simultaneously
        with triggering recompute_recommender_cache_if_needed from
        the UI? will there end up be duplicated recommendations?
        should we add a uninque constraint on (hash x article)?

        Note:

        in theory, the recomputing should be doable independent of users
        in practice, the recompute_recommender_cache takes the user as input.
        for that function to become independent of the user we need to be
        able to recover the ids of the languages, topics, searchers, etc. from the
        content_hash
        to do this their ids would need to be comma separated

        OTOH, in the future we might still want to have a per-user cache
        because the recommendations might be different for each user
        since every user has different language levels!!!

    :param existing_hashes:
    :return:
    """
    for user in User.query.all():
        try:
            reading_pref_hash = reading_preferences_hash(user)
            if reading_pref_hash in existing_hashes:
                recompute_recommender_cache_if_needed(user, session)
                print(f"Success for {user}")
        except Exception as e:
            print(f"Failed for user {user}")


existing_hashes = hashes_of_existing_cached_preferences()
clean_the_cache()
recompute_for_users(existing_hashes)