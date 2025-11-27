import os
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from coleta import (
    extrair_video_id,
    extrair_channel_id,
    listar_videos_recentes,
    listar_videos_mais_vistos,
    listar_videos_mais_comentados,
    coletar_comentarios_multiplos_videos,
)
from analise import (
    preprocessar_textos,
    aplicar_vader,
    aplicar_bert,
    resumo_sentimentos,
    palavras_mais_frequentes,
)

# ============================================================
#   CONFIGURAÇÃO BÁSICA
# ============================================================
st.set_page_config(
    page_title="YouTube Sentiment Dashboard",
    layout="wide",
)
sns.set(style="whitegrid")

st.title("📊 YouTube Sentiment Dashboard")
st.markdown("#### Analise comentários de vídeos do YouTube usando *VADER + BERT*")


# ============================================================
#   SIDEBAR
# ============================================================
with st.sidebar:
    st.header("🎥 Configurações")

    link_input = st.text_input(
        "Cole aqui qualquer link do YouTube (vídeo, canal, @handle ou ID):",
        value="",
        placeholder="https://www.youtube.com/watch?v=...",
    )

    modo_analise = st.selectbox(
        "Modo de análise:",
        [
            "Automático (recomendado)",
            "Apenas este vídeo",
            "Canal – múltiplos vídeos",
        ],
    )

    criterio_videos = st.selectbox(
        "Como escolher os vídeos do canal?",
        [
            "Mais recentes",
            "Mais vistos",
            "Mais comentados (beta)",
        ],
    )

    max_videos = st.slider("Quantidade de vídeos do canal:", 1, 20, 5)
    max_comments = st.slider("Comentários por vídeo:", 20, 500, 200)

    iniciar = st.button("🔍 Coletar e Analisar")


# ============================================================
#   SELEÇÃO DE VÍDEOS
# ============================================================
def selecionar_videos(link: str) -> tuple[str | None, list[dict]]:
    """
    Decide se analisa um único vídeo ou múltiplos vídeos do canal.
    Retorna (channel_id, lista_de_videos)
    """
    # Modo "apenas este vídeo"
    if modo_analise == "Apenas este vídeo":
        vid = extrair_video_id(link)
        if not vid:
            raise ValueError("Não consegui extrair o ID do vídeo. Verifique o link informado.")
        canal_id = extrair_channel_id(link)
        return canal_id, [{"video_id": vid, "video_title": "Vídeo único", "video_published_at": None}]

    # Modos que usam múltiplos vídeos do canal
    canal_id = extrair_channel_id(link)

    if criterio_videos == "Mais vistos":
        videos = listar_videos_mais_vistos(canal_id, max_videos=max_videos)
    elif criterio_videos == "Mais comentados (beta)":
        videos = listar_videos_mais_comentados(canal_id, max_videos=max_videos)
    else:
        videos = listar_videos_recentes(canal_id, max_videos=max_videos)

    return canal_id, videos


