import os
import logging
from datetime import datetime
from collections import defaultdict
from shutil import disk_usage
from tqdm import tqdm
import argparse
from rich.console import Console
from rich.tree import Tree
from win10toast import ToastNotifier
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image
import matplotlib.pyplot as plt

# Configuração do logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Inicializa o console do Rich
console = Console()

# Inicializa o ToastNotifier para notificações
toaster = ToastNotifier()

# Lista de extensões a serem ignoradas
EXTENSOES_IGNORADAS = {'.tmp', '.sys', '.dll', '.log'}
EXTENSOES_NECESSARIAS = {'.jpg', '.png', '.txt', '.pdf'}  # Exemplo, ajuste conforme necessário
TAMANHO_LIMITE_GRANDE = 100 * 1024 * 1024  # 100 MB
TAMANHO_LIMITE_ANOMALO_MIN = 10 * 1024 * 1024  # 10 MB
TAMANHO_LIMITE_ANOMALO_MAX = 200 * 1024 * 1024  # 200 MB

def listar_arquivos(caminho, nivel=0, exibir_todos=False, progress_bar=None):
    arquivos_pastas_tamanhos = []
    try:
        items = os.listdir(caminho)
        if progress_bar:
            progress_bar.total = len(items)

        for item in items:
            caminho_completo = os.path.join(caminho, item)
            emoji = '📄' if os.path.isfile(caminho_completo) else '📁'
            tamanho = 0

            try:
                if os.path.isfile(caminho_completo):
                    if any(caminho_completo.lower().endswith(ext) for ext in EXTENSOES_IGNORADAS):
                        continue
                    tamanho = os.path.getsize(caminho_completo)
                else:
                    tamanho = tamanho_pasta(caminho_completo)

                arquivos_pastas_tamanhos.append((item, tamanho, emoji))
                if progress_bar:
                    progress_bar.update(1)
            except Exception as e:
                logging.error(f"Erro ao processar {caminho_completo}: {e}")
                if progress_bar:
                    progress_bar.update(1)

    except Exception as e:
        logging.error(f"Erro ao listar arquivos: {e}")

    arquivos_pastas_tamanhos.sort(key=lambda x: x[1], reverse=True)

    tree = Tree(f"[bold cyan]📂 {os.path.basename(caminho)}[/]")
    for nome, tamanho, emoji in arquivos_pastas_tamanhos:
        tamanho_formatado = format_tamanho(tamanho)
        cor = "blue" if emoji == '📁' else "green"
        node = f"{emoji} [bold {cor}]{nome:<50}[/] {tamanho_formatado}"
        if emoji == '📁' and (exibir_todos or nivel == 0):
            sub_tree = listar_arquivos(os.path.join(caminho, nome), nivel + 1, exibir_todos, progress_bar)
            tree.add(sub_tree)
        else:
            tree.add(node)

    return tree

def tamanho_pasta(caminho):
    tamanho_total = 0
    try:
        for raiz, _, arquivos in os.walk(caminho):
            tamanho_total += sum(os.path.getsize(os.path.join(raiz, arquivo)) for arquivo in arquivos)
    except Exception as e:
        logging.error(f"Erro ao calcular o tamanho da pasta {caminho}: {e}")
    return tamanho_total

