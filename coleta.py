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
    if "@” in link:
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
