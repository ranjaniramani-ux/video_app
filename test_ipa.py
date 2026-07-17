import eng_to_ipa as ipa

for word in [
    "rain",
    "dog",
    "lake",
    "school",
    "water",
    "banana",
    "police officer"
]:
    print(word, "->", ipa.convert(word))