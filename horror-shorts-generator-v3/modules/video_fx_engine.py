import numpy as np
import random
from moviepy.editor import CompositeVideoClip

# ==========================================
# MELHORIAS 21 a 25: EFEITOS MATRICIAIS (Numpy)
# ==========================================
def aplicar_cor_forte(frame, sat, cont):
    f = frame.astype(float)
    f = (f - 128) * cont + 128
    lum = np.dot(f[..., :3], [0.299, 0.587, 0.114])
    for i in range(3):
        f[..., i] = lum + (f[..., i] - lum) * sat
    return np.clip(f, 0, 255).astype(np.uint8)

def aplicar_cromatico(frame, shift):
    r = np.roll(frame[..., 0], shift, axis=1)
    b = np.roll(frame[..., 2], -shift, axis=1)
    return np.dstack((r, frame[..., 1], b))

def aplicar_glitch(frame, intensity):
    if random.random() > 0.9: # 10% de chance de glitch por frame
        shift = random.randint(-intensity, intensity)
        frame = np.roll(frame, shift, axis=1)
        y = random.randint(0, max(1, frame.shape[0] - 20))
        frame[y:y+20, :, 1] = 255 # Linha de ruído verde clássica
    return frame

def aplicar_shake(frame, intensity):
    dx = random.randint(-intensity, intensity)
    dy = random.randint(-intensity, intensity)
    return np.roll(np.roll(frame, dx, axis=1), dy, axis=0)

def aplicar_vinheta(frame, intensity):
    h, w = frame.shape[:2]
    Y, X = np.ogrid[:h, :w]
    dist = np.sqrt((X - w/2)**2 + (Y - h/2)**2)
    max_dist = np.sqrt((w/2)**2 + (h/2)**2)
    mask = 1 - (dist / max_dist) * intensity
    mask = np.clip(mask, 0, 1)
    return np.clip(frame * mask[..., np.newaxis], 0, 255).astype(np.uint8)

def processar_frame(frame, efeitos):
    """Pipeline de renderização que empilha todos os filtros ativos num único passe."""
    if efeitos.get('cor'):
        frame = aplicar_cor_forte(frame, efeitos['sat'], efeitos['cont'])
    if efeitos.get('croma'):
        frame = aplicar_cromatico(frame, efeitos['croma_shift'])
    if efeitos.get('glitch'):
        frame = aplicar_glitch(frame, efeitos['glitch_int'])
    if efeitos.get('shake'):
        frame = aplicar_shake(frame, efeitos['shake_int'])
    if efeitos.get('vinheta'):
        frame = aplicar_vinheta(frame, efeitos['vinheta_int'])
    return frame

def aplicar_efeitos_visuais(clip, kwargs_melhorias):
    efeitos = {}
    if kwargs_melhorias.get('chk_cor'):
        efeitos['cor'] = True; efeitos['sat'] = kwargs_melhorias.get('cor_sat', 1.5); efeitos['cont'] = kwargs_melhorias.get('cor_cont', 1.2)
    if kwargs_melhorias.get('chk_croma'):
        efeitos['croma'] = True; efeitos['croma_shift'] = kwargs_melhorias.get('croma_shift', 5)
    if kwargs_melhorias.get('chk_glitch'):
        efeitos['glitch'] = True; efeitos['glitch_int'] = kwargs_melhorias.get('glitch_int', 10)
    if kwargs_melhorias.get('chk_shake'):
        efeitos['shake'] = True; efeitos['shake_int'] = kwargs_melhorias.get('shake_int', 5)
    if kwargs_melhorias.get('chk_vinheta'):
        efeitos['vinheta'] = True; efeitos['vinheta_int'] = kwargs_melhorias.get('vinheta_int', 0.5)

    if not efeitos:
        return clip

    return clip.fl_image(lambda f: processar_frame(f, efeitos))

# ==========================================
# MELHORIAS 19 e 20: OVERLAYS DE UI NO VÍDEO
# ==========================================
def aplicar_marca_dagua(clip, texto, pos="bottom-right"):
    from moviepy.editor import TextClip
    try:
        txt = TextClip(texto, fontsize=40, color='white', font='Arial-Bold').set_opacity(0.4)
        margin = 25
        w, h = clip.size
        if pos == "bottom-right": txt = txt.set_position((w - txt.w - margin, h - txt.h - margin))
        elif pos == "top-left": txt = txt.set_position((margin, margin))
        else: txt = txt.set_position(("center", h - txt.h - margin))
            
        txt = txt.set_duration(clip.duration)
        return CompositeVideoClip([clip, txt])
    except Exception as e:
        print(f"Aviso: Não foi possível aplicar a marca d'água (Requer ImageMagick configurado). {e}")
        return clip

def aplicar_barra_progresso(clip, cor, altura=15):
    w, h = clip.size
    color_map = {"Vermelho": (255,0,0), "Branco": (255,255,255), "Amarelo": (255,255,0), "Verde": (0,255,0)}
    rgb = color_map.get(cor, (255,255,255))
    
    def make_frame(t):
        progress = t / clip.duration
        current_w = max(1, int(w * progress))
        frame = np.zeros((altura, w, 3), dtype=np.uint8)
        frame[:, :current_w] = rgb
        return frame
        
    from moviepy.video.VideoClip import VideoClip
    bar_clip = VideoClip(make_frame, duration=clip.duration).set_position(("center", "bottom"))
    return CompositeVideoClip([clip, bar_clip])