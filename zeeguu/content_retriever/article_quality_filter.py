import zeeguu
import newspaper
from zeeguu.model import Article

html_read_more_patterns = [
    "To continue reading this premium",  # New Scientist
    "Cet article est réservé aux abonnés" #Le Figaro
]

plain_text_read_more_patterns = [
    "Create an account for free access to:",  # New Scientist
    "édition abonné" #/www.lemonde.fr
]

incomplete_suggesting_terminations = (
    "Read More"
)


def sufficient_quality(art: newspaper.Article, reason_dict):
    for each in html_read_more_patterns:
        if art.html.find(each) > 0:
            zeeguu.log(f"Incomplete Article (based on HTML analysis): {art.url} contains: {each}")
            _update_reason_dict(reason_dict, f'Html contains incomplete pattern: {each}')
            return False

    return sufficient_quality_of_text(art.text, art.url, reason_dict)


def sufficient_quality_of_text(text: str, url, reason_dict):
    word_count = len(text.split(" "))

    if word_count < Article.MINIMUM_WORD_COUNT:
        _update_reason_dict(reason_dict, "Too Short")

        return False

    for each in plain_text_read_more_patterns:
        if text.find(each) > 0:
            zeeguu.log(f"Incomplete Article (based on text analysis): {url} contains: {each}")
            _update_reason_dict(reason_dict, f'Incomplete pattern in text: {each}"')
            return False

    if text.endswith(incomplete_suggesting_terminations):
        zeeguu.log(f"Incomplete Article (ends with words): {url} ")
        _update_reason_dict(reason_dict, 'Ends with "Read More" or similar')
        return False

    return True


def _update_reason_dict(reason_dict, reason):
    reason_dict.setdefault(reason, 0)
    reason_dict[reason] += 1
