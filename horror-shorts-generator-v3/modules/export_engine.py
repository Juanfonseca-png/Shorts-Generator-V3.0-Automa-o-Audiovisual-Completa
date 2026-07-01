import os
import json
import zipfile
from datetime import datetime
from moviepy.editor import AudioFileClip

def timestamp_str():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def salvar_json(data):
    os.makedirs("outputs", exist_ok=True)
    path = f"outputs/horror_roteiro_{timestamp_str()}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path

def salvar_txt(data):
    os.makedirs("outputs", exist_ok=True)
    path = f"outputs/horror_roteiro_{timestamp_str()}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2))
    return path

def criar_zip(json_path, txt_path, audio_paths):
    ts = timestamp_str()
    zip_path = os.path.join("outputs", f"export_completo_{ts}.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        if json_path and os.path.exists(json_path): zipf.write(json_path, os.path.basename(json_path))
        if txt_path and os.path.exists(txt_path): zipf.write(txt_path, os.path.basename(txt_path))
        for file in audio_paths:
            if os.path.exists(file): zipf.write(file, os.path.basename(file))
    return zip_path

def criar_zip_audios(audio_paths):
    ts = timestamp_str()
    zip_path = os.path.join("outputs", f"apenas_audios_{ts}.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in audio_paths:
            if os.path.exists(file): zipf.write(file, os.path.basename(file))
    return zip_path

def formatar_tempo_srt(segundos):
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = int(segundos % 60)
    ms = int((segundos - int(segundos)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def gerar_srt(audio_files, falas):
    srt_path = os.path.join("outputs", f"legenda_{timestamp_str()}.srt")
    tempo_atual = 0.0
    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, (audio_path, fala) in enumerate(zip(audio_files, falas), start=1):
            if not os.path.exists(audio_path): continue
            clip = AudioFileClip(audio_path)
            duracao = clip.duration
            clip.close()
            inicio_srt = formatar_tempo_srt(tempo_atual)
            fim_srt = formatar_tempo_srt(tempo_atual + duracao)
            f.write(f"{idx}\n")
            f.write(f"{inicio_srt} --> {fim_srt}\n")
            f.write(f"{fala}\n\n")
            tempo_atual += duracao
    return srt_path

# ✅ MELHORIA 18 — Exportar como Pacote CapCut
def exportar_capcut(json_path, txt_path, audio_paths, image_paths):
    if not json_path or not os.path.exists(json_path): 
        raise ValueError("Roteiro JSON não encontrado.")
        
    ts = timestamp_str()
    zip_path = os.path.join("outputs", f"pacote_capcut_{ts}.zip")
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        # Imagens
        for i, img in enumerate(image_paths):
            if img and os.path.exists(img):
                ext = img.split('.')[-1]
                zipf.write(img, f"capcut_package/imagens/cena_{i+1:03d}.{ext}")
        # Áudios
        for i, aud in enumerate(audio_paths):
            if aud and os.path.exists(aud):
                zipf.write(aud, f"capcut_package/audios/cena_{i+1:03d}.mp3")
        # Roteiro Textual
        if txt_path and os.path.exists(txt_path):
            zipf.write(txt_path, "capcut_package/roteiro.txt")
            
        # Instruções de Uso
        readme_content = (
            "=========================================\n"
            "   INSTRUÇÕES DE MONTAGEM NO CAPCUT\n"
            "=========================================\n\n"
            "1. Arraste todos os arquivos da pasta 'audios' para a linha do tempo principal.\n"
            "2. Arraste todos os arquivos da pasta 'imagens' para a faixa de vídeo acima dos áudios.\n"
            "3. Estique ou corte a duração de cada imagem para que seu tamanho se alinhe perfeitamente com o áudio correspondente abaixo dela.\n"
            "4. Selecione as imagens e aplique o efeito de 'Zoom 3D' do CapCut para o toque final!\n"
        )
        readme_path = os.path.join("outputs", f"temp_readme_{ts}.txt")
        with open(readme_path, "w", encoding="utf-8") as f: 
            f.write(readme_content)
        zipf.write(readme_path, "capcut_package/README.txt")
        os.remove(readme_path)
        
    return zip_path