def format_tamanho(tamanho_bytes):
    if tamanho_bytes < 1024:
        return f"{tamanho_bytes} B"
    elif tamanho_bytes < 1024 ** 2:
        return f"{tamanho_bytes / 1024:.2f} KB"
    elif tamanho_bytes < 1024 ** 3:
        return f"{tamanho_bytes / (1024 ** 2):.2f} MB"
    else:
        return f"{tamanho_bytes / (1024 ** 3):.2f} GB"

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def obter_detalhes(caminho):
    total_pastas = 0
    total_arquivos = 0
    ultimo_acesso = defaultdict(lambda: datetime.fromtimestamp(0))

    try:
        for raiz, dirs, arquivos in os.walk(caminho):
            total_pastas += len(dirs)
            total_arquivos += len(arquivos)

            for arquivo in arquivos:
                caminho_arquivo = os.path.join(raiz, arquivo)
                try:
                    ultima_modificacao = os.path.getmtime(caminho_arquivo)
                    ultimo_acesso[arquivo] = max(ultimo_acesso[arquivo], datetime.fromtimestamp(ultima_modificacao))
                except Exception as e:
                    logging.error(f"Erro ao obter detalhes do arquivo {caminho_arquivo}: {e}")
    except Exception as e:
        logging.error(f"Erro ao obter detalhes do diretório {caminho}: {e}")

    total_usado, _, total_livre = disk_usage(caminho)
    total_usado_formatado = format_tamanho(total_usado)
    total_livre_formatado = format_tamanho(total_livre)

    console.print(f"\n[bold yellow]📊 Detalhes do Diretório:[/]")
    console.print(f"  • Total usado no disco: {total_usado_formatado}")
    console.print(f"  • Total livre no disco: {total_livre_formatado}")
    console.print(f"  • Total de pastas: {total_pastas}")
    console.print(f"  • Total de arquivos: {total_arquivos}")

    toaster.show_toast("Análise Completa", "O relatório e os detalhes foram gerados. Verifique o console.", duration=10)

    arquivos_para_deletar = []
    if input("Gostaria de recomendações de arquivos para deletar? (s/n): ").lower() in ["sim", "s"]:
        console.print("\n[bold yellow]🗑️ Recomendações de Arquivos para Deletar:[/]")

        arquivos_antigos = sugerir_arquivos_antigos(caminho, 30)
        arquivos_para_deletar.extend(arquivo[0] for arquivo in arquivos_antigos)
        console.print("\n[bold cyan]📅 Arquivos Antigos:[/]")
        for arquivo, ultima_modificacao in arquivos_antigos:
            console.print(f"  • [cyan]📄 {os.path.relpath(arquivo, caminho)}[/] (Última modificação: {ultima_modificacao.strftime('%Y-%m-%d')})")

        arquivos_grandes = sugerir_arquivos_grandes(caminho, TAMANHO_LIMITE_GRANDE)
        arquivos_para_deletar.extend(arquivo[0] for arquivo in arquivos_grandes)
        console.print("\n[bold cyan]📈 Arquivos Grandes:[/]")
        for arquivo, tamanho in arquivos_grandes:
            console.print(f"  • [cyan]📄 {os.path.relpath(arquivo, caminho)}[/] {format_tamanho(tamanho)}")

        arquivos_duplicados = sugerir_arquivos_duplicados(caminho)
        for arquivos in arquivos_duplicados.values():
            arquivos_para_deletar.extend(arquivos)
        console.print("\n[bold cyan]🔁 Arquivos Duplicados:[/]")
        for arquivos in arquivos_duplicados.values():
            for arquivo in arquivos:
                console.print(f"  • [cyan]📄 {os.path.relpath(arquivo, caminho)}[/]")

        arquivos_temporarios = sugerir_arquivos_temporarios(caminho)
        arquivos_para_deletar.extend(arquivos_temporarios)
        console.print("\n[bold cyan]🗑️ Arquivos Temporários:[/]")
        for arquivo in arquivos_temporarios:
            console.print(f"  • [cyan]📄 {os.path.relpath(arquivo, caminho)}[/]")

        arquivos_nao_necessarios = sugerir_arquivos_nao_necessarios(caminho)
        arquivos_para_deletar.extend(arquivos_nao_necessarios)
        console.print("\n[bold cyan]📋 Arquivos Não Necessários:[/]")
        for arquivo in arquivos_nao_necessarios:
            console.print(f"  • [cyan]📄 {os.path.relpath(arquivo, caminho)}[/]")

        arquivos_anomalos = sugerir_arquivos_tamanho_anomalo(caminho)
        arquivos_para_deletar.extend(arquivo[0] for arquivo in arquivos_anomalos)
        console.print("\n[bold cyan]🔎 Arquivos com Tamanho Anômalo:[/]")
        for arquivo, tamanho in arquivos_anomalos:
            console.print(f"  • [cyan]📄 {os.path.relpath(arquivo, caminho)}[/] {format_tamanho(tamanho)}")

    console.print("\n[bold yellow]🔄 Gerando Relatório PDF...[/]")
    criar_relatorio_pdf(caminho, arquivos_para_deletar)
    console.print("[bold green]✅ Relatório PDF gerado com sucesso![/]")

    if arquivos_para_deletar:
        tree_arquivos_para_deletar = listar_arquivos_para_deletar(arquivos_para_deletar)
        console.print("\n[bold red]🗑️ Arquivos Sugestionados para Deletar:[/]")
        console.print(tree_arquivos_para_deletar)
        escolha = input("\nEscolha uma opção:\n1. Deletar TUDO\n2. Deletar Manualmente\nEscolha: ")
        if escolha == "1":
            deletar_arquivos(arquivos_para_deletar)
            console.print("[bold green]✅ Todos os arquivos foram deletados![/]")
        elif escolha == "2":
            console.print("[bold yellow]Por favor, delete manualmente os arquivos listados acima.[/]")

