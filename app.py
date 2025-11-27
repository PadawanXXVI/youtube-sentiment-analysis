import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Importações internas
from coleta import extrair_channel_id, listar_videos_canal, coletar_comentarios_video
from analise import preprocessar_textos, aplicar_vader, aplicar_bert

# ===============================================
# CONFIGURAÇÃO DA PÁGINA
# ===============================================
st.set_page_config(page_title="YouTube Sentiment Dashboard", layout="wide")
sns.set(style="whitegrid")

st.title("📊 YouTube Sentiment Dashboard")
st.markdown("### Analise comentários de *qualquer vídeo ou canal* usando VADER + BERT")

# ===============================================
# SIDEBAR
# ===============================================
with st.sidebar:
    st.header("🎥 Configurações")

    canal_input = st.text_input(
        "Cole aqui QUALQUER link do YouTube (vídeo, canal, @handle ou ID):",
        value=""
    )

    max_videos = st.slider("Quantidade de vídeos a coletar:", 1, 20, 5)
    max_comments = st.slider("Comentários por vídeo:", 20, 500, 200)

    iniciar = st.button("🔍 Coletar e Analisar")


# ===============================================
# LÓGICA PRINCIPAL
# ===============================================
if iniciar:
    try:
        # Detecta canal automaticamente
        channel_id = extrair_channel_id(canal_input)
        st.info(f"🔎 Canal detectado: {channel_id}")

        # -------------------------------------------
        # COLETAR VÍDEOS
        # -------------------------------------------
        st.subheader("📥 Coletando vídeos...")
        videos = listar_videos_canal(channel_id, max_videos=max_videos)

        if not videos:
            st.error("Nenhum vídeo encontrado para este canal.")
            st.stop()

        df_videos = pd.DataFrame(videos)
        st.write(df_videos)

        # -------------------------------------------
        # COLETAR COMENTÁRIOS
        # -------------------------------------------
        st.subheader("💬 Coletando comentários...")
        all_comments = []

        for v in videos:
            vid = v["video_id"]
            comments = coletar_comentarios_video(vid, max_comments)
            all_comments.extend(comments)

        df = pd.DataFrame(all_comments)

        if df.empty:
            st.error("Nenhum comentário encontrado.")
            st.stop()

        st.success(f"🎉 {len(df)} comentários coletados!")

        # -------------------------------------------
        # PRÉ-PROCESSAMENTO
        # -------------------------------------------
        st.subheader("🧹 Limpando textos dos comentários...")
        df = preprocessar_textos(df)
        st.write(df.head())

        # -------------------------------------------
        # VADER
        # -------------------------------------------
        st.subheader("🔎 Análise de Sentimentos — VADER")
        df = aplicar_vader(df)

        col1, col2, col3 = st.columns(3)
        col1.metric("Positivos (VADER)", int((df["vader_label"] == "positivo").sum()))
        col2.metric("Neutros (VADER)", int((df["vader_label"] == "neutro").sum()))
        col3.metric("Negativos (VADER)", int((df["vader_label"] == "negativo").sum()))

        fig, ax = plt.subplots()
        sns.countplot(data=df, x="vader_label", order=["negativo", "neutro", "positivo"], ax=ax)
        st.pyplot(fig)

        # -------------------------------------------
        # BERT
        # -------------------------------------------
        st.subheader("🤖 Análise de Sentimentos — BERT")
        df = aplicar_bert(df)

        col4, col5, col6 = st.columns(3)
        col4.metric("Positivos (BERT)", int((df["bert_label"] == "positivo").sum()))
        col5.metric("Neutros (BERT)", int((df["bert_label"] == "neutro").sum()))
        col6.metric("Negativos (BERT)", int((df["bert_label"] == "negativo").sum()))

        fig2, ax2 = plt.subplots()
        sns.countplot(data=df, x="bert_label", order=["negativo", "neutro", "positivo"], ax=ax2)
        st.pyplot(fig2)

        # -------------------------------------------
        # TABELA COMPLETA
        # -------------------------------------------
        st.subheader("📄 Tabela de Comentários Classificados")
        st.dataframe(df[["author", "comment", "vader_label", "bert_label"]], use_container_width=True)

        # -------------------------------------------
        # EXPORTAÇÃO
        # -------------------------------------------
        st.subheader("💾 Exportar Resultado")
        from datetime import datetime
        os.makedirs("resultados", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        path_out = f"resultados/analise_{channel_id}_{ts}.csv"
        df.to_csv(path_out, index=False, encoding="utf-8-sig")

        st.success(f"📁 Arquivo salvo em: {path_out}")

    except Exception as e:
        st.error(f"❌ Erro ao processar: {e}")
        