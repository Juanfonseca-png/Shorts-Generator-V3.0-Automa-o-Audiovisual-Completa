import os
import PIL.Image
import subprocess
import shutil
from moviepy.editor import ImageClip, AudioFileClip, VideoFileClip, concatenate_videoclips, CompositeAudioClip
from modules.video_fx_engine import aplicar_efeitos_visuais, aplicar_marca_dagua, aplicar_barra_progresso

if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

import moviepy.video.fx.all as vfx

def listar_midias_ordenadas(pasta: str, por_data: bool = False) -> list[str]:
    if not os.path.exists(pasta): return []
    arquivos = [os.path.join(pasta, f) for f in os.listdir(pasta) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.mp4', '.mov', '.avi', '.webm'))]
    if por_data: return sorted(arquivos, key=lambda x: os.path.getctime(x))
    return sorted(arquivos, key=lambda x: os.path.basename(x))

def get_target_dims(formato: str):
    return (1280, 720) if "16:9" in formato else (720, 1280)

def aplicar_movimento_ken_burns(clip, index, ativar_efeitos, formato, velocidade, intensidade):
    target_w, target_h = get_target_dims(formato)
    w, h = clip.size
    ratio_clip = w / h
    ratio_target = target_w / target_h

    if ratio_clip > ratio_target: clip = clip.resize(height=target_h)
    else: clip = clip.resize(width=target_w)

    if not ativar_efeitos:
        w, h = clip.size
        clip = clip.crop(x_center=w/2, y_center=h/2, width=target_w, height=target_h)
        return clip

    w, h = clip.size
    movimento = index % 4

    if movimento == 0: 
        def zoom_in(get_frame, t):
            progress = min((t / clip.duration) * velocidade, 1.0)
            fator = 1.0 + (0.1 * intensidade * progress)
            frame = clip.get_frame(t)
            import numpy as np
            from PIL import Image
            img = Image.fromarray(frame)
            new_w, new_h = int(w * fator), int(h * fator)
            img = img.resize((new_w, new_h), PIL.Image.LANCZOS)
            left = max(0, (new_w - target_w) / 2)
            top = max(0, (new_h - target_h) / 2)
            return np.array(img.crop((left, top, left + target_w, top + target_h)))
        return clip.fl(zoom_in)
        
    elif movimento == 1: 
        def zoom_out(get_frame, t):
            progress = min((t / clip.duration) * velocidade, 1.0)
            fator_max = 1.0 + (0.1 * intensidade)
            fator = fator_max - (0.1 * intensidade * progress)
            frame = clip.get_frame(t)
            import numpy as np
            from PIL import Image
            img = Image.fromarray(frame)
            new_w, new_h = int(w * fator), int(h * fator)
            img = img.resize((new_w, new_h), PIL.Image.LANCZOS)
            left = max(0, (new_w - target_w) / 2)
            top = max(0, (new_h - target_h) / 2)
            return np.array(img.crop((left, top, left + target_w, top + target_h)))
        return clip.fl(zoom_out)
        
    elif movimento == 2: 
        fator_fixo = 1.0 + (0.2 * intensidade)
        new_w, new_h = int(w * fator_fixo), int(h * fator_fixo)
        def pan_right(get_frame, t):
            progress = min((t / clip.duration) * velocidade, 1.0)
            frame = clip.get_frame(t)
            import numpy as np
            from PIL import Image
            img = Image.fromarray(frame).resize((new_w, new_h), PIL.Image.LANCZOS)
            max_x = max(0, new_w - target_w)
            current_x = max_x * progress
            top = max(0, (new_h - target_h) / 2)
            return np.array(img.crop((current_x, top, current_x + target_w, top + target_h)))
        return clip.fl(pan_right)
        
    elif movimento == 3: 
        fator_fixo = 1.0 + (0.2 * intensidade)
        new_w, new_h = int(w * fator_fixo), int(h * fator_fixo)
        def pan_left(get_frame, t):
            progress = min((t / clip.duration) * velocidade, 1.0)
            frame = clip.get_frame(t)
            import numpy as np
            from PIL import Image
            img = Image.fromarray(frame).resize((new_w, new_h), PIL.Image.LANCZOS)
            max_x = max(0, new_w - target_w)
            current_x = max_x - (max_x * progress)
            top = max(0, (new_h - target_h) / 2)
            return np.array(img.crop((current_x, top, current_x + target_w, top + target_h)))
        return clip.fl(pan_left)

def aplicar_transicao(clip, tipo_transicao, duracao):
    if not tipo_transicao: return clip
    if tipo_transicao == "Fade to Black": return clip.fadeout(duracao).fadein(duracao)
    elif tipo_transicao == "Fade to White": return clip.fadein(duracao, color=[255,255,255]).fadeout(duracao, color=[255,255,255])
    return clip

def aplicar_overlay_texto(clip_video, fala_texto, estilo, tamanho, posicao, duracao_audio):
    if not fala_texto: return clip_video
    
    color, stroke_color = 'white', 'black'
    if "Amarelo" in estilo: color = 'yellow'
    elif "Horror" in estilo: color = 'red'; stroke_color = 'black'
    elif "Neon" in estilo: color = '#39FF14'
    
    y_pos = 'bottom'
    if "Centro" in posicao: y_pos = 'center'
    elif "Superior" in posicao: y_pos = 0.2
    elif "Inferior" in posicao: y_pos = 0.8
    
    palavras = fala_texto.split()
    if not palavras: return clip_video
    
    def contar_vogais(w):
        return sum(1 for c in w.lower() if c in 'aeiouáéíóúâêîôûãõ') or 1
        
    total_vogais = sum(contar_vogais(w) for w in palavras)
    
    from moviepy.editor import TextClip, CompositeVideoClip
    text_clips = []
    current_time = 0.0
    
    for w in palavras:
        peso_palavra = contar_vogais(w)
        duracao_palavra = (peso_palavra / total_vogais) * duracao_audio
        try:
            txt_clip = TextClip(w, fontsize=tamanho, color=color, stroke_color=stroke_color, stroke_width=2, font="Arial-Bold")
            pos = ('center', clip_video.size[1] * y_pos) if isinstance(y_pos, float) else ('center', y_pos)
            txt_clip = txt_clip.set_position(pos).set_start(current_time).set_duration(duracao_palavra)
            text_clips.append(txt_clip)
        except: pass
        current_time += duracao_palavra
        
    if text_clips: return CompositeVideoClip([clip_video] + text_clips)
    return clip_video

def montar_video(lista_midias, lista_audios, output_path, ativar_efeitos, formato, intensidade, velocidade, kwargs_melhorias=None):
    if kwargs_melhorias is None: kwargs_melhorias = {}
    
    if len(lista_midias) < len(lista_audios):
        while len(lista_midias) < len(lista_audios): lista_midias.append(lista_midias[-1]) 
    elif len(lista_midias) > len(lista_audios):
        lista_midias = lista_midias[:len(lista_audios)]

    clips = []
    lista_falas = kwargs_melhorias.get("falas", [])
    
    for idx, (audio_path, midia_path) in enumerate(zip(lista_audios, lista_midias)):
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        extensao = midia_path.lower().split('.')[-1]
        
        if extensao in ['mp4', 'mov', 'avi', 'mkv', 'webm']:
            vid_clip = VideoFileClip(midia_path).without_audio()
            if vid_clip.duration < duration: vid_clip = vid_clip.fx(vfx.loop, duration=duration)
            else: vid_clip = vid_clip.subclip(0, duration)
            clip_final = aplicar_movimento_ken_burns(vid_clip, idx, ativar_efeitos, formato, velocidade, intensidade)
        else:
            img_clip = ImageClip(midia_path).set_duration(duration)
            clip_final = aplicar_movimento_ken_burns(img_clip, idx, ativar_efeitos, formato, velocidade, intensidade)
            
        if kwargs_melhorias.get("ativar_transicoes"):
            clip_final = aplicar_transicao(clip_final, kwargs_melhorias.get("tipo_transicao"), kwargs_melhorias.get("dur_transicao"))
            
        if kwargs_melhorias.get("ativar_overlay_texto") and idx < len(lista_falas):
            fala = lista_falas[idx]
            clip_final = aplicar_overlay_texto(clip_final, fala, kwargs_melhorias.get("overlay_estilo"), kwargs_melhorias.get("overlay_tam"), kwargs_melhorias.get("overlay_pos"), duration)
            
        clip_final = clip_final.set_audio(audio_clip)
        clips.append(clip_final)
        
    video_final = concatenate_videoclips(clips, method="compose")
    
    # M21-25: Processamento Matricial (Filtros e Efeitos Pesados)
    if not kwargs_melhorias.get("preview_mode"):
        video_final = aplicar_efeitos_visuais(video_final, kwargs_melhorias)
    
    # M19-20: Overlays de UI
    if kwargs_melhorias.get('chk_marca'):
        video_final = aplicar_marca_dagua(video_final, kwargs_melhorias.get('texto_marca'), kwargs_melhorias.get('pos_marca'))
    if kwargs_melhorias.get('chk_barra'):
        video_final = aplicar_barra_progresso(video_final, kwargs_melhorias.get('cor_barra'))
    
    if kwargs_melhorias.get("trilha_bg") and os.path.exists(kwargs_melhorias.get("trilha_bg")):
        musica_clip = AudioFileClip(kwargs_melhorias.get("trilha_bg")).volumex(kwargs_melhorias.get("vol_bg", 0.15))
        if musica_clip.duration < video_final.duration: musica_clip = musica_clip.fx(vfx.loop, duration=video_final.duration)
        else: musica_clip = musica_clip.subclip(0, video_final.duration)
        audio_misturado = CompositeAudioClip([video_final.audio, musica_clip])
        video_final = video_final.set_audio(audio_misturado)

    temp_output = output_path.replace(".mp4", "_temp.mp4")
    if kwargs_melhorias.get("preview_mode"): video_final = video_final.resize(0.5)

    # M26: Compressão Customizada
    bitrate_str = kwargs_melhorias.get("compressao_bitrate", "5000k").split(" ")[0]
    
    video_final.write_videofile(temp_output, fps=24, codec="libx264", audio_codec="aac", bitrate=bitrate_str, logger=None)
    
    for c in clips: c.close()
    video_final.close()
    
    srt_path = kwargs_melhorias.get("srt_path")
    if kwargs_melhorias.get("queimar_legenda") and srt_path and os.path.exists(srt_path):
        estilo, tamanho = kwargs_melhorias.get("srt_estilo", "Branca simples"), kwargs_melhorias.get("srt_tamanho", 40)
        cor_p, cor_b = "&H00FFFFFF", "&H00000000"
        if "Amarela" in estilo: cor_p = "&H0000FFFF"
        elif "Horror" in estilo: cor_p = "&H000000FF"; cor_b = "&H00000000"
        elif "Neon" in estilo: cor_p = "&H0000FF00"
        
        srt_fmt = srt_path.replace("\\", "/")
        style_str = f"Fontsize={tamanho},PrimaryColour={cor_p},OutlineColour={cor_b},Bold=-1"
        try:
            subprocess.run(["ffmpeg", "-y", "-i", temp_output, "-vf", f"subtitles='{srt_fmt}':force_style='{style_str}'", "-c:a", "copy", output_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.remove(temp_output)
        except Exception as e:
            print(f"Erro ffmpeg: {e}. Salvando sem legenda.")
            os.rename(temp_output, output_path)
    else:
        os.rename(temp_output, output_path)

    # M27: Limpeza de Cache de Render
    if kwargs_melhorias.get("chk_cleanup"):
        prev_dir = os.path.join("outputs", "previews")
        if os.path.exists(prev_dir):
            try: 
                shutil.rmtree(prev_dir)
                os.makedirs(prev_dir)
            except: pass