def sugerir_arquivos_antigos(caminho, limite_dias):
    arquivos_sugeridos = []
    hoje = datetime.now()

    for raiz, _, arquivos in os.walk(caminho):
        for arquivo in arquivos:
            caminho_arquivo = os.path.join(raiz, arquivo)
            try:
                ultima_modificacao = os.path.getmtime(caminho_arquivo)
                if (hoje - datetime.fromtimestamp(ultima_modificacao)).days > limite_dias:
                    arquivos_sugeridos.append((caminho_arquivo, datetime.fromtimestamp(ultima_modificacao)))
            except Exception as e:
                logging.error(f"Erro ao verificar arquivo {caminho_arquivo}: {e}")

    return arquivos_sugeridos

def sugerir_arquivos_grandes(caminho, tamanho_limite):
    arquivos_sugeridos = []

    for raiz, _, arquivos in os.walk(caminho):
        for arquivo in arquivos:
            caminho_arquivo = os.path.join(raiz, arquivo)
            try:
                tamanho = os.path.getsize(caminho_arquivo)
                if tamanho > tamanho_limite:
                    arquivos_sugeridos.append((caminho_arquivo, tamanho))
            except Exception as e:
                logging.error(f"Erro ao verificar tamanho do arquivo {caminho_arquivo}: {e}")

    return arquivos_sugeridos

def sugerir_arquivos_duplicados(caminho):
    arquivos_hash = defaultdict(list)
    arquivos_duplicados = {}

    for raiz, _, arquivos in os.walk(caminho):
        for arquivo in arquivos:
            caminho_arquivo = os.path.join(raiz, arquivo)
            try:
                with open(caminho_arquivo, 'rb') as f:
                    hash_arquivo = hash(f.read())
                    arquivos_hash[hash_arquivo].append(caminho_arquivo)
            except Exception as e:
                logging.error(f"Erro ao calcular hash do arquivo {caminho_arquivo}: {e}")

    for hash_arquivo, arquivos in arquivos_hash.items():
        if len(arquivos) > 1:
            arquivos_duplicados[hash_arquivo] = arquivos

    return arquivos_duplicados

def sugerir_arquivos_temporarios(caminho):
    arquivos_sugeridos = []

    for raiz, _, arquivos in os.walk(caminho):
        for arquivo in arquivos:
            if any(arquivo.lower().endswith(ext) for ext in EXTENSOES_IGNORADAS):
                arquivos_sugeridos.append(os.path.join(raiz, arquivo))

    return arquivos_sugeridos

def sugerir_arquivos_nao_necessarios(caminho):
    arquivos_sugeridos = []

    for raiz, _, arquivos in os.walk(caminho):
        for arquivo in arquivos:
            if any(arquivo.lower().endswith(ext) for ext in EXTENSOES_NECESSARIAS):
                arquivos_sugeridos.append(os.path.join(raiz, arquivo))

    return arquivos_sugeridos

def sugerir_arquivos_tamanho_anomalo(caminho):
    arquivos_sugeridos = []

    for raiz, _, arquivos in os.walk(caminho):
        for arquivo in arquivos:
            caminho_arquivo = os.path.join(raiz, arquivo)
            try:
                tamanho = os.path.getsize(caminho_arquivo)
                if TAMANHO_LIMITE_ANOMALO_MIN < tamanho < TAMANHO_LIMITE_ANOMALO_MAX:
                    arquivos_sugeridos.append((caminho_arquivo, tamanho))
            except Exception as e:
                logging.error(f"Erro ao verificar tamanho do arquivo {caminho_arquivo}: {e}")

    return arquivos_sugeridos

