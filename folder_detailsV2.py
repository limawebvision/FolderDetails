import os
from colorama import init, Fore, Style
from datetime import datetime, timedelta
from collections import defaultdict
from shutil import disk_usage
from tqdm import tqdm
import argparse

global tree_relatorio
tree_relatorio = ""

init(autoreset=True)

def listar_arquivos(caminho, nivel=0, exibir_todos=False, progress_bar=None):
    global tree_relatorio

    arquivos_pastas_tamanhos = []
    try:
        for item in os.listdir(caminho):
            try:
                caminho_completo = os.path.join(caminho, item)
                emoji = '📄' if os.path.isfile(caminho_completo) else '📁'
                tamanho = os.path.getsize(caminho_completo) if os.path.isfile(caminho_completo) else tamanho_pasta_raiz(caminho_completo)
                arquivos_pastas_tamanhos.append((item, tamanho, emoji))
                progress_bar.update(1)
            except:
                continue
    except:
        None


    arquivos_pastas_tamanhos = sorted(arquivos_pastas_tamanhos, key=lambda x: x[1], reverse=True)

    for nome, tamanho, emoji in arquivos_pastas_tamanhos:
        tamanho_formatado = format_tamanho(tamanho)
        cor = Fore.BLUE if emoji == '📁' else Fore.GREEN
        tree_relatorio += f"{'    ' * nivel}{cor}{emoji} {nome:<50} {tamanho_formatado}\n"

        if emoji == '📁' and (exibir_todos or nivel == 0):
            listar_arquivos(os.path.join(caminho, nome), nivel + 1, exibir_todos)

def tamanho_pasta_raiz(caminho):
    tamanho_total = 0
    for raiz, _, arquivos in os.walk(caminho):
        tamanho_total += sum(os.path.getsize(os.path.join(raiz, arquivo)) for arquivo in arquivos)
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

    for raiz, pastas, arquivos in os.walk(caminho):
        try:
            total_pastas += len(pastas)
            total_arquivos += len(arquivos)
        except:
            continue

        for arquivo in arquivos:
            try:
                caminho_arquivo = os.path.join(raiz, arquivo)
                ultima_modificacao = os.path.getmtime(caminho_arquivo)
                ultimo_acesso[arquivo] = max(ultimo_acesso[arquivo], datetime.fromtimestamp(ultima_modificacao))
            except:
                continue

    total_usado, _, total_livre = disk_usage(caminho)

    total_usado_formatado = format_tamanho(total_usado)
    total_livre_formatado = format_tamanho(total_livre)

    print(Fore.YELLOW + f"\n📊 Detalhes do Diretório:")
    print(f"  • Total usado no disco: {total_usado_formatado}")
    print(f"  • Total livre no disco: {total_livre_formatado}")
    print(f"  • Total de pastas: {total_pastas}")
    print(f"  • Total de arquivos: {total_arquivos}")

    ask_recom = input("Gostaria de recomendações de arquivos para deletar? (s/n): ")
    if ask_recom.lower() in ["sim", "s"]:
        print(Fore.YELLOW + "\n🗑️ Recomendações de Arquivos para Deletar:")
        hoje = datetime.now()
        limite_dias = 30
        try:
            for raiz, pastas, arquivos in os.walk(caminho):
                try:
                    for arquivo in arquivos:
                        try:
                            caminho_arquivo = os.path.join(raiz, arquivo)
                            ultima_modificacao = os.path.getmtime(caminho_arquivo)
                            if (hoje - datetime.fromtimestamp(ultima_modificacao)) > timedelta(days=limite_dias):
                                print(f"  • {Fore.CYAN + '📄 ' + os.path.relpath(raiz, caminho)} {Fore.RESET}/{Fore.GREEN + arquivo + Fore.RESET} (Última modificação: {datetime.fromtimestamp(ultima_modificacao).strftime('%Y-%m-%d')})")
                        except:
                            continue

                    for pasta in pastas:
                        try:
                            print(f"  • {Fore.CYAN + '📁 ' + os.path.relpath(raiz, caminho)} {Fore.RESET}/{Fore.YELLOW + pasta + Fore.RESET}")
                        except:
                            continue
                except:
                    continue
        except:
            None

def parse_args():
    parser = argparse.ArgumentParser(description='Exibe a estrutura de árvore de um diretório com detalhes.')
    parser.add_argument('caminho', type=str, help='O caminho para o diretório ou disco a ser analisado')
    parser.add_argument('--all', action='store_true', help='Exibe todos os arquivos e pastas, incluindo subpastas')
    return parser.parse_args()

def main():
    args = parse_args()
    caminho = args.caminho

    clear_terminal()

    with tqdm(desc="Obtendo lista de arquivos e calculando tamanhos", unit="file") as progress_bar:
        listar_arquivos(caminho, exibir_todos=args.all, progress_bar=progress_bar)

    print(Fore.CYAN + "✅ ANÁLISE COMPLETA\n")
    print(Fore.YELLOW + "🌳 GERANDO RELATORIO DE ARVORE:")

    print(tree_relatorio)

    print(Fore.CYAN + "\n\n🔍 GERANDO DETALHES\n")
    obter_detalhes(caminho)

if __name__ == "__main__":

    print("Made with 💟 By LIMA")
    print("GITHUB: https://github.com/limawebvision/FolderDetails")
    main()
