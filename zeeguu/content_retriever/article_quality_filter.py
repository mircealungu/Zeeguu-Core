import zeeguu
from zeeguu.model import Article

html_read_more_patterns = [
    "To continue reading this premium"  # New Scientist
]

plain_text_read_more_patterns = [
    "Create an account for free access to:" # New Scientist
]

incomplete_suggesting_terminations = (
    "Read More",
    "..."
)


def sufficient_quality(art, reason_dict):
    word_count = len(art.text.split(" "))

    if word_count < Article.MINIMUM_WORD_COUNT:
        _update_reason_dict(reason_dict, "Too Short")

        return False

    for each in html_read_more_patterns:
        if art.html.find(each) > 0:
            zeeguu.log(f"Incomplete Article (based on HTML analysis): {art.url}")
            _update_reason_dict(reason_dict, 'Html contains incomplete patterns')
            return False

    for each in plain_text_read_more_patterns:
        if art.text.find(each) > 0:
            zeeguu.log(f"Incomplete Article (based on text analysis): {art.url}")
            _update_reason_dict(reason_dict, 'text contains incomplete patterns"')
            return False

    if art.text.endswith(incomplete_suggesting_terminations):
        zeeguu.log(f"Incomplete Article (ends with words): {art.url}")
        _update_reason_dict(reason_dict, 'Ends with "Read More" or similar terminations')
        return False

    return True


def _update_reason_dict(reason_dict, reason):
    reason_dict.setdefault(reason, 0)
    reason_dict[reason] += 1
