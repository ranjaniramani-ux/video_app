"""
video_worker.py — generates a single vocabulary video.
Called by server.py via subprocess.

Usage:
python3 video_worker.py <english> <translated> <transliteration>
                        <image_url> <output_file> <font_file> [latin_font] [add_logo]
"""

import sys
import os
import traceback
import requests
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS

FONT_CACHE = {}
print("VIDEO WORKER STARTED", flush=True)

def get_font(font_file, size):
    key = (font_file, size)

    if key not in FONT_CACHE:
        path = os.path.join("fonts", font_file)

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Font not found: {path}\n"
                "Please make sure this file is in your fonts/ folder."
            )

        FONT_CACHE[key] = ImageFont.truetype(path, size)

    return FONT_CACHE[key]


def make_video(
    english_word,
    translated_word,
    transliteration,
    image_url,
    output_file,
    font_file,
    latin_font="NotoSans-Regular.ttf",
    add_logo=False
):
    print(f"[1/4] Downloading image...")
    resp = requests.get(
        image_url,
        timeout=15,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    resp.raise_for_status()
    print(f"      Image size: {len(resp.content)} bytes")

    tmp_img = f"image_tmp_{os.getpid()}.jpg"
    with open(tmp_img, "wb") as f:
        f.write(resp.content)

    print(f"[2/4] Building frame...")

    img = Image.open(tmp_img)
    print(f"      Original size: {img.size}, mode: {img.mode}")
    base = img.convert("RGB").resize((854, 480))

    # overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    # bar     = Image.new("RGBA", (1280, 180), (0, 0, 0, 100))  # 👈 lighter
    # overlay.paste(bar, (0, 540))  # 👈 adjusted position

  
    # base = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(base)

    # fonts
    font_native = get_font(font_file, 66)
    font_roman = get_font(latin_font, 40)
    font_eng = get_font(latin_font, 48)
    
    # Draw English word + dash
    top_text = f"{english_word.upper()} -"

    draw.text(
        (40, 30),
        top_text,
        font=font_eng,
        fill="white",
        stroke_width=2,
        stroke_fill="black"
    )

    # Calculate width of English text
    bbox = draw.textbbox((40, 30), top_text, font=font_eng)
    text_width = bbox[2] - bbox[0]

    # Draw translated word right next to it
    draw.text(
        (40 + text_width + 10, 30),   # 👈 spacing after English
        translated_word,
        font=font_native,
        fill="white",
        stroke_width=2,
        stroke_fill="black"
    )
    

    # # Transliteration
    # if transliteration:
    #     draw.text(
    #         (40, 600),
    #         transliteration,
    #         font=font_roman,
    #         fill="#ffe066",
    #         stroke_width=1,
    #         stroke_fill="black"
    #     )
    
    # ===== DISCLAIMER TEXT =====
    disclaimer_text = "© Learning Matters | Images: Unsplash | Educational Use Only"

    font_disclaimer = get_font(latin_font, 22)

    # get text size for centering
    bbox = draw.textbbox((0, 0), disclaimer_text, font=font_disclaimer)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # centered horizontally, near bottom
    x_position = (854 - text_width) // 2
    video_height = 480
    y_position = video_height - text_height - 10
    

    draw.text(
        (x_position, y_position),
        disclaimer_text,
        font=font_disclaimer,
        fill="white",          # soft grey (subtle)
        stroke_width=1,
        stroke_fill="black"      # improves readability
    )

    tmp_frame = f"frame_tmp_{os.getpid()}.jpg"
    base.save(tmp_frame, quality=75)
    os.remove(tmp_img)
    print("      Frame saved.")

    print(f"[3/4] Generating audio...")
    tmp_audio = f"voice_tmp_{os.getpid()}.mp3"

    tts = gTTS(
        text=f"{english_word}. {english_word}. {english_word}.",
        lang="en",
        # for indian accent
        tld="co.in"
    )
    tts.save(tmp_audio)
    print("      Audio saved.")

    print(f"[4/4] Encoding video...")
    from moviepy import ImageClip, AudioFileClip, CompositeAudioClip, AudioClip
    
    speech = AudioFileClip(tmp_audio)

    # slow down speech
    speech = speech.with_speed_scaled(0.85)
    # speech = speech.fx(lambda clip: clip.with_speed_scaled(0.7))
    # speech = speech.with_speed_scaled(0.7)

    silence = AudioClip(lambda t: 0, duration=3)

  

    # speech = AudioFileClip(tmp_audio)
    # silence = AudioClip(lambda t: 0, duration=5)
    final_audio = CompositeAudioClip([silence, speech.with_start(3)])
    total_duration = 3 + speech.duration

    clip = ImageClip(tmp_frame).with_duration(total_duration)

    # ✅ LOGO OVERLAY
    if add_logo:
        from moviepy import ImageClip as MPImageClip, CompositeVideoClip

        logo = MPImageClip("logo.png") \
            .with_duration(clip.duration) \
            .resized(height=50) \
            .with_position(("right", "top"))

        clip = CompositeVideoClip([clip, logo])

    clip = clip.with_audio(final_audio)

    clip.write_videofile(
        output_file,
        fps=15,
        codec="libx264",
        audio_codec="aac",
        bitrate="800k",
        preset="ultrafast",
        logger="bar"
    )
    final_audio.close()

    speech.close()
    clip.close()

    for f in (tmp_audio, tmp_frame):
        try:
            os.remove(f)
        except OSError:
            pass

    print(f"      Video saved: {output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 7:
        print("Usage: app.py <english> <translated> <transliteration> "
              "<image_url> <output_file> <font_file> [latin_font] [add_logo]")
        sys.exit(1)

    try:
        add_logo = False
        if len(sys.argv) > 8:
            add_logo = sys.argv[8].lower() == "true"

        make_video(
            english_word=sys.argv[1],
            translated_word=sys.argv[2],
            transliteration=sys.argv[3],
            image_url=sys.argv[4],
            output_file=sys.argv[5],
            font_file=sys.argv[6],
            latin_font=sys.argv[7] if len(sys.argv) > 7 else "NotoSans-Regular.ttf",
            add_logo=add_logo
        )

        print("SUCCESS")

    except Exception:
        print("VIDEO WORKER CRASHED:")
        traceback.print_exc()
        sys.exit(1)