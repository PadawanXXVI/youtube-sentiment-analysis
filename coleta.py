import os
import re
import time
import requests
import pandas as pd
from typing import List, Dict, Optional

# ============================================================
#   Carregar a API Key
# ============================================================
try:
    import streamlit as st
    YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]
except:
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


# ============================================================
#   Extrair VIDEO ID
# ============================================================
def extrair_video_id(link: str) -> Optional[str]:
    """
    Extrai o ID do vídeo de várias formas:
    - https://youtube.com/watch?v=ID
    - https://youtu.be/ID
    - Shorts
    """
    link = link.strip()

    # watch?v=
    if "watch?v=" in link:
        return link.split("watch?v=")[1].split("&")[0]

    # youtu.be/xxxx
    if "youtu.be/" in link:
        return link.split("youtu.be/")[1].split("?")[0]

    # shorts
    if "/shorts/" in link:
        return link.split("/shorts/")[1].split("?")[0]

    return None


# ============================================================
#   Extrair CHANNEL ID de QUALQUER LINK
# ============================================================
def extrair_channel_id(link: str) -> str:
    link = link.strip()

    # ID direto UCxxxx
    if re.fullmatch(r"UC[\w-]{20,}", link):
        return link

    # Link de vídeo → pegar canal real
    video_id = extrair_video_id(link)
    if video_id:
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={YOUTUBE_API_KEY}"
        resp = requests.get(url).json()
        return resp["items"][0]["snippet"]["channelId"]

    # @handle
    if "@" in link:
        handle = link.split("@")[1].split("/")[0]
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={handle}&key={YOUTUBE_API_KEY}"
        return requests.get(url).json()["items"][0]["snippet"]["channelId"]

    # /channel/
    if "/channel/" in link:
        return link.split("/channel/")[1].split("/")[0]

    # /user/ ou /c/ (canal personalizado)
    if "/user/" in link:
        user = link.split("/user/")[1].split("/")[0]
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={user}&key={YOUTUBE_API_KEY}"
        return requests.get(url).json()["items"][0]["snippet"]["channelId"]

    if "/c/" in link:
        custom = link.split("/c/")[1].split("/")[0]
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={custom}&key={YOUTUBE_API_KEY}"
        return requests.get(url).json()["items"][0]["snippet"]["channelId"]

    raise ValueError("Não foi possível identificar o canal.")

# ============================================================
#   LISTAR VÍDEOS RECENTES
# ============================================================
def listar_videos_recentes(channel_id: str, max_videos: int) -> List[Dict]:
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": YOUTUBE_API_KEY,
        "channelId": channel_id,
        "part": "snippet",
        "order": "date",
        "maxResults": max_videos,
        "type": "video",
    }

    data = requests.get(url, params=params).json()
    return [
        {
            "video_id": item["id"]["videoId"],
            "video_title": item["snippet"]["title"],
            "video_published_at": item["snippet"]["publishedAt"],
        }
        for item in data.get("items", [])
    ]

# ============================================================
#   LISTAR MAIS VISTOS
# ============================================================
def listar_videos_mais_vistos(channel_id: str, max_videos: int) -> List[Dict]:
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": YOUTUBE_API_KEY,
        "channelId": channel_id,
        "part": "snippet",
        "order": "viewCount",
        "maxResults": max_videos,
        "type": "video",
    }

    data = requests.get(url, params=params).json()
    return [
        {
            "video_id": item["id"]["videoId"],
            "video_title": item["snippet"]["title"],
            "video_published_at": item["snippet"]["publishedAt"],
        }
        for item in data.get("items", [])
    ]

# ============================================================
#   LISTAR MAIS COMENTADOS (manual)
# ============================================================
def listar_videos_mais_comentados(channel_id: str, max_videos: int) -> List[Dict]:

    # Primeiro pega muitos vídeos
    recentes = listar_videos_recentes(channel_id, max_videos=20)

    # Agora pega estatísticas
    ids = ",".join([v["video_id"] for v in recentes])
    url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={ids}&key={YOUTUBE_API_KEY}"
    stats = requests.get(url).json()["items"]

    # Faz join
    for v in recentes:
        st = next((x for x in stats if x["id"] == v["video_id"]), None)
        v["commentCount"] = int(st["statistics"].get("commentCount", 0))

    # Ordenar desc
    recentes.sort(key=lambda x: x["commentCount"], reverse=True)

    return recentes[:max_videos]

# ============================================================
#   COLETAR COMENTÁRIOS
# ============================================================
def coletar_comentarios_video(video_id: str, max_comments: int = 200):

    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "key": YOUTUBE_API_KEY,
        "part": "snippet",
        "videoId": video_id,
        "maxResults": 100,
        "textFormat": "plainText",
    }

    comentarios = []
    page_token = None

    while True:
        if page_token:
            params["pageToken"] = page_token

        data = requests.get(url, params=params).json()

        for item in data.get("items", []):
            s = item["snippet"]["topLevelComment"]["snippet"]
            comentarios.append(
                {
                    "video_id": video_id,
                    "author": s.get("authorDisplayName", ""),
                    "comment": s.get("textDisplay", ""),
                    "like_count": s.get("likeCount", 0),
                    "published_at": s.get("publishedAt", ""),
                }
            )

            if len(comentarios) >= max_comments:
                return comentarios

        page_token = data.get("nextPageToken")
        if not page_token:
            break

        time.sleep(0.3)

    return comentarios
