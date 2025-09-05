# 🎥 Análise de Sentimentos em Comentários de Vídeos do YouTube

Projeto acadêmico desenvolvido para a disciplina **Mineração de Textos**, no 4º semestre do curso de **Tecnologia em Ciência de Dados** da **Faculdade de Tecnologia e Inovação Senac DF**, sob orientação do professor **Msc. Edgar Devanir Amoroso**.

---

## 👥 Equipe
- Anderson de Matos Guimarães  
- Gustavo Stefano Thomazinho  
- Renan Ost  

---

## 🎯 Objetivo

Aplicar técnicas de **mineração de textos** e **processamento de linguagem natural (NLP)** para identificar sentimentos expressos por usuários nos comentários de vídeos do YouTube. O projeto visa classificar os comentários como **positivos**, **negativos** ou **neutros**, e gerar visualizações que permitam interpretar padrões emocionais e temáticos.

---

## 🧪 Tecnologias Utilizadas

- **Sistema Operacional**: Windows  
- **Editor de Código**: Visual Studio Code (VS Code)  
- **Ambiente de Desenvolvimento**: Jupyter Notebook integrado ao VS Code  
- **Terminal**: Bash integrado  
- **Linguagem**: Python  
- **Bibliotecas**:
  - `google-api-python-client` (coleta de dados via YouTube API)
  - `pandas`, `numpy` (manipulação de dados)
  - `nltk`, `spaCy` (pré-processamento de texto)
  - `transformers`, `TextBlob`, `BERTimbau` (análise de sentimentos)
  - `matplotlib`, `seaborn`, `plotly` (visualização)

---

## 📁 Estrutura do Projeto

```
youtube-sentiment-analysis/
│
├── data/                     # Dados brutos e tratados
│   ├── raw/                  # Comentários originais
│   └── processed/            # Dados limpos e prontos para análise
│
├── notebooks/                # Jupyter Notebooks com experimentos
│   ├── coleta.ipynb          # Coleta de dados via API
│   ├── limpeza.ipynb         # Pré-processamento dos textos
│   ├── sentimentos.ipynb     # Análise de sentimentos
│   └── visualizacao.ipynb    # Gráficos e dashboards
│
├── src/                      # Scripts Python reutilizáveis
│   ├── youtube_api.py        # Coleta de comentários
│   ├── preprocess.py         # Limpeza e normalização
│   ├── sentiment_model.py    # Classificação de sentimentos
│   └── utils.py              # Funções auxiliares
│
├── RELATORIO.md              # Relatórios semanais
├── requirements.txt          # Lista de dependências
└── .gitignore                # Arquivos ignorados pelo Git
```

---

## 📌 Organização no GitHub

- **GitHub Projects**: Quadro Kanban com colunas *Backlog*, *Em andamento*, *Concluído*
- **Milestones**: Etapas do projeto divididas por entregas
- **Issues**: Tarefas específicas com labels como `coleta`, `NLP`, `visualização`, `documentação`

---

## 📊 Resultados Esperados

- Classificação dos sentimentos por comentário
- Gráficos de polaridade e nuvem de palavras
- Comparação entre vídeos e temas
- Relatório final com interpretação dos padrões encontrados

---

## 📄 Licença

Este projeto está licenciado sob a **MIT License**.

---

## 📬 Contato

Para dúvidas ou sugestões, entre em contato com a equipe via GitHub ou diretamente com os autores.
