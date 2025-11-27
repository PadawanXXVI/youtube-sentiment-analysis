import os
import re
import time
import requests
import pandas as pd
from typing import List, Dict, Optional

# Tenta pegar a API Key do Streamlit Cloud; se não houver, usa variável de ambiente
try:
    import streamlit as st  # type: ignore
    YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]
except Exception:
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

if not YOUTUBE_API_KEY:
    # Não levantamos erro aqui para permitir import do módulo;
    # o app fará a validação e mostrará mensagem amigável.
    print("⚠ YOUTUBE_API_KEY não encontrada. Configure em st.secrets ou variável de ambiente.")


# ============================================================
#   EXTRATORES DE ID
# ============================================================
def extrair_video_id(link: str) -> Optional[str]:
    """
    Extrai o ID de vídeo de vários formatos de link do YouTube.
    Aceita:
      - https://www.youtube.com/watch?v=ID
      - https://youtu.be/ID
      - https://www.youtube.com/shorts/ID
    """
    link = link.strip()

    if "watch?v=" in link:
        return link.split("watch?v=")[1].split("&")[0]

    if "youtu.be/" in link:
        return link.split("youtu.be/")[1].split("?")[0]

    if "/shorts/" in link:
        return link.split("/shorts/")[1].split("?")[0]

    return None


def extrair_channel_id(link_ou_id: str) -> str:
    """
    Recebe um ID de canal (UC...) ou QUALQUER link do YouTube e devolve o channel_id.
    Aceita:
      - ID direto: UCxxxxxxxxxxxxxxxxxxxx
      - Link de vídeo: https://www.youtube.com/watch?v=...
      - Link encurtado: https://youtu.be/...
      - Shorts: https://www.youtube.com/shorts/...
      - /channel/ID
      - /user/NOME
      - /c/NOME
      - /@handle
    """
    texto = link_ou_id.strip()

    # Se já parece um ID de canal, retorna direto
    if re.fullmatch(r"UC[\w-]{20,}", texto):
        return texto

    # Se for link de vídeo, usa API de vídeos para descobrir o canal
    video_id = extrair_video_id(texto)
    if video_id:
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "key": YOUTUBE_API_KEY,
            "part": "snippet",
            "id": video_id,
        }
        resp = requests.get(url, params=params)
        data = resp.json()
        items = data.get("items", [])
        if not items:
            raise ValueError("Não foi possível obter informações do vídeo para descobrir o canal.")
        return items[0]["snippet"]["channelId"]

    # Handle @nome
    if "youtube.com/@" in texto or texto.startswith("@"):
        handle = texto.split("@")[1].split("/")[0]
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "key": YOUTUBE_API_KEY,
            "part": "snippet",
            "type": "channel",
            "q": handle,
            "maxResults": 1,
        }
        resp = requests.get(url, params=params)
        data = resp.json()
        items = data.get("items", [])
        if not items:
            raise ValueError("Não foi possível encontrar canal a partir do handle informado.")
        return items[0]["snippet"]["channelId"]

    # /channel/ID
    if "/channel/" in texto:
        return texto.split("/channel/")[1].split("/")[0]

    # /user/ ou /c/ -> buscar via search
    termo = None
    if "/user/" in texto:
        termo = texto.split("/user/")[1].split("/")[0]
    elif "/c/" in texto:
        termo = texto.split("/c/")[1].split("/")[0]

    if termo:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "key": YOUTUBE_API_KEY,
            "part": "snippet",
            "type": "channel",
            "q": termo,
            "maxResults": 1,
        }
        resp = requests.get(url, params=params)
        data = resp.json()
        items = data.get("items", [])
        if not items:
            raise ValueError("Não foi possível encontrar canal a partir da URL informada.")
        return items[0]["snippet"]["channelId"]

    raise ValueError("Não foi possível identificar o canal a partir do texto informado.")