# ============================================================
#   LÓGICA PRINCIPAL
# ============================================================
if iniciar:
    try:
        if not link_input.strip():
            st.error("Informe um link de vídeo ou canal do YouTube.")
            st.stop()

        canal_id, videos = selecionar_videos(link_input)

        if not videos:
            st.error("Nenhum vídeo encontrado para este canal.")
            st.stop()

        st.info(f"📺 Canal detectado: {canal_id}")

        df_videos = pd.DataFrame(videos)

        st.subheader("🎬 Vídeos selecionados para análise")
        st.dataframe(df_videos, use_container_width=True)

        # -------------------------------------------
        # COLETA DE COMENTÁRIOS
        # -------------------------------------------
        st.subheader("💬 Coletando comentários...")
        with st.spinner("Buscando comentários na API do YouTube..."):
            df_comments = coletar_comentarios_multiplos_videos(
                videos, max_comments_por_video=max_comments
            )

        if df_comments.empty:
            st.warning("Nenhum comentário encontrado para os vídeos selecionados.")
            st.stop()

        st.success(f"✅ {len(df_comments)} comentários coletados!")

        # -------------------------------------------
        # PRÉ-PROCESSAMENTO
        # -------------------------------------------
        st.subheader("🧹 Limpando textos...")
        df = preprocessar_textos(df_comments)
        st.dataframe(df.head(), use_container_width=True)

        # -------------------------------------------
        # ANÁLISE DE SENTIMENTOS
        # -------------------------------------------
        st.subheader("🧠 Rodando análises de sentimento...")
        df = aplicar_vader(df)
        df = aplicar_bert(df)

        resumo = resumo_sentimentos(df)

        # -------------------------------------------
        # ABAS DO DASHBOARD
        # -------------------------------------------
        tab_geral, tab_vader, tab_bert, tab_comentarios, tab_insights, tab_export = st.tabs(
            ["📌 Visão Geral", "🧪 VADER", "🤖 BERT", "💬 Comentários", "📊 Insights", "💾 Exportação"]
        )

        # ---------------- Visão Geral ----------------
        with tab_geral:
            st.subheader("📌 Resumo Geral")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total de comentários", resumo["total_comentarios"])

            vader_pos = resumo["vader"]["percents"].get("positivo", 0)
            bert_pos = resumo["bert"]["percents"].get("positivo", 0)
            col2.metric("Positivos (VADER)", f"{vader_pos:.1f}%")
            col3.metric("Positivos (BERT)", f"{bert_pos:.1f}%")

            st.markdown("##### Comparação de distribuição de sentimentos")
            dist_df = pd.DataFrame(
                {
                    "sentimento": ["negativo", "neutro", "positivo"],
                    "VADER": [
                        resumo["vader"]["counts"]["negativo"],
                        resumo["vader"]["counts"]["neutro"],
                        resumo["vader"]["counts"]["positivo"],
                    ],
                    "BERT": [
                        resumo["bert"]["counts"]["negativo"],
                        resumo["bert"]["counts"]["neutro"],
                        resumo["bert"]["counts"]["positivo"],
                    ],
                }
            ).set_index("sentimento")
            st.bar_chart(dist_df)

        # ---------------- VADER ----------------
        with tab_vader:
            st.subheader("🧪 Distribuição VADER")
            col1, col2, col3 = st.columns(3)
            col1.metric("Negativos", int(resumo["vader"]["counts"]["negativo"]))
            col2.metric("Neutros", int(resumo["vader"]["counts"]["neutro"]))
            col3.metric("Positivos", int(resumo["vader"]["counts"]["positivo"]))

            fig, ax = plt.subplots()
            sns.countplot(
                data=df,
                x="vader_label",
                order=["negativo", "neutro", "positivo"],
                ax=ax,
            )
            ax.set_title("Distribuição de sentimentos (VADER)")
            st.pyplot(fig)

        # ---------------- BERT ----------------
        with tab_bert:
            st.subheader("🤖 Distribuição BERT")
            col1, col2, col3 = st.columns(3)
            col1.metric("Negativos", int(resumo["bert"]["counts"]["negativo"]))
            col2.metric("Neutros", int(resumo["bert"]["counts"]["neutro"]))
            col3.metric("Positivos", int(resumo["bert"]["counts"]["positivo"]))

            fig2, ax2 = plt.subplots()
            sns.countplot(
                data=df,
                x="bert_label",
                order=["negativo", "neutro", "positivo"],
                ax=ax2,
            )
            ax2.set_title("Distribuição de sentimentos (BERT)")
            st.pyplot(fig2)

        # ---------------- Comentários ----------------
        with tab_comentarios:
            st.subheader("💬 Comentários classificados")
            filtro_sent = st.selectbox(
                "Filtrar por sentimento (BERT):",
                ["Todos", "positivo", "neutro", "negativo"],
            )
            df_filtrado = df
            if filtro_sent != "Todos":
                df_filtrado = df[df["bert_label"] == filtro_sent]

            st.dataframe(
                df_filtrado[["video_id", "author", "comment", "vader_label", "bert_label"]],
                use_container_width=True,
            )

        # ---------------- Insights ----------------
        with tab_insights:
            st.subheader("📊 Insights de texto")

            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("*Palavras mais frequentes (geral)*")
                freq_geral = palavras_mais_frequentes(df, n=20)
                st.dataframe(freq_geral, use_container_width=True)

            with col_b:
                st.markdown("*Palavras mais frequentes em comentários negativos (BERT)*")
                freq_neg = palavras_mais_frequentes(
                    df,
                    n=20,
                    filtro_coluna="bert_label",
                    filtro_valor="negativo",
                )
                st.dataframe(freq_neg, use_container_width=True)

            st.markdown("---")
            st.markdown("*Top 5 comentários mais positivos (BERT)*")
            positivos = df[df["bert_label"] == "positivo"].copy()
            positivos = positivos.sort_values(by="like_count", ascending=False).head(5)
            st.dataframe(
                positivos[["video_id", "author", "comment", "like_count"]],
                use_container_width=True,
            )

            st.markdown("*Top 5 comentários mais negativos (BERT)*")
            negativos = df[df["bert_label"] == "negativo"].copy()
            negativos = negativos.sort_values(by="like_count", ascending=False).head(5)
            st.dataframe(
                negativos[["video_id", "author", "comment", "like_count"]],
                use_container_width=True,
            )

        # ---------------- Exportação ----------------
        with tab_export:
            st.subheader("💾 Exportar dados")
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"analise_youtube_{ts}.csv"

            csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")

            st.download_button(
                label="⬇ Baixar CSV completo",
                data=csv_bytes,
                file_name=nome_arquivo,
                mime="text/csv",
            )

            st.info(
                "O arquivo CSV contém todas as colunas da análise: vídeo, autor, comentário, "
                "labels de sentimento do VADER e BERT, além de scores numéricos."
            )

    except Exception as e:
        st.error(f"❌ Erro ao processar: {e}")
        
