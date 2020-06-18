import zeeguu_core

JUNK_PATTERNS = [

    "\nAdvertisement\n",
    "\ntrue\n",
    "\nAutomatisk oplaæsning\n",
    "Der er ikke oplæsning af denne artikel, så den oplæses derfor med maskinstemme. Kontakt os gerne på automatiskoplaesning@pol.dk, hvis du hører ord, hvis udtale kan forbedres. Du kan også hjælpe ved at udfylde spørgeskemaet herunder, hvor vi spørger, hvordan du har oplevet den automatiske oplæsning. Spørgeskema om automatisk oplæsning",
    "Som registreret bruger kan du overvåge emner og journalister og modtage nyhederne i din indbakke og følge din nyhedsstrøm på Finans.",

]


def cleanup_non_content_bits(text: str):
    """

        Sometimes newspaper still leaves some individual fragments
        in the article.text.


    :param text:
    :return:
    """
    new_text = text

    for junk_pattern in JUNK_PATTERNS:
        cleaned = new_text.replace(junk_pattern, "")

        if cleaned != new_text:
            zeeguu_core.log(f"cleaned: {junk_pattern}")
            new_text = cleaned

    return new_text