# ============================================================
#   LISTAGEM DE VÍDEOS DO CANAL
# ============================================================
def _listar_videos(channel_id: str, max_videos: int, order: str) -> List[Dict]:
    """
    Função interna que lista vídeos de um canal usando diferentes ordenações.
    order pode ser: 'date', 'viewCount', 'relevance'
    """
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY não configurada.")

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": YOUTUBE_API_KEY,
        "channelId": channel_id,
        "part": "snippet",
        "order": order,
        "maxResults": max_videos,
        "type": "video",
    }
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        raise RuntimeError(f"Erro ao listar vídeos: {resp.status_code} - {resp.text}")

    data = resp.json()
    videos = []
    for item in data.get("items", []):
        videos.append(
            {
                "video_id": item["id"]["videoId"],
                "video_title": item["snippet"]["title"],
                "video_published_at": item["snippet"]["publishedAt"],
            }
        )
    return videos


def listar_videos_recentes(channel_id: str, max_videos: int) -> List[Dict]:
    return _listar_videos(channel_id, max_videos, order="date")


def listar_videos_mais_vistos(channel_id: str, max_videos: int) -> List[Dict]:
    # 'viewCount' só funciona em algumas combinações; se der erro, recai para recentes
    try:
        return _listar_videos(channel_id, max_videos, order="viewCount")
    except Exception:
        return _listar_videos(channel_id, max_videos, order="date")


def listar_videos_mais_comentados(channel_id: str, max_videos: int) -> List[Dict]:
    """
    A API não ordena direto por comentários.
    Estratégia:
      1) pega até 20 vídeos recentes
      2) consulta estatísticas
      3) ordena por commentCount
      4) devolve os top max_videos
    """
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY não configurada.")

    base = _listar_videos(channel_id, max_videos=20, order="date")
    if not base:
        return []

    ids = ",".join(v["video_id"] for v in base)
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "key": YOUTUBE_API_KEY,
        "part": "statistics",
        "id": ids,
    }
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        return base  # fallback

    stats = {item["id"]: item["statistics"] for item in resp.json().get("items", [])}

    for v in base:
        stt = stats.get(v["video_id"], {})
        v["commentCount"] = int(stt.get("commentCount", 0))

    base.sort(key=lambda x: x.get("commentCount", 0), reverse=True)
    return base[:max_videos]


# ============================================================
#   COLETA DE COMENTÁRIOS
# ============================================================
def coletar_comentarios_video(video_id: str, max_comments: int = 200) -> List[Dict]:
    """
    Coleta até 'max_comments' comentários de um vídeo usando commentThreads.
    """
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY não configurada.")

    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "key": YOUTUBE_API_KEY,
        "part": "snippet",
        "videoId": video_id,
        "maxResults": 100,
        "textFormat": "plainText",
        "order": "relevance",
    }

    comentarios: List[Dict] = []
    page_token: Optional[str] = None

    while True:
        if page_token:
            params["pageToken"] = page_token

        resp = requests.get(url, params=params)
        if resp.status_code != 200:
            print(f"Erro ao coletar comentários do vídeo {video_id}: {resp.text}")
            break

        data = resp.json()
        for item in data.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comentarios.append(
                {
                    "video_id": video_id,
                    "author": snippet.get("authorDisplayName", ""),
                    "comment": snippet.get("textDisplay", ""),
                    "like_count": snippet.get("likeCount", 0),
                    "published_at": snippet.get("publishedAt", ""),
                }
            )
            if len(comentarios) >= max_comments:
                return comentarios

        page_token = data.get("nextPageToken")
        if not page_token:
            break

        time.sleep(0.3)

    return comentarios


def coletar_comentarios_multiplos_videos(videos: List[Dict], max_comments_por_video: int) -> pd.DataFrame:
    """
    Recebe uma lista de vídeos (dicts com 'video_id') e coleta comentários de todos.
    """
    all_comments: List[Dict] = []
    for v in videos:
        vid = v["video_id"]
        comments = coletar_comentarios_video(vid, max_comments=max_comments_por_video)
        all_comments.extend(comments)
    return pd.DataFrame(all_comments)
    
