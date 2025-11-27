import os
import re
import time
import requests
import pandas as pd
from typing import List, Dict, Optional

# ============================================================
#   CARREGAR A API KEY CORRETAMENTE (STREAMLIT CLOUD)
# ============================================================
try:
    import streamlit as st
    YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]
except:
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

DEFAULT_MAX_VIDEOS = int(os.getenv("MAX_VIDEOS", 5))


# ============================================================
#   Função completa para extrair canal de QUALQUER LINK
# ============================================================
def extrair_channel_id(link: str) -> str:
    """
    Aceita:
      - link de vídeo: https://youtube.com/watch?v=ID
      - link de canal: https://youtube.com/channel/ID
      - link @handle: https://youtube.com/@nome
      - link /user/
      - link /c/
      - ID direto começando por UC
    """
    link = link.strip()

    # Caso o usuário insira diretamente o ID do canal
    if re.fullmatch(r"UC[\w-]{20,}", link):
        return link

    # Vídeo
    if "watch?v=" in link:
        video_id = link.split("watch?v=")[1].split("&")[0]
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={YOUTUBE_API_KEY}"
        resp = requests.get(url).json()
        return resp["items"][0]["snippet"]["channelId"]

    # Handle @nome
    if "/@" in link or link.startswith("@"):
        handle = link.split("@")[1].split("/")[0]
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={handle}&key={YOUTUBE_API_KEY}"
        resp = requests.get(url).json()
        return resp["items"][0]["snippet"]["channelId"]

    # /c/ personalizado
    if "/c/" in link:
        custom = link.split("/c/")[1].split("/")[0]
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={custom}&key={YOUTUBE_API_KEY}"
        resp = requests.get(url).json()
        return resp["items"][0]["snippet"]["channelId"]

    # /user/
    if "/user/" in link:
        user = link.split("/user/")[1].split("/")[0]
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={user}&key={YOUTUBE_API_KEY}"
        resp = requests.get(url).json()
        return resp["items"][0]["snippet"]["channelId"]

    # /channel/
    if "/channel/" in link:
        return link.split("/channel/")[1].split("/")[0]

    raise ValueError("Não consegui identificar o canal a partir do link informado.")


# ============================================================
#   Lista vídeos recentes do canal
# ============================================================
def listar_videos_canal(channel_id: str, max_videos: int = DEFAULT_MAX_VIDEOS) -> List[Dict]:

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": YOUTUBE_API_KEY,
        "channelId": channel_id,
        "part": "snippet",
        "order": "date",
        "maxResults": max_videos,
        "type": "video",
    }

    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        raise RuntimeError(f"Erro ao listar vídeos: {resp.status_code} - {resp.text}")

    data = resp.json()

    return [
        {
            "video_id": item["id"]["videoId"],
            "video_title": item["snippet"]["title"],
            "video_published_at": item["snippet"]["publishedAt"]
        }
        for item in data.get("items", [])
    ]


# ============================================================
#   Coleta comentários de UM vídeo
# ============================================================
def coletar_comentarios_video(video_id: str, max_comments: int = 200) -> List[Dict]:

    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "key": YOUTUBE_API_KEY,
        "part": "snippet",
        "videoId": video_id,
        "maxResults": 100,
        "textFormat": "plainText",
        "order": "relevance",
    }

    comentarios = []
    total = 0
    page_token: Optional[str] = None

    while True:
        if page_token:
            params["pageToken"] = page_token

        resp = requests.get(url, params=params)
        data = resp.json()

        if resp.status_code != 200:
            print(f"Erro ao coletar comentários do vídeo {video_id}: {resp.text}")
            break

        for item in data.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]

            comentarios.append({
                "video_id": video_id,
                "author": snippet.get("authorDisplayName", ""),
                "comment": snippet.get("textDisplay", ""),
                "like_count": snippet.get("likeCount", 0),
                "published_at": snippet.get("publishedAt", "")
            })

            total += 1
            if total >= max_comments:
                return comentarios

        page_token = data.get("nextPageToken")
        if not page_token:
            break

        time.sleep(0.3)

    return comentarios


# ============================================================
#   Coleta comentários de TODOS vídeos
# ============================================================
def coletar_comentarios_canal(canal_input: str,
                              max_videos: int = DEFAULT_MAX_VIDEOS,
                              max_comments_por_video: int = 200) -> pd.DataFrame:

    channel_id = extrair_channel_id(canal_input)
    videos = listar_videos_canal(channel_id, max_videos=max_videos)

    all_comments = []
    for v in videos:
        vid = v["video_id"]
        comments = coletar_comentarios_video(vid, max_comments_por_video)
        all_comments.extend(comments)

    return pd.DataFrame(all_comments)
