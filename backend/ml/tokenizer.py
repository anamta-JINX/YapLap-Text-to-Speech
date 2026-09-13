import re
import string

SYMBOLS = "_~ " + string.ascii_lowercase + "!'(),-.:;?"
SYMBOL_TO_ID = {symbol: index for index, symbol in enumerate(SYMBOLS)}
PAD_ID = SYMBOL_TO_ID["_"]
UNK_ID = SYMBOL_TO_ID["~"]


def normalize_text(text: str) -> str:
    text = text.lower().replace("’", "'").replace("—", "-")
    text = re.sub(r"[^a-z !'(),\-.:;?]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def text_to_sequence(text: str) -> list[int]:
    clean = normalize_text(text)
    return [SYMBOL_TO_ID.get(char, UNK_ID) for char in clean] or [UNK_ID]
