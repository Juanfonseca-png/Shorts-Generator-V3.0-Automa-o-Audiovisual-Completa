import os
import time
import requests
import urllib.parse

def gerar_imagens_cenas(prompts: list[str], pasta_saida: str, progress_callback=None) -> list[str]:
    os.makedirs(pasta_saida, exist_ok=True)
    imagens_geradas = []
    total = len(prompts)
    
    for i, prompt in enumerate(prompts, start=1):
        safe_prompt = urllib.parse.quote(prompt[:800] + ", vertical 9:16 aspect ratio, dark cinematic horror, no text")
        url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=720&height=1280&nologo=true"
        nome_arquivo = os.path.join(pasta_saida, f"imagem_{i:02d}.jpg")
        
        tentativas = 0
        sucesso = False
        while tentativas < 3 and not sucesso:
            try:
                response = requests.get(url, timeout=60)
                if response.status_code == 200:
                    with open(nome_arquivo, 'wb') as f:
                        f.write(response.content)
                    imagens_geradas.append(nome_arquivo)
                    sucesso = True
            except Exception:
                pass
            
            if not sucesso:
                tentativas += 1
                time.sleep(2)
                
        if progress_callback:
            progress_callback(i, total)
            
    return imagens_geradas

# ✅ MELHORIA 11 — Gerador de Thumbnail via API
def gerar_thumbnail(prompt: str, largura: int, altura: int):
    pasta_saida = "outputs"
    os.makedirs(pasta_saida, exist_ok=True)
    
    safe_prompt = urllib.parse.quote(prompt[:800] + ", high quality, youtube thumbnail, detailed, no text")
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width={largura}&height={altura}&nologo=true"
    nome_arquivo = os.path.join(pasta_saida, f"thumbnail_{int(time.time())}.jpg")
    
    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            with open(nome_arquivo, 'wb') as f:
                f.write(response.content)
            return nome_arquivo
        raise Exception(f"Status Code {response.status_code}")
    except Exception as e:
        raise Exception(f"Falha ao gerar Thumbnail: {str(e)}")