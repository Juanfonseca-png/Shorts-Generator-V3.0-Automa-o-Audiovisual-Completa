import os
from pydub import AudioSegment
from pydub.generators import WhiteNoise

def aplicar_efeito_radio(audio_path, int_ruido=0.01, freq_grave=300, freq_agudo=3400):
    """
    ✅ MELHORIA 15 — Efeito de Áudio: Rádio FM
    Aplica filtros passa-alta e passa-baixa e sobrepõe ruído branco para simular um rádio antigo/comunicador.
    """
    try:
        sound = AudioSegment.from_file(audio_path)
        
        # Corta frequências muito graves e muito agudas (efeito "telefone")
        sound = sound.high_pass_filter(freq_grave)
        sound = sound.low_pass_filter(freq_agudo)
        
        # Gera ruído branco da exata duração do áudio
        noise = WhiteNoise().to_audio_segment(duration=len(sound))
        
        # Ajuste de ganho (0.01 a 0.05 mapeado para db negativos de forma logarítmica/aproximada)
        # -40dB é bem baixo, -20dB é bem alto.
        gain = -40 + (int_ruido * 400) 
        noise = noise.apply_gain(gain)
        
        # Mistura o áudio processado com o ruído
        mixed = sound.overlay(noise)
        mixed.export(audio_path, format="mp3")
        
    except Exception as e:
        print(f"❌ Erro ao aplicar efeito de rádio FM: {e}")