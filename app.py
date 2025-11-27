import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Importações internas
from coleta import (
    extrair_video_id,
    extrair_channel_id,
    listar_videos_recentes,
    listar_videos_mais_vistos,
    listar_videos_mais_comentados,
    coletar_comentarios_video
)
from analise import preprocessar_textos, aplicar_vader, aplicar_bert

# ===============================================
# CONFIGURAÇÃO DA PÁGINA
# ===============================================
st.set_page_config(page_title="YouTube Sentiment Dashboard", layout="wide")
sns.set(style="whitegrid")

st.title("📊 YouTube Sentiment Dashboard")
st.markdown("### Analise comentários de vídeos do YouTube usando *VADER + BERT*")

# ===============================================
# SIDEBAR — CONFIGURAÇÕES
# ===============================================
with st.sidebar:
    st.header("🎥 Configurações")

    canal_input = st.text_input(
        "Cole aqui qualquer link do YouTube (vídeo, canal, @handle ou ID):",
        value=""
    )

    modo_analise = st.selectbox(
        "Modo de Análise:",
        [
            "Automático (Recomendado)",
            "Apenas 1 vídeo específico",
            "Vários vídeos do canal"
        ]
    )

    criterio = st.selectbox(
        "Como escolher os vídeos do canal?",
        [
            "Mais recentes",
            "Mais vistos",
            "Mais comentados"
        ]
    )

    max_videos = st.slider("Quantidade de vídeos do canal:", 1, 20, 5)
    max_comments = st.slider("Comentários por vídeo:", 20, 500, 200)

    iniciar = st.button("🔍 Coletar e Analisar")


# ===============================================
# FUNÇÃO PRINCIPAL
# ===============================================
if iniciar:
    try:

        # =====================================================
        # 1 - MODO INTELIGENTE (AUTOMÁTICO)
        # =====================================================
        video_id = extrair_video_id(canal_input)

        if modo_analise == "Apenas 1 vídeo específico":
            if not video_id:
                st.error("❌ O link informado não é um vídeo.")
                st.stop()
            st.info(f"🎬 Vídeo detectado: {video_id}")
            videos = [{"video_id": video_id}]

        elif modo_analise == "Vários vídeos do canal":
            channel_id = extrair_channel_id(canal_input)
            st.info(f"📡 Canal detectado: {channel_id}")

            if criterio == "Mais recentes":
                videos = listar_videos_recentes(channel_id, max_videos)
            elif criterio == "Mais vistos":
                videos = listar_videos_mais_vistos(channel_id, max_videos)
            else:
                videos = listar_videos_mais_comentados(channel_id, max_videos)

        else:  # Automático
            if video_id:
                st.info(f"🎬 Vídeo detectado: {video_id}")
                videos = [{"video_id": video_id}]
            else:
                channel_id = extrair_channel_id(canal_input)
                st.info(f"📡 Canal detectado: {channel_id}")

                if criterio == "Mais recentes":
                    videos = listar_videos_recentes(channel_id, max_videos)
                elif criterio == "Mais vistos":
                    videos = listar_videos_mais_vistos(channel_id, max_videos)
                else:
                    videos = listar_videos_mais_comentados(channel_id, max_videos)

        # =====================================================
        # 2 - Mostrar vídeos selecionados
        # =====================================================
        st.subheader("📥 Vídeos selecionados para análise")
        df_videos = pd.DataFrame(videos)
        st.write(df_videos)

        # =====================================================
        # 3 - COLETAR COMENTÁRIOS
        # =====================================================
        st.subheader("💬 Coletando comentários...")
        all_comments = []

        for v in videos:
            comments = coletar_comentarios_video(v["video_id"], max_comments)
            all_comments.extend(comments)

        df = pd.DataFrame(all_comments)

        if df.empty:
            st.error("Nenhum comentário encontrado.")
            st.stop()

        st.success(f"🎉 {len(df)} comentários coletados!")

        # =====================================================
        # 4 - PRÉ PROCESSAMENTO
        # =====================================================
        st.subheader("🧹 Limpando textos...")
        df = preprocessar_textos(df)
        st.write(df.head())

        # =====================================================
        # 5 - VADER
        # =====================================================
        st.subheader("🔎 VADER — Análise de Sentimentos")
        df = aplicar_vader(df)

        col1, col2, col3 = st.columns(3)
        col1.metric("Positivos (VADER)", (df["vader_label"] == "positivo").sum())
        col2.metric("Neutros (VADER)", (df["vader_label"] == "neutro").sum())
        col3.metric("Negativos (VADER)", (df["vader_label"] == "negativo").sum())

        fig, ax = plt.subplots()
        sns.countplot(data=df, x="vader_label", order=["negativo", "neutro", "positivo"], ax=ax)
        st.pyplot(fig)

        # =====================================================
        # 6 - BERT
        # =====================================================
        st.subheader("🤖 BERT — Análise de Sentimentos")
        df = aplicar_bert(df)

        col4, col5, col6 = st.columns(3)
        col4.metric("Positivos (BERT)", (df["bert_label"] == "positivo").sum())
        col5.metric("Neutros (BERT)", (df["bert_label"] == "neutro").sum())
        col6.metric("Negativos (BERT)", (df["bert_label"] == "negativo").sum())

        fig2, ax2 = plt.subplots()
        sns.countplot(data=df, x="bert_label", order=["negativo", "neutro", "positivo"], ax=ax2)
        st.pyplot(fig2)

        # =====================================================
        # 7 - TABELA FINAL
        # =====================================================
        st.subheader("📄 Comentários Classificados")
        st.dataframe(df, use_container_width=True)

        # =====================================================
        # 8 - EXPORTAÇÃO
        # =====================================================
        from datetime import datetime
        os.makedirs("resultados", exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_name = f"analise_youtube_{ts}.csv"

        df.to_csv(f"resultados/{export_name}", index=False, encoding="utf-8-sig")

        st.success(f"📁 Arquivo exportado como: {export_name}")

    except Exception as e:
        st.error(f"❌ Erro ao processar: {e}")
        