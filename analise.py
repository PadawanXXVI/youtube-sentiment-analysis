import re
import numpy as np
import pandas as pd
import string

# Tentativa de importar VADER
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # type: ignore
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

# Tentativa de importar BERT (Transformers)
try:
    from transformers import pipeline  # type: ignore
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
    if "comment" not in df.columns:
        raise ValueError("A coluna 'comment' não existe no DataFrame.")
    df["texto_limpo"] = df["comment"].apply(limpar_texto)
    return df


# ============================================================
#   VADER
# ============================================================
def aplicar_vader(df: pd.DataFrame) -> pd.DataFrame:
    if not VADER_AVAILABLE:
        df["vader_compound"] = np.nan
        df["vader_label"] = "indefinido"
        return df

    sia = SentimentIntensityAnalyzer()

    df["vader_compound"] = df["texto_limpo"].apply(lambda t: sia.polarity_scores(t)["compound"])

    def _classificar(comp):
        if comp >= 0.05:
            return "positivo"
        if comp <= -0.05:
            return "negativo"
        return "neutro"

    df["vader_label"] = df["vader_compound"].apply(_classificar)
    return df


# ============================================================
#   BERT
# ============================================================
def aplicar_bert(df: pd.DataFrame) -> pd.DataFrame:
    if not BERT_AVAILABLE:
        df["bert_label_raw"] = "indefinido"
        df["bert_estrelas"] = np.nan
        df["bert_label"] = "indefinido"
        return df

    clf = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

    textos = df["texto_limpo"].fillna("").tolist()
    resultados = clf(textos, truncation=True)

    df["bert_label_raw"] = [r["label"] for r in resultados]

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
        if e == 3:
            return "neutro"
        return "positivo"

    df["bert_label"] = df["bert_estrelas"].apply(mapear)
    return df


# ============================================================
#   RESUMO DE SENTIMENTOS
# ============================================================
def resumo_sentimentos(df: pd.DataFrame) -> dict:
    """
    Calcula contagens e percentuais de sentimentos para VADER e BERT.
    """
    total = len(df) if len(df) > 0 else 1

    def _contar(col):
        cont = df[col].value_counts(dropna=False).to_dict()
        for k in ("positivo", "neutro", "negativo"):
            cont.setdefault(k, 0)
        return {
            "counts": cont,
            "percents": {k: (v / total) * 100 for k, v in cont.items()},
        }

    return {
        "total_comentarios": len(df),
        "vader": _contar("vader_label") if "vader_label" in df.columns else {},
        "bert": _contar("bert_label") if "bert_label" in df.columns else {},
    }


# ============================================================
#   PALAVRAS MAIS FREQUENTES (insights de texto)
# ============================================================
STOPWORDS_PT = {
    "a", "o", "as", "os", "de", "da", "do", "das", "dos", "e", "é", "que", "em",
    "um", "uma", "para", "por", "na", "no", "nas", "nos", "com", "se", "eu", "você",
    "ele", "ela", "eles", "elas", "te", "me", "já", "mas", "muito", "muita", "muitos",
    "muitas", "vai", "tá", "ta", "tô", "to", "ser", "estar", "foi", "era", "tem",
}


def palavras_mais_frequentes(
    df: pd.DataFrame,
    n: int = 20,
    filtro_coluna: str | None = None,
    filtro_valor: str | None = None,
) -> pd.DataFrame:
    """
    Retorna um DataFrame com as N palavras mais frequentes em 'texto_limpo'.
    Pode filtrar por uma coluna de sentimento (ex: 'bert_label') e valor ('negativo').
    """
    dados = df
    if filtro_coluna and filtro_valor:
        dados = dados[dados[filtro_coluna] == filtro_valor]

    todas_palavras: list[str] = []
    for t in dados["texto_limpo"].dropna().tolist():
        for p in str(t).split():
            p = p.strip().lower()
            if not p or p in STOPWORDS_PT or len(p) <= 2:
                continue
            todas_palavras.append(p)

    if not todas_palavras:
        return pd.DataFrame(columns=["palavra", "frequencia"])

    serie = pd.Series(todas_palavras)
    freq = serie.value_counts().reset_index()
    freq.columns = ["palavra", "frequencia"]
    return freq.head(n)
    
