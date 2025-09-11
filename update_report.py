import os
from datetime import datetime

RELATORIO_PATH = "RELATORIO.md"

def atualizar_relatorio(data, atividade, responsaveis, status):
    """
    Atualiza o RELATORIO.md adicionando uma nova linha na tabela de entregas semanais.

    Args:
        data (str): Data no formato DD/MM/AAAA
        atividade (str): Descrição da atividade/entregável
        responsaveis (str): Nomes dos responsáveis
        status (str): Status (✅ Concluído | ⏳ Em andamento | 🔲 Pendente)
    """
    nova_linha = f"| {data} | {atividade} | {responsaveis} | {status} |\n"

    if not os.path.exists(RELATORIO_PATH):
        print("⚠️ Arquivo RELATORIO.md não encontrado. Criando um novo...")
        with open(RELATORIO_PATH, "w", encoding="utf-8") as f:
            f.write("# 📝 Relatório de Atividades – Projeto *YouTube Sentiment Analysis*\n\n")
            f.write("| Data       | Entregável / Atividade | Responsáveis | Status |\n")
            f.write("|------------|------------------------|--------------|--------|\n")

    with open(RELATORIO_PATH, "a", encoding="utf-8") as f:
        f.write(nova_linha)

    print(f"✅ Atividade registrada: {atividade} ({data})")

if __name__ == "__main__":
    # Exemplo de uso:
    data = input("Digite a data (DD/MM/AAAA): ")
    atividade = input("Digite a descrição da atividade: ")
    responsaveis = input("Digite os responsáveis: ")
    status = input("Digite o status (✅ Concluído | ⏳ Em andamento | 🔲 Pendente): ")

    atualizar_relatorio(data, atividade, responsaveis, status)
