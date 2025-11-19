# faceless_youtube_factory.py - LUXURY EDITION NO EMOJIS (Clean CMD Output)
# Big bold drop shadow captions + cinematic visuals + rich progress bars (no Unicode issues)

import os
import random
import requests
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn
from rich.console import Console
from PIL import Image as PILImage
from moviepy.editor import *
PILImage.ANTIALIAS = PILImage.LANCZOS

from moviepy.video.tools.subtitles import SubtitlesClip
from proglog import ProgressBarLogger
from groq import Groq
import edge_tts
import asyncio
from dotenv import load_dotenv

load_dotenv()
console = Console()

class RichProgressLogger(ProgressBarLogger):
    def __init__(self, progress, task):
        super().__init__()
        self.progress = progress
        self.task = task

    def callback(self, **changes):
        if 'index' in changes and 'total' in changes:
            bar = changes['index'] / changes['total']
            self.progress.update(self.task, completed=bar * 100)

# ========================= CONFIG =========================
NICHES = "Luxury Dark Retreats and High-End Sensory Deprivation Experiences"
EDGE_VOICE = "en-US-AndrewNeural"

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
os.makedirs("videos", exist_ok=True)
os.makedirs("temp_stock", exist_ok=True)

# =========================================================
async def edge_tts_save(text, filename):
    communicate = edge_tts.Communicate(text, EDGE_VOICE)
    await communicate.save(filename)

def text_to_speech(text, filename):
    console.log(f"Generating voice -> {filename}")
    asyncio.run(edge_tts_save(text, filename))

def generate_content():
    prompt = f"""Write viral faceless YouTube content about: {NICHES}

Output exactly:

LONG_SCRIPT:
[1200-1600 word calm mysterious script]

SHORT_1:
[50-90 sec hook]

SHORT_2:
[50-90 sec hook]

SHORT_3:
[50-90 sec hook]
"""
    with Progress() as progress:
        task = progress.add_task("Generating scripts with Groq...", total=1)
        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}], temperature=0.85, max_tokens=4096)
        progress.update(task, advance=1)
    text = response.choices[0].message.content
    parts = text.split("SHORT_")
    long = parts[0].split("LONG_SCRIPT:")[1].strip() if "LONG_SCRIPT:" in text else text[:4000]
    shorts = [p.strip().lstrip("123:. ") for p in parts[1:4]]
    return long, shorts

def download_stock(query):
    try:
        url = f"https://pixabay.com/api/videos/?key=25540889-f8c8e4f9d8e8b8b8b8b8b8b8b&q={query}+cinematic+dark+mystery+luxury&per_page=5"
        data = requests.get(url, timeout=15).json()
        links = [hit['videos']['large']['url'] for hit in data.get('hits', [])[:5]]
        paths = []
        for i, link in enumerate(links):
            path = f"temp_stock/cinematic_{i}.mp4"
            if not os.path.exists(path):
                with Progress(
                    TextColumn("{task.description}"),
                    BarColumn(),
                    TransferSpeedColumn(),
                    TimeRemainingColumn(),
                ) as progress:
                    task = progress.add_task(f"Downloading stock {i+1}/5...", total=None)
                    r = requests.get(link, stream=True, timeout=30)
                    with open(path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1024*1024):
                            f.write(chunk)
                            progress.update(task, advance=len(chunk))
            paths.append(path)
        return paths
    except:
        return None

def create_video(script, audio_file, output_name, is_short=False):
    audio = AudioFileClip(audio_file)
    duration = min(audio.duration, 60 if is_short else 900)
    size = (1080, 1920) if is_short else (1920, 1080)

    sentences = [s.strip() + "." for s in script.replace("\n"," ").split(".") if s.strip()][:12 if is_short else 30]
    seg = duration / len(sentences)

    clips = []
    console.log(f"Building {len(sentences)} clips for {output_name}...")

    for sentence in sentences:
        stock = download_stock(sentence[:60])
        if stock and os.path.exists(stock[0]):
            clip = VideoFileClip(random.choice(stock)).subclip(0, seg)
        else:
            clip = ColorClip(size=size, color=(5,5,15), duration=seg)

        clip = clip.resize(width=size[0]*1.2)
        clip = clip.fx(vfx.resize, lambda t: 1 + 0.05*t/seg)
        clip = clip.crop(x_center=clip.w/2, y_center=clip.h/2, width=size[0], height=size[1])
        clips.append(clip.set_fps(30))

    video = concatenate_videoclips(clips, method="compose").set_audio(audio.subclip(0, duration)).set_duration(duration)

    def make_txt(txt):
        main = TextClip(txt.upper()[:120], fontsize=90 if is_short else 100, color='white', font='Impact', kerning=-3, stroke_width=8, stroke_color='black')
        shadow = TextClip(txt.upper()[:120], fontsize=90 if is_short else 100, color='#00000088', font='Impact', kerning=-3).set_position((8,8))
        caption = CompositeVideoClip([shadow, main]).set_duration(seg).set_position(('center', 'bottom')).margin(bottom=100 if is_short else 140)
        return caption

    subtitles_data = [((i*seg, (i+1)*seg), s) for i, s in enumerate(sentences)]
    subs = SubtitlesClip(subtitles_data, make_txt)

    final = CompositeVideoClip([video, subs]).set_fps(30)

    with Progress(
        TextColumn("Rendering {task.description}"),
        BarColumn(),
        TimeRemainingColumn(),
        "{task.percentage:>3.0f}%",
    ) as progress:
        task = progress.add_task(output_name, total=100)
        logger = RichProgressLogger(progress, task)
        final.write_videofile(f"videos/{output_name}", fps=30, threads=8, preset="ultrafast", logger=logger)
    
    final.close(); audio.close()
    console.log(f"{output_name} DONE")

# ========================= MAIN =========================
if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    console.print("VOID SANCTUARY LUXURY BATCH STARTING - NO EMOJIS EDITION")
    long_script, shorts = generate_content()

    text_to_speech(long_script, "long_audio.mp3")
    create_video(long_script, "long_audio.mp3", "LONG_TODAY.mp4", is_short=False)

    for i, short in enumerate(shorts, 1):
        text_to_speech(short, f"short_{i}_audio.mp3")
        create_video(short, f"short_{i}_audio.mp3", f"SHORT_{i}_TODAY.mp4", is_short=True)

    console.print("ALL VIDEOS DONE - CHECK 'videos' FOLDER - VOID SANCTUARY READY")