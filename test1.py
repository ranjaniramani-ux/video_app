import eng_to_ipa as ipa
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

word = "rain"

ipa_word = ipa.convert(word)

print("IPA:", ipa_word)

print(
    transliterate(
        ipa_word,
        sanscript.OPTITRANS,
        sanscript.TAMIL
    )
)