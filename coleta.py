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


# ============================================================
#   EXTRAI VIDEO ID — SE FOR LINK DE VÍDEO
# ============================================================
def extrair_video_id(link: str) -> Optional[str]:
    """
    Retorna o video_id se o link contiver watch?v=
    """
    if "watch?v=" in link:
        return link.split("watch?v=")[1].split("&")[0]
    return None


# ============================================================
#   EXTRAI CHANNEL ID — SUPORTA QUALQUER TIPO DE LINK
# ============================================================
def extrair_channel_id(link: str) -> str:
    link = link.strip()

    # ID direto
    if re.fullmatch(r"UC[\w-]{20,}", link):
        return link

    # Vídeo → descobrir canal
    if "watch?v=" in link:
        video_id = extrair_video_id(link)
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={YOUTUBE_API_KEY}"
        resp = requests.get(url).json()
        return resp["items"][0]["snippet"]["channelId"]

    # Handle @
    if "/@" in link or link.startswith("@"):
        handle = link.split("@")[1].split("/")[0]
        search_url = (
            "https://www.googleapis.com/youtube/v3/search?"
            f"part=snippet&type=channel&q={handle}&key={YOUTUBE_API_KEY}"
        )
        resp = requests.get(search_url).json()
        return resp["items"][0]["snippet"]["channelId"]

    # /c/
    if "/c/" in link:
        custom = link.split("/c/")[1].split("/")[0]
        search_url = (
            "https://www.googleapis.com/youtube/v3/search?"
            f"part=snippet&type=channel&q={custom}&key={YOUTUBE_API_KEY}"
        )
        resp = requests.get(search_url).json()
        return resp["items"][0]["snippet"]["channelId"]

    # /user/
    if "/user/" in link:
        user = link.split("/user/")[1].split("/")[0]
        search_url = (
            "https://www.googleapis.com/youtube/v3/search?"
            f"part=snippet&type=channel&q={user}&key={YOUTUBE_API_KEY}"
        )
        resp = requests.get(search_url).json()
        return resp["items"][0]["snippet"]["channelId"]

    # /channel/
    if "/channel/" in link:
        return link.split("/channel/")[1].split("/")[0]

    raise ValueError("Não foi possível identificar o canal a partir do link informado.")
    


# ============================================================
#   LISTAR VÍDEOS — MODOS COMERCIAIS
# ============================================================

# ---- MODO PADRÃO: Mais recentes ----
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

    resp = requests.get(url, params=params)
    data = resp.json()
    return [
        {
            "video_id": item["id"]["videoId"],
            "video_title": item["snippet"]["title"],
            "video_published_at": item["snippet"]["publishedAt"]
        }
        for item in data.get("items", [])
    ]


# ---- MODO: Mais vistos ----
def listar_videos_mais_vistos(channel_id: str, max_videos: int) -> List[Dict]:

    # Passo 1: pegar vídeos via search
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": YOUTUBE_API_KEY,
        "channelId": channel_id,
        "part": "snippet",
        "order": "date",
        "maxResults": 50,   # buscar mais vídeos para melhor ranking
        "type": "video",
    }
    resp = requests.get(url, params=params).json()

    ids = [item["id"]["videoId"] for item in resp.get("items", [])]

    # Passo 2: pegar estatísticas reais
    stats_url = (
        "https://www.googleapis.com/youtube/v3/videos?"
        f"part=statistics,snippet&id={','.join(ids)}&key={YOUTUBE_API_KEY}"
    )
    stats = requests.get(stats_url).json()

    videos = []
    for item in stats.get("items", []):
        videos.append({
            "video_id": item["id"],
            "video_title": item["snippet"]["title"],
            "viewCount": int(item["statistics"].get("viewCount", 0)),
            "commentCount": int(item["statistics"].get("commentCount", 0)),
        })

    # Ordenar por visualizações
    videos_sorted = sorted(videos, key=lambda x: x["viewCount"], reverse=True)
    return videos_sorted[:max_videos]


# ---- MODO: Mais comentados ----
def listar_videos_mais_comentados(channel_id: str, max_videos: int) -> List[Dict]:

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": YOUTUBE_API_KEY,
        "channelId": channel_id,
        "part": "snippet",
        "order": "date",
        "maxResults": 50,
        "type": "video",
    }
    resp = requests.get(url, params=params).json()

    ids = [item["id"]["videoId"] for item in resp.get("items", [])]

    stats_url = (
        "https://www.googleapis.com/youtube/v3/videos?"
        f"part=statistics,snippet&id={','.join(ids)}&key={YOUTUBE_API_KEY}"
    )
    stats = requests.get(stats_url).json()

    videos = []
    for item in stats.get("items", []):
        videos.append({
            "video_id": item["id"],
            "video_title": item["snippet"]["title"],
            "commentCount": int(item["statistics"].get("commentCount", 0)),
        })

    videos_sorted = sorted(videos, key=lambda x: x["commentCount"], reverse=True)
    return videos_sorted[:max_videos]



# ============================================================
#   COLETAR COMENTÁRIOS DE UM VÍDEO
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