def listar_arquivos_para_deletar(arquivos_para_deletar):
    tree = Tree("[bold red]📂 Arquivos para Deletar[/]")
    for arquivo in arquivos_para_deletar:
        tamanho = os.path.getsize(arquivo)
        tamanho_formatado = format_tamanho(tamanho)
        node = f"📄 [cyan]{os.path.relpath(arquivo)}[/] {tamanho_formatado}"
        tree.add(node)
    return tree

def deletar_arquivos(arquivos_para_deletar):
    for arquivo in arquivos_para_deletar:
        try:
            os.remove(arquivo)
            console.print(f"[bold green]Deletado:[/] {os.path.relpath(arquivo)}")
        except Exception as e:
            logging.error(f"Erro ao deletar arquivo {arquivo}: {e}")

def criar_relatorio_pdf(caminho, arquivos_para_deletar):
    doc = SimpleDocTemplate("relatorio.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    content = []

    # Adiciona título
    content.append(Paragraph("Relatório de Análise de Disco", styles['Title']))

    # Resumo do uso do disco
    total_usado, _, total_livre = disk_usage(caminho)
    content.append(Paragraph(f"Total usado no disco: {format_tamanho(total_usado)}", styles['Normal']))
    content.append(Paragraph(f"Total livre no disco: {format_tamanho(total_livre)}", styles['Normal']))

    # Pastas e arquivos mais pesados
    content.append(Paragraph("Pastas e Arquivos Mais Pesados:", styles['Heading2']))
    tree = listar_arquivos(caminho, exibir_todos=True)
    content.append(Paragraph(str(tree), styles['Normal']))

    # Sugestões para deletar
    if arquivos_para_deletar:
        content.append(Paragraph("Arquivos Sugestionados para Deletar:", styles['Heading2']))
        for arquivo in arquivos_para_deletar:
            tamanho = os.path.getsize(arquivo)
            content.append(Paragraph(f"{os.path.relpath(arquivo)} - {format_tamanho(tamanho)}", styles['Normal']))

    # Gráfico de distribuição do espaço em disco
    plt.figure(figsize=(8, 4))
    labels = ['Usado', 'Livre']
    sizes = [total_usado, total_livre]
    colors = ['#ff9999','#66b3ff']
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')
    plt.savefig("grafico_distribuicao.png")
    plt.close()

    content.append(Paragraph("Gráfico de Distribuição do Espaço em Disco:", styles['Heading2']))
    content.append(Image("grafico_distribuicao.png"))

    doc.build(content)

def main():
    parser = argparse.ArgumentParser(description="Analisador de Disco")
    parser.add_argument("caminho", type=str, help="Caminho do diretório a ser analisado")
    parser.add_argument("--todos", action="store_true", help="Exibir todas as pastas e arquivos")
    args = parser.parse_args()

    clear_terminal()
    console.print(f"[bold yellow]Iniciando análise no diretório:[/] [cyan]{args.caminho}[/]")

    if not os.path.isdir(args.caminho):
        console.print("[bold red]Erro:[/] O caminho fornecido não é um diretório válido.")
        exit(1)

    progress_bar = tqdm(total=0, desc="Processando", dynamic_ncols=True)
    console.print("[bold yellow]📝 Analisando diretório...[/]")
    tree = listar_arquivos(args.caminho, exibir_todos=args.todos, progress_bar=progress_bar)
    progress_bar.close()

    clear_terminal()
    console.print("[bold cyan]✅ ANÁLISE COMPLETA[/]\n")
    console.print("[bold yellow]🌳 GERANDO RELATÓRIO DE ÁRVORE:[/]")
    console.print(tree)

    console.print("\n[bold cyan]🔍 GERANDO DETALHES[/]\n")
    obter_detalhes(args.caminho)

if __name__ == "__main__":
    main()
