import os

RELATORIO_PATH = "RELATORIO.md"

def atualizar_relatorio(data, atividade, responsaveis, status):
    """
    Atualiza o RELATORIO.md:
    - Se a data + atividade já existem, atualiza responsáveis e status.
    - Caso contrário, adiciona uma nova linha.
    """
    nova_linha = f"| {data} | {atividade} | {responsaveis} | {status} |\n"

    # Se não existir RELATORIO.md, cria do zero
    if not os.path.exists(RELATORIO_PATH):
        print("⚠️ Arquivo RELATORIO.md não encontrado. Criando um novo...")
        with open(RELATORIO_PATH, "w", encoding="utf-8") as f:
            f.write("# 📝 Relatório de Atividades – Projeto *YouTube Sentiment Analysis*\n\n")
            f.write("| Data       | Entregável / Atividade | Responsáveis | Status |\n")
            f.write("|------------|------------------------|--------------|--------|\n")
            f.write(nova_linha)
        print(f"✅ Atividade registrada: {atividade} ({data})")
        return

    # Ler conteúdo existente
    with open(RELATORIO_PATH, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    cabecalho = []
    tabela = []
    dentro_tabela = False

    for linha in linhas:
        if linha.startswith("| Data"):
            dentro_tabela = True
        if dentro_tabela:
            tabela.append(linha)
        else:
            cabecalho.append(linha)

    # Verificar se já existe a mesma data + atividade
    atualizado = False
    for i, linha in enumerate(tabela):
        colunas = [c.strip() for c in linha.split("|")[1:-1]]
        if len(colunas) == 4 and colunas[0] == data and colunas[1] == atividade:
            tabela[i] = nova_linha
            atualizado = True
            break

    # Se não encontrou, adiciona nova linha
    if not atualizado:
        tabela.append(nova_linha)

    # Regravar o arquivo
    with open(RELATORIO_PATH, "w", encoding="utf-8") as f:
        f.writelines(cabecalho + tabela)

    if atualizado:
        print(f"🔄 Atividade atualizada: {atividade} ({data})")
    else:
        print(f"✅ Nova atividade registrada: {atividade} ({data})")


if __name__ == "__main__":
    # Entrada de dados pelo usuário
    data = input("Digite a data (DD/MM/AAAA): ")
    atividade = input("Digite a descrição da atividade: ")
    responsaveis = input("Digite os responsáveis: ")
    status = input("Digite o status (✅ Concluído | ⏳ Em andamento | 🔲 Pendente): ")

    atualizar_relatorio(data, atividade, responsaveis, status)
