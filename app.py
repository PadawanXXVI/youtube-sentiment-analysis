import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
import os

from coleta import extrair_channel_id, listar_videos_canal, coletar_comentarios_video
from analise import preprocessar_textos, aplicar_vader, aplicar_bert

load_dotenv()

st.set_page_config(page_title="YouTube Sentiment Dashboard", layout="wide")
sns.set(style="whitegrid")

# ================================
#       INTERFACE DO DASHBOARD
# ================================

st.title("📊 YouTube Sentiment Dashboard")
st.markdown("### Analise comentários de qualquer canal usando VADER + BERT")

with st.sidebar:
    st.header("🎥 Configurações")
    canal_input = st.text_input(
        "Informe o canal do YouTube (URL ou Channel ID):",
        value=os.getenv("CHANNEL_ID", "")
    )
    max_videos = st.slider("Quantidade de vídeos a coletar:", 1, 20, 5)
    max_comments = st.slider("Comentários por vídeo:", 20, 500, 200)

    iniciar = st.button("🔍 Coletar e Analisar")


if iniciar:
    try:
        channel_id = extrair_channel_id(canal_input)
        st.info(f"Canal detectado: `{channel_id}`")

        st.subheader("📥 Coletando vídeos...")
        videos = listar_videos_canal(channel_id, max_videos=max_videos)
        df_videos = pd.DataFrame(videos)
        st.write(df_videos)

        st.subheader("💬 Coletando comentários...")
        all_comments = []
        for v in videos:
            vid = v["video_id"]
            comments = coletar_comentarios_video(vid, max_comments)
            all_comments.extend(comments)

        df = pd.DataFrame(all_comments)
        st.success(f"Foram coletados {len(df)} comentários!")

        # =====================================
        #           PRÉ-PROCESSAMENTO
        # =====================================
        st.subheader("🧹 Limpando textos...")
        df = preprocessar_textos(df)
        st.write(df.head())

        # =====================================
        #            ANÁLISE VADER
        # =====================================
        st.subheader("🔎 VADER - Sentiment Analysis")
        df = aplicar_vader(df)
        col1, col2, col3 = st.columns(3)
        col1.metric("Positivos", int((df["vader_label"] == "positivo").sum()))
        col2.metric("Neutros", int((df["vader_label"] == "neutro").sum()))
        col3.metric("Negativos", int((df["vader_label"] == "negativo").sum()))

        # Gráfico VADER
        fig, ax = plt.subplots()
        sns.countplot(data=df, x="vader_label", order=["negativo", "neutro", "positivo"], ax=ax)
        ax.set_title("Distribuição VADER")
        st.pyplot(fig)

        # =====================================
        #             ANÁLISE BERT
        # =====================================
        st.subheader("🤖 BERT - Sentiment Analysis")
        df = aplicar_bert(df)
        col4, col5, col6 = st.columns(3)
        col4.metric("Positivos", int((df["bert_label"] == "positivo").sum()))
        col5.metric("Neutros", int((df["bert_label"] == "neutro").sum()))
        col6.metric("Negativos", int((df["bert_label"] == "negativo").sum()))

        # Gráfico BERT
        fig2, ax2 = plt.subplots()
        sns.countplot(data=df, x="bert_label", order=["negativo", "neutro", "positivo"], ax=ax2)
        ax2.set_title("Distribuição BERT")
        st.pyplot(fig2)

        # =====================================
        #            TABELA COMPLETA
        # =====================================
        st.subheader("📄 Comentários Classificados")
        st.dataframe(df[["author", "comment", "vader_label", "bert_label"]])

        # =====================================
        #        SALVAR RESULTADO CSV
        # =====================================
        from datetime import datetime

        os.makedirs("resultados", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path_out = f"resultados/analise_canal_{ts}.csv"
        df.to_csv(path_out, index=False, encoding="utf-8-sig")

        st.success(f"Arquivo salvo em: {path_out}")

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
