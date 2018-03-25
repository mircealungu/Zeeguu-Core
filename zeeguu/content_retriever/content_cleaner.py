def cleanup_non_content_bits(text: str):
    """

        Sometimes newspaper still leaves some individual fragments
        in the article.text.


    :param text:
    :return:
    """
    new_text = text.replace("\nAdvertisement\n", "")

    return new_text
