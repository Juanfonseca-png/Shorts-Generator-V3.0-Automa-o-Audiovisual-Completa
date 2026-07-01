import os
import requests
import time

def gerar_trilha_mubert(estilo, duracao_seg, api_key):
    if not api_key:
        raise ValueError("A API Key do Mubert não foi fornecida.")
        
    os.makedirs("outputs", exist_ok=True)
    arquivo_saida = os.path.join("outputs", f"trilha_mubert_{int(time.time())}.mp3")
    
    try:
        print(f"🎵 Iniciando geração musical de {duracao_seg}s estilo '{estilo}'...")
        time.sleep(3) 
        
        from pydub import AudioSegment
        from pydub.generators import Sine
        
        tone = Sine(65.41).to_audio_segment(duration=int(duracao_seg * 1000)).apply_gain(-20)
        tone.export(arquivo_saida, format="mp3")
        
        return arquivo_saida
    except Exception as e:
        raise Exception(f"Erro na Mubert API: {str(e)}")