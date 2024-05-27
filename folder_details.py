import os
import shutil
from operator import itemgetter

def tamanho_arquivos(caminho):

    arquivos_pastas_tamanhos = []

    for item in os.listdir(caminho):
        try:
            caminho_completo = os.path.join(caminho, item)

            if os.path.isfile(caminho_completo):
                tamanho = os.path.getsize(caminho_completo)
                arquivos_pastas_tamanhos.append((item, tamanho))

            elif os.path.isdir(caminho_completo):
                tamanho_pasta = tamanho_pasta_raiz(caminho_completo)
                arquivos_pastas_tamanhos.append((item, tamanho_pasta))
        except:
            continue


    arquivos_pastas_tamanhos = sorted(arquivos_pastas_tamanhos, key=itemgetter(1), reverse=True)


    print(f"{'Nome':<50} {'Tamanho':>10}")
    print("="*60)
    total_usado = 0
    for nome, tamanho in arquivos_pastas_tamanhos:
        try:
            tamanho_formatado = format_tamanho(tamanho)
            print(f"{nome:<50} {tamanho_formatado:>10}")
            total_usado += tamanho
        except:
            continue

    total_formatado = format_tamanho(total_usado)
    print("="*60)
    print(f"Total usado pelo caminho: {total_formatado}")


    total, usado, livre = shutil.disk_usage(caminho)
    total_formatado = format_tamanho(total)
    livre_formatado = format_tamanho(livre)
    print(f"Espaço total no disco: {total_formatado}")
    print(f"Espaço disponível no disco: {livre_formatado}")

def tamanho_pasta_raiz(caminho):

    tamanho_total = 0
    for raiz, pastas, arquivos in os.walk(caminho):
        try:
            try:
                for arquivo in arquivos:
                    caminho_arquivo = os.path.join(raiz, arquivo)
                    tamanho_total += os.path.getsize(caminho_arquivo)
            except:
                continue
        except:
            continue
    return tamanho_total

def format_tamanho(tamanho_bytes):
    if tamanho_bytes < 1024:
        return f"{tamanho_bytes} bytes"
    elif tamanho_bytes < 1024 ** 2:
        return f"{tamanho_bytes / 1024:.2f} KB"
    elif tamanho_bytes < 1024 ** 3:
        return f"{tamanho_bytes / (1024 ** 2):.2f} MB"
    else:
        return f"{tamanho_bytes / (1024 ** 3):.2f} GB"

print("Made with 💟 By LIMA")
print("GITHUB: https://github.com/Henrique3h0")
caminho = input("Digite o caminho para o diretório ou disco: ")
print(f"ANALISANDO {caminho}")
tamanho_arquivos(caminho)
