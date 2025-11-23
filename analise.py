import re
import numpy as np
import pandas as pd
import string

# Tentativa de importar VADER
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

# Tentativa de importar BERT (Transformers)
try:
    from transformers import pipeline
    BERT_AVAILABLE = True
except ImportError:
    BERT_AVAILABLE = False


# ============================================================
#   PRÉ-PROCESSAMENTO
# ============================================================

def limpar_texto(texto: str) -> str:
    if pd.isna(texto):
        return ""

    t = str(texto)

    # Remove URLs
    t = re.sub(r"http\S+|www\.\S+", "", t)

    # Remove @menções e #hashtags
    t = re.sub(r"[@#]\w+", "", t)

    # Remove números
    t = re.sub(r"\d+", "", t)

    # Remove pontuação
    t = t.translate(str.maketrans("", "", string.punctuation))

    # Espaços extras
    t = re.sub(r"\s+", " ", t).strip()

    return t.lower()


def preprocessar_textos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona coluna texto_limpo ao DataFrame.
    """
    if "comment" not in df.columns:
        raise ValueError("A coluna 'comment' não existe no DataFrame.")

    df["texto_limpo"] = df["comment"].apply(limpar_texto)
    return df


# ============================================================
#   ANÁLISE DE SENTIMENTO – VADER
# ============================================================

def aplicar_vader(df: pd.DataFrame) -> pd.DataFrame:
    if not VADER_AVAILABLE:
        print("⚠ Biblioteca VADER não encontrada. Instale com: pip install vaderSentiment")
        df["vader_compound"] = np.nan
        df["vader_label"] = "indefinido"
        return df

    sia = SentimentIntensityAnalyzer()

    df["vader_compound"] = df["texto_limpo"].apply(lambda t: sia.polarity_scores(t)["compound"])

    def _classificar(comp):
        if comp >= 0.05:
            return "positivo"
        elif comp <= -0.05:
            return "negativo"
        return "neutro"

    df["vader_label"] = df["vader_compound"].apply(_classificar)
    return df


# ============================================================
#   ANÁLISE DE SENTIMENTO – BERT (Transformers)
# ============================================================

def aplicar_bert(df: pd.DataFrame) -> pd.DataFrame:
    if not BERT_AVAILABLE:
        print("⚠ Transformers não disponível. Instale com: pip install transformers")
        df["bert_label_raw"] = "indefinido"
        df["bert_estrelas"] = np.nan
        df["bert_label"] = "indefinido"
        return df

    print("Carregando modelo BERT (nlptown)… Aguarde...")
    clf = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

    textos = df["texto_limpo"].fillna("").tolist()
    resultados = clf(textos, truncation=True)

    df["bert_label_raw"] = [r["label"] for r in resultados]

    # Extrai número de estrelas da label
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
