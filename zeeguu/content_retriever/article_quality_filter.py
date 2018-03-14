from zeeguu.model import Article


def sufficient_quality(text, reason_dict):
    word_count = len(text.split(" "))

    if word_count < Article.MINIMUM_WORD_COUNT:
        _update_reason_dict(reason_dict, "Too Short")

        return False

    if text.find("Read More") > 0:
        _update_reason_dict(reason_dict, 'Contains "Read More"')

        return False

    return True


def _update_reason_dict(reason_dict, reason):
    reason_dict.setdefault(reason, 0)
    reason_dict[reason] += 1
