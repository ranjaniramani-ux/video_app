# Import all required MoviePy classes (video, audio, text handling)
from moviepy import *

# gTTS is used to convert text to speech (English voice)
from gtts import gTTS

# Google Translator to translate English → Indian language
from googletrans import Translator

# requests is used to download the image from the internet
import requests

# os is used for file cleanup (delete temp audio)
import os

from PIL import Image




# ============================
# STEP 1: TAKE USER INPUTS
# ============================

import sys

if len(sys.argv) < 5:
    print("Usage: app.py <english> <translated> <image_url> <output>")
    sys.exit(1)

english_word = sys.argv[1]
translated_word = sys.argv[2]
image_url = sys.argv[3]
output_file = sys.argv[4]







# ============================
# STEP 2: LANGUAGE CODE MAPPING
# ============================

# Mapping Indian languages to Google Translate language codes
lang_map = {
    "kannada": "kn",
    "tamil": "ta",
    "telugu": "te",
    "hindi": "hi",
    "malayalam": "ml"
}

# Get the correct language code (default = Kannada)
lang_code = lang_map.get(language, "kn")


# ============================
# STEP 3: TRANSLATE THE WORD
# ============================

# Create translator object
#translator = Translator()

# Translate English word into selected Indian language
#translated = translator.translate(english_word, dest=lang_code).text


# ============================
# STEP 4: SELECT FONT FOR LANGUAGE
# ============================

# Each Indian script needs its own Unicode font
font_map = {
    "hindi": "NotoSansDevanagari-Regular.ttf",
    "marathi": "NotoSansDevanagari-Regular.ttf",
    "tamil": "NotoSansTamil-Regular.ttf",
    "kannada": "NotoSansKannada-Regular.ttf",
    "telugu": "NotoSansTelugu-Regular.ttf",
    "malayalam": "NotoSansMalayalam-Regular.ttf",
    "bengali": "NotoSansBengali-Regular.ttf"
}

# Pick font based on selected language
font_file = font_map.get(language, "NotoSansDevanagari-Regular.ttf")


# Combine English and translated word with hyphen
display_text = f"{english_word.upper()} - {translated_word}"



# ============================
# STEP 5: DOWNLOAD IMAGE
# ============================


# ---------------- DOWNLOAD & RESIZE IMAGE ----------------
img_bytes = requests.get(image_url).content
with open("image.jpg", "wb") as f:
    f.write(img_bytes)

# Resize image to 1280x720 to prevent memory errors
img = Image.open("image.jpg")
img = img.convert("RGB")
img = img.resize((1280, 720))
img.save("image.jpg")



# ============================
# STEP 6: CREATE AUDIO
# ============================

# Generate English speech saying the word 3 times
tts = gTTS(text=f"{english_word}. {english_word}. {english_word}.", lang="en")

# Save speech audio to file
tts.save("voice.mp3")

# Load speech audio
speech = AudioFileClip("voice.mp3")

# Create 5 seconds of silence
silence = AudioClip(lambda t: 0, duration=5)

# Combine silence + speech (speech starts after 5 seconds)
final_audio = CompositeAudioClip([
    silence,
    speech.with_start(5)
])


# ============================
# STEP 7: CREATE VIDEO
# ============================

# Total video duration = 5 sec silence + speech duration
#Commenttotal_duration = 5 + speech.duration
img_clip = ImageClip("image.jpg").with_duration(6)


# Create image clip for full duration
#Commentimg_clip = ImageClip("image.jpg").with_duration(total_duration)

# Create text overlay (top-left, bold, high contrast)
text_clip = TextClip(
    text=display_text,
    font=font_file,            # Unicode font for Indian languages
    font_size=80,              # Large text
    color="white",             # Text color
    stroke_color="black",      # Outline for visibility
    stroke_width=3,
    method="caption",          # Required for Unicode rendering
    size=(1200, 150)           # Mandatory for caption method
).with_position((30, 30)).with_duration(total_duration)

video = CompositeVideoClip([img_clip, text_clip])
final = video
final.write_videofile(output_file, fps=24, codec="libx264")
# Combine image + text
#Commentvideo = CompositeVideoClip([img_clip, text_clip])

# Attach audio to video
#Commentfinal = video.with_audio(final_audio)


# ============================
# STEP 8: EXPORT FINAL VIDEO
# ============================

# Write the final MP4 file
#Commentfinal.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac")


# Delete temporary audio file
#Commentos.remove("voice.mp3")

print("✅ output generated successfully")
