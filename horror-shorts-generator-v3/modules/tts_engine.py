import edge_tts
import asyncio
import os
import time

VOZES = {
    "antonio": {"desc": "Antônio (Masculino | Adulto/Grave)", "voice": "pt-BR-AntonioNeural"},
    "donato": {"desc": "Donato (Masculino | Formal/Sério)", "voice": "pt-BR-DonatoNeural"},
    "fabio": {"desc": "Fábio (Masculino | Jovem/Dinâmico)", "voice": "pt-BR-FabioNeural"},
    "humberto": {"desc": "Humberto (Masculino | Padrão/Energético)", "voice": "pt-BR-HumbertoNeural"},
    "julio": {"desc": "Júlio (Masculino | Aveludado)", "voice": "pt-BR-JulioNeural"},
    "francisca": {"desc": "Francisca (Feminina | Jovem/Amigável)", "voice": "pt-BR-FranciscaNeural"},
    "elza": {"desc": "Elza (Feminina | Madura/Professoral)", "voice": "pt-BR-ElzaNeural"},
    "giovanna": {"desc": "Giovanna (Feminina | Natural/Conversa)", "voice": "pt-BR-GiovannaNeural"},
    "leila": {"desc": "Leila (Feminina | Suave/Delicada)", "voice": "pt-BR-LeilaNeural"},
    "leticia": {"desc": "Letícia (Feminina | Clara/Curiosidades)", "voice": "pt-BR-LeticiaNeural"},
    "brenda": {"desc": "Brenda (Feminina | Firme/Energética)", "voice": "pt-BR-BrendaNeural"},
    "jenny": {"desc": "Jenny (Multilingual | Feminina Premium)", "voice": "en-US-JennyMultilingualNeural"},
    "ryan": {"desc": "Ryan (Multilingual | Masculino Suave)", "voice": "en-US-RyanMultilingualNeural"},
    "andrew": {"desc": "Andrew (Multilingual | Masculino Quente)", "voice": "en-US-AndrewMultilingualNeural"},
    "ava": {"desc": "Ava (Multilingual | Feminina Dinâmica)", "voice": "en-US-AvaMultilingualNeural"},
    "florian": {"desc": "Florian (Multilingual | Masc Investigativo)", "voice": "de-DE-FlorianMultilingualNeural"},
    "seraphina": {"desc": "Seraphina (Multilingual | Fem Direta/Séria)", "voice": "de-DE-SeraphinaMultilingualNeural"},
    "remy": {"desc": "Remy (Multilingual | Masculino Sussurrado/Elegante)", "voice": "fr-FR-RemyMultilingualNeural"},
    "vivienne": {"desc": "Vivienne (Multilingual | Feminina Articulada)", "voice": "fr-FR-VivienneMultilingualNeural"}
}

async def _synthesize_single(text: str, output_path: str, voice: str, rate: str, pitch: str):
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    await communicate.save(output_path)

def gerar_audio(text: str, output_path: str, voice: str, rate: str, pitch: str):
    asyncio.run(_synthesize_single(text, output_path, voice, rate, pitch))

def gerar_todos_audios(falas: list[str], pasta_saida: str, voice_key: str = "antonio", taxa_str: str = "+0%", tom_str: str = "+0Hz", progress_callback=None) -> list[str]:
    os.makedirs(pasta_saida, exist_ok=True)
    arquivos = []
    total = len(falas)
    v_cfg = VOZES.get(voice_key, VOZES["antonio"])
    
    for i, fala in enumerate(falas, start=1):
        nome = os.path.join(pasta_saida, f"cena_{i:02d}.mp3")
        tentativas = 0
        sucesso = False
        ultimo_erro = ""
        
        while tentativas < 3 and not sucesso:
            try:
                gerar_audio(fala, nome, v_cfg["voice"], taxa_str, tom_str)
                sucesso = True
            except Exception as e:
                ultimo_erro = str(e)
                tentativas += 1
                time.sleep(2)
                
        if not sucesso:
            raise Exception(f"Falha na cena {i} após 3 tentativas. Erro: {ultimo_erro}")
            
        arquivos.append(nome)
        if progress_callback:
            progress_callback(i, total)
        time.sleep(1)
            
    return arquivos