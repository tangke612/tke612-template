#!/usr/bin/env python3
"""
subtitle_batch_openai_srt_tmdb_fixed.py
批量翻译 ~/Desktop/sub 文件夹内的英文字幕 (.srt)
自动识别文件名对应的电影或电视剧，从 TMDB 获取剧情简介，
并利用 OpenAI 翻译生成中英文双语字幕（上英文，下中文）。
"""

import os
import re
import requests
import warnings
from openai import OpenAI
from tqdm import tqdm

# === 忽略 urllib3 LibreSSL 警告 ===
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")

# === API 密钥配置 ===
OPENAI_API_KEY = "input your openai api key"
TMDB_API_KEY = "input your tmdb api"
MODEL = "gpt-4o-mini"

client = OpenAI(api_key=OPENAI_API_KEY)

# ================= 工具函数 =================

def clean_title(title):
    """清理文件名中的无关信息，仅保留剧名"""
    title = os.path.splitext(os.path.basename(title))[0]
    title = re.sub(r"\b(19|20)\d{2}\b", "", title)  # 去年份
    title = re.sub(r"[. _-]*(S\d{1,2}E\d{1,2}|Season\s*\d+|Ep\d+|Episode\s*\d+)", "", title, flags=re.I)
    title = re.sub(r"\b(1080p|720p|480p|2160p|x264|x265|WEB[-_. ]?DL|BluRay|HDR|HEVC|AAC|H264|H265|CHS|ENG|SUB|Dual|NF|AMZN|WEBRip)\b", "", title, flags=re.I)
    title = re.sub(r"[._]+", " ", title)
    return title.strip()


def get_movie_info_from_tmdb(title):
    """根据文件名从 TMDB 获取剧情简介"""
    title = clean_title(title)
    base_url = "https://api.themoviedb.org/3"
    headers = {"accept": "application/json"}

    # 搜索电影
    search_url = f"{base_url}/search/movie?api_key={TMDB_API_KEY}&query={title}"
    response = requests.get(search_url, headers=headers)
    data = response.json()
    if data.get("results"):
        movie = data["results"][0]
        movie_id = movie["id"]
        detail_url = f"{base_url}/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
        detail = requests.get(detail_url).json()
        return {"title": detail.get("title"), "overview": detail.get("overview"), "type": "movie"}

    # 若未找到，再尝试电视剧
    search_url = f"{base_url}/search/tv?api_key={TMDB_API_KEY}&query={title}"
    response = requests.get(search_url, headers=headers)
    data = response.json()
    if data.get("results"):
        tv = data["results"][0]
        tv_id = tv["id"]
        detail_url = f"{base_url}/tv/{tv_id}?api_key={TMDB_API_KEY}&language=en-US"
        detail = requests.get(detail_url).json()
        return {"title": detail.get("name"), "overview": detail.get("overview"), "type": "tv"}

    return None


def split_srt_blocks(srt_text):
    """按字幕块拆分"""
    return re.split(r'\n\s*\n', srt_text.strip())


def translate_lines_with_context(lines, context):
    """翻译一批字幕行，保持中英文严格一一对应"""
    numbered_text = "\n".join([f"{i+1}. {line}" for i, line in enumerate(lines)])
    prompt = (
        f"以下是影视作品的部分台词，背景简介：{context}\n"
        f"请将每一行分别翻译成中文，并严格保持与原行数一一对应。\n"
        f"每一行输出格式为：英文|||中文\n\n"
        f"{numbered_text}"
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.choices[0].message.content.strip()

    translated_pairs = []
    for line in text.splitlines():
        if "|||" in line:
            _, zh = line.split("|||", 1)
            translated_pairs.append(zh.strip())

    # 若模型返回的行数不足，补空行以保持对齐
    while len(translated_pairs) < len(lines):
        translated_pairs.append("")
    return translated_pairs


def process_srt_file(filepath):
    """处理单个字幕文件"""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    info = get_movie_info_from_tmdb(os.path.basename(filepath))
    context = info["overview"] if info else "无剧情简介"

    blocks = split_srt_blocks(content)
    parsed_blocks = []

    # 解析字幕块，提取编号、时间轴、文字
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) >= 2:
            index = lines[0].strip() if re.match(r"^\d+$", lines[0]) else None
            timecode = None
            text_lines = []
            for line in lines[1:]:
                if "-->" in line:
                    timecode = line.strip()
                else:
                    text_lines.append(line.strip())
            if text_lines and timecode:
                parsed_blocks.append({
                    "index": index,
                    "time": timecode,
                    "text": " ".join(text_lines)
                })

    # 批量翻译（每次 100 行）
    batch_size = 100
    translated_texts = []
    text_blocks = [b["text"] for b in parsed_blocks]

    for i in tqdm(range(0, len(text_blocks), batch_size), desc=os.path.basename(filepath)):
        batch = text_blocks[i:i + batch_size]
        translated_lines = translate_lines_with_context(batch, context)
        translated_texts.extend(translated_lines)

    # 生成中英文双语字幕，保留原时间轴
    out_path = os.path.splitext(filepath)[0] + "_zh.srt"
    with open(out_path, "w", encoding="utf-8") as f:
        for idx, block in enumerate(parsed_blocks):
            f.write(f"{idx+1}\n")
            f.write(f"{block['time']}\n")
            f.write(f"{block['text']}\n")
            if idx < len(translated_texts):
                f.write(f"{translated_texts[idx]}\n")
            f.write("\n")

    print(f"✅ 翻译完成: {out_path}")


def main():
    folder = os.path.expanduser("~/Desktop/sub")
    for filename in os.listdir(folder):
        if filename.lower().endswith((".srt", ".ass")):
            process_srt_file(os.path.join(folder, filename))


if __name__ == "__main__":
    main()