from .feed_retrieval import retrieve_articles_from_all_feeds
from .recompute_recommender_cache import clean_the_cache, recompute_for_users

retrieve_articles_from_all_feeds()
clean_the_cache()
recompute_for_users()
