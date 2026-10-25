def normalize_persian_text(value):
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    return (
        text
        .replace("ي", "ی")
        .replace("ى", "ی")
        .replace("ك", "ک")
        .replace("ۀ", "ه")
        .replace("ة", "ه")
        .replace("ؤ", "و")
    )
def normalize_persian_search_text(value):
    text = normalize_persian_text(value)
    return ( 
        text
        .replace("ا", "آ")
    )