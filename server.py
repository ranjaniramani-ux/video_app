"""
server.py  —  Flask backend for Language Video Generator

pip install flask deep-translator indic-transliteration moviepy gtts pillow requests
"""

from flask import Flask, request, send_file, render_template, jsonify
from deep_translator import GoogleTranslator
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
import subprocess
import uuid
import sys
import os

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ── language config ───────────────────────────────────────────────────────────

LANG_CODE = {
    "kannada":   "kn",
    "tamil":     "ta",
    "hindi":     "hi",
    "telugu":    "te",
    "malayalam": "ml",
}

# Target script for each language — used to write the English word
# phonetically IN the native script so kids can sound it out
LANG_SCRIPT = {
    "kannada":   sanscript.KANNADA,
    "tamil":     sanscript.TAMIL,
    "hindi":     sanscript.DEVANAGARI,
    "telugu":    sanscript.TELUGU,
    "malayalam": sanscript.MALAYALAM,
}

LANG_FONT = {
    "tamil": "NotoSansTamil-Regular.ttf",
    "hindi": "NotoSansDevanagari-Regular.ttf",
    "kannada": "NotoSansKannada-Regular.ttf",
    "telugu": "NotoSansTelugu-Regular.ttf",
    "malayalam": "NotoSansMalayalam-Regular.ttf",
}

LATIN_FONT = "NotoSans-Regular.ttf"


def english_to_native_script(english_word: str, language: str) -> str:
    """
    Write the English word phonetically in the native script.
    e.g.  'apple'  →  'அப்ப்லே'  (Tamil)
          'mango'  →  'மங்கோ'    (Tamil)

    This uses OPTITRANS → native script conversion so Tamil/Kannada kids
    can read the English pronunciation using letters they already know.
    """
    script = LANG_SCRIPT.get(language)
    if not script:
        return ""
    try:
        # OPTITRANS is a casual romanisation scheme designed to map
        # English-like phonetic spellings to Indic scripts
        result = transliterate(english_word.lower(), sanscript.OPTITRANS, script)
        return result
    except Exception as e:
        print(f"Transliteration error: {e}")
        return ""


# ── routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/translate", methods=["POST"])
def translate_route():
    data     = request.get_json(force=True)
    word     = (data.get("english_word") or "").strip()
    language = (data.get("language") or "").strip().lower()

    if not word or not language:
        return jsonify({"error": "Missing fields"}), 400

    lang_code = LANG_CODE.get(language)
    if not lang_code:
        return jsonify({"error": f"Unsupported language: {language}"}), 400

    try:
        # 1. Translate English word → native language
        translated = GoogleTranslator(source="en", target=lang_code).translate(word)

        # 2. Write the English word phonetically IN the native script
        #    so kids can sound out the English pronunciation
        transliteration = english_to_native_script(word, language)

        print(f"  '{word}' → '{translated}' | phonetic: '{transliteration}'")

        return jsonify({
            "translated":      translated,
            "transliteration": transliteration,
        })

    except Exception as e:
        print(f"TRANSLATE ERROR: {e}")
        return jsonify({"error": f"Translation failed: {e}"}), 500


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)

    english         = (data.get("english_word")    or "").strip()
    translated      = (data.get("translated_word") or "").strip()
    transliteration = (data.get("transliteration") or "").strip()
    image_url       = (data.get("image_url")       or "").strip()
    language        = (data.get("language")        or "tamil").strip().lower()

    if not english or not translated or not image_url:
        return jsonify({"error": "Missing required fields"}), 400
    if not image_url.startswith(("http://", "https://")):
        return jsonify({"error": "Image URL must start with http:// or https://"}), 400

   
    font_file = LANG_FONT.get(language, "NotoSansTamil-Regular.ttf")
    output    = f"{uuid.uuid4()}.mp4"

    print(f"\nGenerating video: {english} → {translated} | {transliteration}")
    print(f"  image: {image_url}")
    print(f"  font:  {font_file}")

    try:
        result = subprocess.run(
            [
                sys.executable, "app.py",
                english, translated, transliteration,
                image_url, output, font_file, LATIN_FONT,
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )

        print("WORKER STDOUT:", result.stdout)
        if result.stderr:
            print("WORKER STDERR:", result.stderr)

        if result.returncode != 0:
            detail = result.stdout[-800:] + result.stderr[-400:]
            return jsonify({"error": "Video generation failed", "detail": detail}), 500

        if not os.path.exists(output) or os.path.getsize(output) == 0:
            return jsonify({"error": "Video file was not created"}), 500

        return send_file(output, mimetype="video/mp4")

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Video generation timed out after 3 minutes"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            os.remove(output)
        except OSError:
            pass


@app.route("/merge", methods=["POST"])

def merge():
    data = request.get_json(force=True)
    
   
    print("MERGE INPUT:", data)
    if not isinstance(data, list) or len(data) == 0:
        return jsonify({"error": "Expected a non-empty list"}), 400

    language  = (data[0].get("language") or "tamil").strip().lower()
    font_file = LANG_FONT.get(language, "NotoSansTamil-VariableFont_wdth,wght.ttf")
    clips     = []
    output    = f"{uuid.uuid4()}_merged.mp4"
    

    

    try:
        for item in data:
            add_logo = item.get("add_logo", False)
            print("Add Logo Checkbox:", add_logo)
            english         = (item.get("english_word")    or "").strip()
            translated      = (item.get("translated_word") or "").strip()
            transliteration = (item.get("transliteration") or "").strip()
            image_url       = (item.get("image_url")       or "").strip()
            

            if not english or not image_url:
                continue

            clip_out = f"{uuid.uuid4()}.mp4"
            result = subprocess.run(
                [
                    sys.executable, "app.py",
                    english, translated, transliteration,
                    image_url, clip_out, font_file, LATIN_FONT,
                    str(add_logo) 
                ],
                capture_output=True,
                text=True,
                timeout=180,
            )
            if result.returncode != 0:
                print("MERGE WORKER ERROR:", result.stdout, result.stderr)
                continue
            clips.append(clip_out)

        if not clips:
            return jsonify({"error": "No videos could be generated"}), 400
            print("FAILED ROW:", item)
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)

        from moviepy import VideoFileClip, concatenate_videoclips
        video_clips = [VideoFileClip(c) for c in clips]
        final       = concatenate_videoclips(video_clips)
        final.write_videofile(output, codec="libx264", audio_codec="aac")

        for vc in video_clips:
            vc.close()
        final.close()

        return send_file(output, as_attachment=True, download_name="merged.mp4")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        for c in clips:
            try:
                os.remove(c)
            except OSError:
                pass
        try:
            os.remove(output)
        except OSError:
            pass


if __name__ == "__main__":
    app.run(debug=True)