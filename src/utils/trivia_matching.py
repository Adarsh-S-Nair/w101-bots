"""Conservative, desktop-independent question matching. Never fuzzy-guess."""
import re
import unicodedata


def normalize_text(text):
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKC", text).casefold()
    text = text.translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'}))
    return re.sub(r"\s+", " ", text).strip()


def find_answer(questions, question):
    key = normalize_text(question)
    if not key:
        return None
    matches = [answer for candidate, answer in questions.items()
               if normalize_text(candidate) == key]
    if not matches or any(not isinstance(answer, str) or not answer.strip() for answer in matches):
        return None
    if len({normalize_text(answer) for answer in matches}) != 1:
        return None
    return matches[0]
