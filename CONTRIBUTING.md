# 🤝 Contribuindo para o projeto *YouTube Sentiment Analysis*

Obrigado por considerar contribuir com este projeto!  
Este documento define as diretrizes para participação, organização e boas práticas no repositório.

---

## 📌 Como contribuir

1. **Faça um fork** do repositório.  
2. **Crie uma branch** com um nome descritivo:  
   ```
   git checkout -b feat/nova-funcionalidade
   ```
3. **Implemente suas alterações** (código, documentação ou dados).  
4. **Confirme seus commits** seguindo o padrão [Conventional Commits](#✍️-padrão-de-commits).  
5. **Abra um Pull Request (PR)** para a branch `main` descrevendo claramente a mudança.  

---

## 🗂️ Organização do projeto

- **Issues**: usadas para reportar bugs, sugerir melhorias e acompanhar tarefas.  
- **Labels**: ajudam a organizar as issues:  
  - `coleta` → tarefas ligadas à coleta de dados  
  - `pré-processamento` → limpeza e preparação dos textos  
  - `análise de sentimentos` → modelagem e classificação  
  - `visualização` → geração de gráficos e dashboards  
  - `documentação` → relatórios, README, etc.  
- **Milestones**: representam as entregas da disciplina:  
  - Etapa 1 – Coleta e Pré-processamento  
  - Etapa 2 – Análise de Sentimentos  
  - Etapa 3 – Visualização dos Resultados  
  - Etapa 4 – Relatório Final e Apresentação  
- **Project Board (Kanban)**: organiza o fluxo de trabalho em:  
  - Backlog → planejado  
  - Em andamento → em execução  
  - Concluído → finalizado  

---

## ✍️ Padrão de commits

Usamos o padrão **[Conventional Commits](https://www.conventionalcommits.org/)**.  
Formato:  
```
tipo(escopo): mensagem breve
```

### Tipos mais usados
- **feat** → nova funcionalidade  
- **fix** → correção de bug  
- **docs** → mudanças apenas na documentação  
- **style** → formatação (espaços, indentação, ponto e vírgula)  
- **refactor** → refatoração de código (sem mudar funcionalidade)  
- **test** → criação ou ajuste de testes  
- **chore** → tarefas diversas (build, dependências, configs)  

### Exemplos
- `feat(api): implementar coleta de comentários do YouTube`  
- `fix(preprocess): corrigir remoção de stopwords`  
- `docs(readme): adiciona checklist de issues e snapshot do Kanban`  

---

## 📋 Boas práticas

- Sempre vincule **issues** às **milestones**.  
- Atualize o **Project Board** movendo tarefas de *Backlog → Em andamento → Concluído*.  
- Descreva claramente o que foi feito no **Pull Request**.  
- Revise ortografia e clareza nos relatórios/documentação.  

---

## 📬 Contato

Dúvidas ou sugestões podem ser abertas como **issues** neste repositório ou discutidas diretamente com a equipe:  
- Anderson de Matos Guimarães  
- Gustavo Stefano Thomazinho  
- Renan Ost  
