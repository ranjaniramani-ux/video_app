import eng_to_ipa as ipa
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

def ipa_to_phonetic(text):
    replacements = {
        "eɪ": "ey",
        "ɔ": "aa",
        "ə": "a",
        "æ": "a",
        "ɪ": "i",
        "i": "ee",
        "u": "oo",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text

word = "rain"

ipa_word = ipa.convert(word)
phonetic = ipa_to_phonetic(ipa_word)

print("IPA      :", ipa_word)
print("PHONETIC :", phonetic)

print(
    transliterate(
        phonetic,
        sanscript.OPTITRANS,
        sanscript.TAMIL
    )
)