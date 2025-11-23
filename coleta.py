import os
import re
import time
import requests
import pandas as pd
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
DEFAULT_MAX_VIDEOS = int(os.getenv("MAX_VIDEOS", 5))


# ============================================================
#   Função para extrair channel_id de uma URL ou ID direto
# ============================================================
def extrair_channel_id(canal_input: str) -> str:
    """
    Recebe um ID de canal ou URL e devolve o channel_id.
    Aceita:
      - https://www.youtube.com/channel/ID
      - ID direto
    """
    canal_input = canal_input.strip()

    # Se NÃO contém youtube.com, assume ser o ID
    if "youtube.com" not in canal_input:
        return canal_input

    # Extrai do padrão /channel/ID
    match = re.search(r"youtube\.com/channel/([^/?]+)", canal_input)
    if match:
        return match.group(1)

    raise ValueError(
        "⚠ Não consegui extrair channel_id da URL.\n"
        "Use uma URL do tipo: https://www.youtube.com/channel/ID ou informe o ID diretamente."
    )


# ============================================================
#   Lista os vídeos recentes de um canal
# ============================================================
def listar_videos_canal(channel_id: str, max_videos: int = DEFAULT_MAX_VIDEOS) -> List[Dict]:
    """
    Lista os últimos vídeos do canal usando o endpoint 'search'.
    """
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY não encontrada no .env.")

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
    items = data.get("items", [])

    videos = []
    for item in items:
        videos.append({
            "video_id": item["id"]["videoId"],
            "video_title": item["snippet"]["title"],
            "video_published_at": item["snippet"]["publishedAt"],
        })

    return videos


# ============================================================
#   Coleta comentários de UM vídeo
# ============================================================
def coletar_comentarios_video(video_id: str, max_comments: int = 200) -> List[Dict]:
    """
    Coleta até 'max_comments' comentários de um vídeo.
    Usa o endpoint 'commentThreads'.
    """

    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY não encontrada no .env.")

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
        if resp.status_code != 200:
            print(f"Erro ao coletar comentários do vídeo {video_id}: {resp.text}")
            break

        data = resp.json()
        items = data.get("items", [])

        for item in items:
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comentarios.append({
                "video_id": video_id,
                "author": snippet.get("authorDisplayName", ""),
                "comment": snippet.get("textDisplay", ""),
                "like_count": snippet.get("likeCount", 0),
                "published_at": snippet.get("publishedAt", ""),
            })

            total += 1
            if total >= max_comments:
                return comentarios

        # Verifica próxima página
        page_token = data.get("nextPageToken")
        if not page_token:
            break

        time.sleep(0.3)  # evita limite da API

    return comentarios


# ============================================================
#   Coleta comentários de TODOS vídeos do canal
# ============================================================
def coletar_comentarios_canal(canal_input: str,
                              max_videos: int = DEFAULT_MAX_VIDEOS,
                              max_comments_por_video: int = 200) -> pd.DataFrame:
    """
    Recebe uma URL/ID de canal e retorna DataFrame com TODOS os comentários.
    """
    channel_id = extrair_channel_id(canal_input)
    videos = listar_videos_canal(channel_id, max_videos=max_videos)

    all_comments = []
    for video in videos:
        vid = video["video_id"]
        comments = coletar_comentarios_video(vid, max_comments=max_comments_por_video)
        all_comments.extend(comments)

    return pd.DataFrame(all_comments)
