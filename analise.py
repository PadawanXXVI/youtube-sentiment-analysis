import re
import numpy as np
import pandas as pd
import string

# ============================================================
#   IMPORTAR VADER — carrega apenas 1 vez
# ============================================================
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    sia = SentimentIntensityAnalyzer()
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    sia = None

# ============================================================
#   IMPORTAR BERT — usando cache do Streamlit
# ============================================================
try:
    import streamlit as st
    from transformers import pipeline

    @st.cache_resource
    def carregar_modelo_bert():
        return pipeline(
            "sentiment-analysis",
            model="nlptown/bert-base-multilingual-uncased-sentiment"
        )

    BERT_AVAILABLE = True

except Exception:
    BERT_AVAILABLE = False
    carregar_modelo_bert = None


# ============================================================
#   PRÉ-PROCESSAMENTO E LIMPEZA
# ============================================================
def limpar_texto(texto: str) -> str:
    if pd.isna(texto):
        return "texto_vazio"

    t = str(texto)

    # Remove URLs
    t = re.sub(r"http\S+|www\.\S+", "", t)

    # Remove @ e #
    t = re.sub(r"[@#]\w+", "", t)

    # Remove números
    t = re.sub(r"\d+", "", t)

    # Remove pontuação
    t = t.translate(str.maketrans("", "", string.punctuation))

    # Normaliza espaços
    t = re.sub(r"\s+", " ", t).strip()

    if t == "":
        return "texto_limpo_vazio"

    return t.lower()


def preprocessar_textos(df: pd.DataFrame) -> pd.DataFrame:
    if "comment" not in df.columns:
        raise ValueError("A coluna 'comment' não existe no DataFrame.")

    df["texto_limpo"] = df["comment"].apply(limpar_texto)
    return df


# ============================================================
#   ANÁLISE DE SENTIMENTO – VADER
# ============================================================
def aplicar_vader(df: pd.DataFrame) -> pd.DataFrame:
    if not VADER_AVAILABLE:
        df["vader_compound"] = np.nan
        df["vader_label"] = "indefinido"
        return df

    df["vader_compound"] = df["texto_limpo"].apply(
        lambda t: sia.polarity_scores(t)["compound"]
    )

    def _classificar(comp):
        if pd.isna(comp):
            return "indefinido"
        if comp >= 0.05:
            return "positivo"
        elif comp <= -0.05:
            return "negativo"
        return "neutro"

    df["vader_label"] = df["vader_compound"].apply(_classificar)
    return df


# ============================================================
#   ANÁLISE DE SENTIMENTO – BERT
# ============================================================
def aplicar_bert(df: pd.DataFrame) -> pd.DataFrame:
    if not BERT_AVAILABLE:
        df["bert_label_raw"] = "indefinido"
        df["bert_estrelas"] = np.nan
        df["bert_label"] = "indefinido"
        return df

    clf = carregar_modelo_bert()

    textos = df["texto_limpo"].fillna("").tolist()
    resultados = clf(textos, truncation=True)

    df["bert_label_raw"] = [r["label"] for r in resultados]

    # extrair estrelas (1 a 5)
    estrelas = []
    for lab in df["bert_label_raw"]:
        nums = re.findall(r"\d+", lab)
        estrelas.append(int(nums[0]) if nums else np.nan)

    df["bert_estrelas"] = estrelas

    def mapear(e):
        if pd.isna(e):
            return "indefinido"
        e = int(e)
        if e <= 2:
            return "negativo"
        elif e == 3:
            return "neutro"
        else:
            return "positivo"

    df["bert_label"] = df["bert_estrelas"].apply(mapear)

    return df
