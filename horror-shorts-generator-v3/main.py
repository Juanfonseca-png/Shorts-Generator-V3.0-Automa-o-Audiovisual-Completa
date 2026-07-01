#!/usr/bin/env python3
"""
Shorts Generator V3.0 — Máquina Universal de Vídeos Virais
Ferramenta desktop em Python + Gradio para geração e montagem audiovisual completa.
"""
import os
import sys
import json
import time
import glob
import shutil
import requests
import subprocess
import threading
import logging
import platform
from datetime import datetime
import pandas as pd

import gradio as gr
from dotenv import load_dotenv, set_key

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.prompt_templates import SYSTEM_PROMPT, PROMPT_ANALISE, build_user_prompt, TEMPLATES_NICHO
from modules.gemini_client import GeminiClient
from modules.tts_engine import gerar_todos_audios, VOZES, gerar_audio
from modules.script_engine import formatar_roteiro, extrair_falas, extrair_prompts_imagem, extrair_prompts_video, extrair_metadata
from modules.export_engine import salvar_json, salvar_txt, criar_zip, criar_zip_audios, timestamp_str, gerar_srt, exportar_capcut
from modules.image_engine import gerar_imagens_cenas, gerar_thumbnail
from modules.video_engine import montar_video, listar_midias_ordenadas
from modules.flow_engine import gerar_imagens_no_flow  
from modules.music_engine import gerar_trilha_mubert
from modules.publisher_engine import publicar_youtube
from modules.scraper_engine import extrair_e_resumir_url
from modules.audio_fx_engine import aplicar_efeito_radio

load_dotenv()

os.makedirs("outputs", exist_ok=True)
logging.basicConfig(filename=os.path.join("outputs", "app.log"), level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

STATE_LOCK = threading.Lock()
CANCEL_EVENT = threading.Event()

STATE = {
    "last_data": None,
    "last_audio_dir": None,
    "last_audio_files": [],
    "last_image_dir": None,
    "last_image_files": [],
    "last_json_path": None,
    "last_txt_path": None,
    "last_video_path": None,
    "last_bg_music": None,
    "last_srt_path": None,
    "last_thumbnail_path": None
}

HISTORY_FILE = os.path.join("outputs", "history.json")

def _load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except Exception: pass
    return []

def _save_history(entry):
    hist = _load_history()
    hist.insert(0, entry)
    limit = int(os.getenv("HISTORY_LIMIT", "50"))
    hist = hist[:limit]
    os.makedirs("outputs", exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f: json.dump(hist, f, ensure_ascii=False, indent=2)

def _clear_history():
    if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)

def aplicar_template(selecao):
    if selecao in TEMPLATES_NICHO: return TEMPLATES_NICHO[selecao]["tema"], TEMPLATES_NICHO[selecao]["intensidade"]
    return "", "🟠 Misterioso & Intrigante"

def extrair_resumo_url(url):
    api_key = os.getenv("GEMINI_API_KEY", "")
    resumo = extrair_e_resumir_url(url, api_key, os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    return resumo, gr.update(visible=True)

def gerar_roteiro(url_ref, conteudo_extraido, tema_input, intensidade, qtd_cenas, modo_batch, qtd_batch):
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key: raise gr.Error("API Key não configurada.")
    if not tema_input: raise gr.Error("Forneça um tema ou nicho.")

    qtd = int(qtd_batch) if modo_batch else 1
    resultados = []
    client = GeminiClient(api_key=api_key, model_name=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    
    contexto = conteudo_extraido if conteudo_extraido else url_ref
    user_prompt = build_user_prompt(tema_input, intensidade, contexto, int(qtd_cenas))
    CANCEL_EVENT.clear()

    for i in range(qtd):
        if CANCEL_EVENT.is_set():
            resultados.append(("Batch Cancelado pelo Usuário!", "", "", "", "", pd.DataFrame(), pd.DataFrame(), "", ""))
            break
            
        try: 
            data_cru = client.generate_script(SYSTEM_PROMPT, user_prompt)
            if isinstance(data_cru, str):
                clean_data = data_cru.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_data[clean_data.find('{'):clean_data.rfind('}')+1])
            else: data = data_cru
            
            if "roteiro" not in data:
                if "response" in data and "roteiro" in data["response"]: data = data["response"]
                elif "cenas" in data: data["roteiro"] = data.pop("cenas")
                    
            df_editor = []
            for idx_cena, cena_dict in enumerate(data.get("roteiro", [])):
                for k in list(cena_dict.keys()): cena_dict[k.lower()] = cena_dict.pop(k)
                if "cena" not in cena_dict: cena_dict["cena"] = idx_cena + 1
                if "fala_tts" not in cena_dict: cena_dict["fala_tts"] = cena_dict.get("fala", "")
                if "prompt_imagem_flux" not in cena_dict: cena_dict["prompt_imagem_flux"] = cena_dict.get("prompt_imagem", "")
                if "efeito_camera" not in cena_dict: cena_dict["efeito_camera"] = "Estático"
                df_editor.append([cena_dict["cena"], cena_dict["fala_tts"], cena_dict["prompt_imagem_flux"], cena_dict["efeito_camera"]])

            roteiro_txt = formatar_roteiro(data)
            falas_txt = "\n".join([f"{idx+1:02d}. {f}" for idx, f in enumerate(extrair_falas(data))])
            imgs_txt = "\n\n".join([f"【{idx+1:02d}】{p}" for idx, p in enumerate(extrair_prompts_imagem(data))])
            vids_txt = "\n\n".join([f"【{idx+1:02d}】{p}" for idx, p in enumerate(extrair_prompts_video(data))])

            meta = extrair_metadata(data)
            meta_txt = f"Títulos:\n" + "\n".join([f"  • {t}" for t in meta.get("titulos", [])]) + f"\n\nDescrição:\n{meta.get('descricao', '')}"
            json_path, txt_path = salvar_json(data), salvar_txt(data)
            
            with STATE_LOCK:
                STATE["last_data"] = data; STATE["last_json_path"] = json_path; STATE["last_txt_path"] = txt_path

            _save_history({"timestamp": datetime.now().isoformat(), "tema": tema_input, "intensidade": intensidade, "json_file": os.path.basename(json_path), "txt_file": os.path.basename(txt_path)})
            df_vozes = pd.DataFrame({"Cena": [r[0] for r in df_editor], "Voz": ["antonio" for _ in df_editor]})
            resultados.append((roteiro_txt, falas_txt, imgs_txt, vids_txt, meta_txt, pd.DataFrame(df_editor, columns=["Cena", "Fala TTS", "Prompt Imagem", "Efeito Câmera"]), df_vozes, meta.get("titulos", [""])[0], meta.get("descricao", "")))

        except Exception as e: raise gr.Error(f"Erro na geração: {str(e)}")

    if modo_batch and qtd > 1:
        sep = "\n" + "="*60 + "\n"
        return (sep.join([r[0] for r in resultados]), sep.join([r[1] for r in resultados]), sep.join([r[2] for r in resultados]), sep.join([r[3] for r in resultados]), sep.join([r[4] for r in resultados]), resultados[-1][5], resultados[-1][6], resultados[-1][7], resultados[-1][8])
    return resultados[0]

def cancelar_batch():
    CANCEL_EVENT.set(); return "🛑 Cancelamento solicitado. Aguarde..."

def salvar_edicoes_roteiro(df):
    with STATE_LOCK:
        data = STATE.get("last_data")
        if not data: return "❌ Gere um roteiro primeiro.", "", ""
        for i, row in df.iterrows():
            if i < len(data["roteiro"]):
                data["roteiro"][i]["fala_tts"], data["roteiro"][i]["prompt_imagem_flux"], data["roteiro"][i]["efeito_camera"] = str(row["Fala TTS"]), str(row["Prompt Imagem"]), str(row["Efeito Câmera"])
        STATE["last_data"] = data
        falas_txt = "\n".join([f"{idx+1:02d}. {f}" for idx, f in enumerate(extrair_falas(data))])
        imgs_txt = "\n\n".join([f"【{idx+1:02d}】{p}" for idx, p in enumerate(extrair_prompts_imagem(data))])
    return "✅ Edições salvas com sucesso!", falas_txt, imgs_txt

def regenerar_cena_individual(n_cena, voz_selecionada, taxa, tom):
    with STATE_LOCK: data = STATE.get("last_data")
    if not data: return "❌ Nenhum roteiro gerado.", pd.DataFrame(), "", ""
    idx = int(n_cena) - 1
    if idx < 0 or idx >= len(data["roteiro"]): return "❌ Número de cena inválido.", pd.DataFrame(), "", ""
    cena_atual = data["roteiro"][idx]
    contexto = json.dumps([c for c in data["roteiro"] if c["cena"] in [idx, idx+2]], ensure_ascii=False)
    prompt = f"A cena {n_cena} original era:\n{json.dumps(cena_atual, ensure_ascii=False)}\n\nReescreva mantendo conexão:\n{contexto}\n\nRetorne JSON com: cena, bloco_narrativo, fala_tts, prompt_imagem_flux, efeito_camera."
    client = GeminiClient(api_key=os.getenv("GEMINI_API_KEY"), model_name=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    try:
        resp = client.client.models.generate_content(model=client.model_name, contents=prompt)
        clean = resp.text.replace("```json", "").replace("```", "").strip()
        nova_cena = json.loads(clean[clean.find('{'):clean.rfind('}')+1])
        data["roteiro"][idx].update(nova_cena)
        with STATE_LOCK: STATE["last_data"] = data
        df_editor = [[c["cena"], c.get("fala_tts",""), c.get("prompt_imagem_flux",""), c.get("efeito_camera","")] for c in data["roteiro"]]
        audio_path = os.path.join(STATE["last_audio_dir"], f"cena_{int(n_cena):02d}.mp3") if STATE.get("last_audio_dir") else ""
        if audio_path:
            v_cfg = VOZES.get(voz_selecionada, VOZES["antonio"])
            gerar_audio(nova_cena.get("fala_tts",""), audio_path, v_cfg["voice"], f"{int(taxa):+d}%", f"{int(tom):+d}Hz")
        return f"✅ Cena {int(n_cena)} regenerada!", pd.DataFrame(df_editor, columns=["Cena", "Fala TTS", "Prompt Imagem", "Efeito Câmera"]), formatar_roteiro(data), "\n".join([f"{i+1:02d}. {f}" for i, f in enumerate(extrair_falas(data))])
    except Exception as e: return f"❌ Erro ao regenerar: {e}", pd.DataFrame(), "", ""

def analisar_roteiro_ia():
    with STATE_LOCK: data = STATE.get("last_data")
    if not data: return "❌ Nenhum roteiro gerado."
    try:
        client = GeminiClient(api_key=os.getenv("GEMINI_API_KEY", ""), model_name=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
        resp = client.client.models.generate_content(model=client.model_name, contents=f"{PROMPT_ANALISE}\n\n{json.dumps(data)}")
        return resp.text
    except Exception as e: return f"Erro na análise: {e}"

def traduzir_roteiro_ui(idioma, regerar, voz, taxa, tom):
    with STATE_LOCK: data = STATE.get("last_data")
    if not data: return "❌ Nenhum roteiro.", pd.DataFrame()
    prompt = f"Traduza APENAS os campos 'fala_tts' do roteiro JSON abaixo para {idioma}. Mantenha a estrutura JSON e prompts em inglês.\n{json.dumps(data, ensure_ascii=False)}"
    client = GeminiClient(api_key=os.getenv("GEMINI_API_KEY"), model_name=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    try:
        resp = client.client.models.generate_content(model=client.model_name, contents=prompt)
        clean = resp.text.replace("```json", "").replace("```", "").strip()
        novo_data = json.loads(clean[clean.find('{'):clean.rfind('}')+1])
        with STATE_LOCK: STATE["last_data"] = novo_data
        msg = f"✅ Traduzido para {idioma}."
        if regerar:
            falas = extrair_falas(novo_data)
            pasta = STATE.get("last_audio_dir", os.path.join("outputs", f"audio_{timestamp_str()}"))
            gerar_todos_audios(falas, pasta, voice_key=voz, taxa_str=f"{int(taxa):+d}%", tom_str=f"{int(tom):+d}Hz")
            with STATE_LOCK: STATE["last_audio_dir"] = pasta; STATE["last_audio_files"] = [os.path.join(pasta, f"cena_{i+1:02d}.mp3") for i in range(len(falas))]
            msg += " Áudios regerados!"
        df_editor = [[c["cena"], c.get("fala_tts",""), c.get("prompt_imagem_flux",""), c.get("efeito_camera","")] for c in novo_data["roteiro"]]
        return msg, pd.DataFrame(df_editor, columns=["Cena", "Fala TTS", "Prompt Imagem", "Efeito Câmera"])
    except Exception as e: return f"❌ Erro: {e}", pd.DataFrame()

def preview_voz_tts(voz_selecionada, taxa, tom):
    v_cfg = VOZES.get(voz_selecionada, VOZES["antonio"])
    caminho = os.path.join("outputs", "previews", f"preview_{timestamp_str()}.mp3")
    gerar_audio("Este é um teste de áudio.", caminho, v_cfg["voice"], f"{int(taxa):+d}%", f"{int(tom):+d}Hz")
    return gr.Audio(value=caminho, visible=True, autoplay=True)

def gerar_audios_tts(voz_selecionada, taxa, tom, chk_vozes_mistas, df_vozes, chk_radio, radio_ruido, radio_grave, radio_agudo, progress=gr.Progress()):
    with STATE_LOCK: data = STATE.get("last_data")
    if not data: raise gr.Error("Gere um roteiro primeiro.")
    falas = extrair_falas(data)
    pasta = os.path.join("outputs", f"audio_{timestamp_str()}")
    try: 
        if chk_vozes_mistas:
            os.makedirs(pasta, exist_ok=True)
            arquivos = []
            vozes_lista = df_vozes["Voz"].tolist()
            for i, fala in enumerate(falas):
                voz_key = vozes_lista[i] if i < len(vozes_lista) else "antonio"
                v_cfg = VOZES.get(voz_key, VOZES["antonio"])
                nome = os.path.join(pasta, f"cena_{i+1:02d}.mp3")
                gerar_audio(fala, nome, v_cfg["voice"], f"{int(taxa):+d}%", f"{int(tom):+d}Hz")
                arquivos.append(nome)
                progress((i+1)/len(falas), desc=f"Gerando áudio {i+1}...")
        else:
            arquivos = gerar_todos_audios(falas, pasta, voice_key=voz_selecionada, taxa_str=f"{int(taxa):+d}%", tom_str=f"{int(tom):+d}Hz", progress_callback=lambda i,t: progress(i/t, desc=f"Áudio {i}/{t}"))
        
        if chk_radio:
            for f_audio in arquivos: aplicar_efeito_radio(f_audio, radio_ruido, radio_grave, radio_agudo)
                
        with STATE_LOCK: STATE["last_audio_dir"], STATE["last_audio_files"] = pasta, arquivos
        return f"✅ {len(arquivos)} áudios gerados", [p for p in arquivos if os.path.exists(p)]
    except Exception as e: raise gr.Error(f"Erro TTS: {str(e)}")

def chamar_mubert(estilo, vol, key):
    set_key(".env", "MUBERT_API_KEY", key); load_dotenv(override=True)
    with STATE_LOCK: data = STATE.get("last_data")
    if not data: raise gr.Error("Gere roteiro/áudios primeiro.")
    try:
        trilha = gerar_trilha_mubert(estilo, len(data.get("roteiro",[])) * 3.5, key)
        with STATE_LOCK: STATE["last_bg_music"] = trilha
        return f"✅ Trilha gerada: {trilha}", trilha
    except Exception as e: raise gr.Error(f"Erro Mubert: {e}")

def gerar_imagens(progress=gr.Progress()):
    with STATE_LOCK: data = STATE.get("last_data")
    if not data: raise gr.Error("Gere um roteiro primeiro.")
    prompts = extrair_prompts_imagem(data)
    pasta = os.path.join("outputs", f"imagens_{timestamp_str()}")
    arquivos = gerar_imagens_cenas(prompts, pasta, progress_callback=lambda i,t: progress(i/t, desc=f"Imagem {i}/{t}"))
    with STATE_LOCK: STATE["last_image_dir"], STATE["last_image_files"] = pasta, arquivos
    return f"✅ {len(arquivos)} imagens geradas", [(img, f"Cena {i+1}") for i, img in enumerate(arquivos)]

def gerar_thumbnail_ui(w, h):
    with STATE_LOCK: data = STATE.get("last_data")
    if not data: raise gr.Error("Gere um roteiro primeiro para ter o prompt.")
    prompt_thumb = extrair_metadata(data).get("thumbnail", "creepy cinematic background")
    try:
        path = gerar_thumbnail(prompt_thumb, w, h)
        with STATE_LOCK: STATE["last_thumbnail_path"] = path
        return path
    except Exception as e: raise gr.Error(f"Erro Thumb: {e}")

def gerar_imagens_flow_playwright(pasta_midias):
    with STATE_LOCK: data = STATE.get("last_data")
    if not data: raise gr.Error("Gere roteiro primeiro.")
    prompts = extrair_prompts_imagem(data)
    pasta = pasta_midias or os.path.join("outputs", "imagens_flow")
    try:
        gr.Info("Automação iniciada! Aguarde.")
        arquivos = gerar_imagens_no_flow(prompts, pasta, "https://labs.google/fx/pt/tools/flow")
        with STATE_LOCK: STATE["last_image_dir"], STATE["last_image_files"] = pasta, arquivos
        return f"✅ {len(arquivos)} imagens Flow salvas", [(img, f"Cena {i+1}") for i, img in enumerate(arquivos)]
    except Exception as e: raise gr.Error(f"Erro: {str(e)}")

# ==========================================
# CORE DE MONTAGEM COM TODOS OS KWARGS
# ==========================================
def montar_video_core(pasta_midias, upload_midias, ordenar_por_data, ativar_efeitos, formato_video, intensidade, velocidade, 
                      chk_transicoes, tipo_transicao, dur_transicao, chk_musica, vol_musica, 
                      chk_legenda, estilo_legenda, tam_legenda, pos_legenda, queimar_legenda, 
                      chk_overlay_texto, overlay_estilo, overlay_tam, overlay_pos,
                      chk_cor, cor_sat, cor_cont, chk_croma, croma_shift, chk_glitch, glitch_int, chk_shake, shake_int, chk_vinheta, vinheta_int,
                      chk_marca, texto_marca, pos_marca, chk_barra, cor_barra, chk_comp, comp_bitrate, chk_cleanup,
                      preview_n=None):
    with STATE_LOCK:
        audio_files = STATE.get("last_audio_files")
        image_files = STATE.get("last_image_files", [])
        bg_music = STATE.get("last_bg_music")
        data = STATE.get("last_data")
        
    if not audio_files: raise gr.Error("Gere os áudios TTS primeiro.")
    if pasta_midias: set_key(".env", "LAST_MEDIA_FOLDER", pasta_midias); load_dotenv(override=True)
    
    midias = [f.name if hasattr(f, 'name') else f for f in upload_midias] if upload_midias else listar_midias_ordenadas(pasta_midias, ordenar_por_data) if pasta_midias else image_files
    if not midias: raise gr.Error("Nenhuma mídia encontrada.")

    if preview_n:
        midias = midias[:int(preview_n)]; audio_files = audio_files[:int(preview_n)]

    falas = extrair_falas(data) if data else []
    srt_path = None
    if chk_legenda and data:
        srt_path = gerar_srt(audio_files[:int(preview_n)] if preview_n else audio_files, falas[:int(preview_n)] if preview_n else falas)
        with STATE_LOCK: STATE["last_srt_path"] = srt_path

    kwargs_melhorias = {
        "preview_mode": True if preview_n else False,
        "ativar_transicoes": chk_transicoes, "tipo_transicao": tipo_transicao, "dur_transicao": dur_transicao,
        "trilha_bg": bg_music if chk_musica else None, "vol_bg": vol_musica,
        "srt_path": srt_path, "queimar_legenda": queimar_legenda, "srt_estilo": estilo_legenda, "srt_tamanho": tam_legenda,
        "ativar_overlay_texto": chk_overlay_texto, "overlay_estilo": overlay_estilo, "overlay_tam": overlay_tam, "overlay_pos": overlay_pos,
        "falas": falas,
        "chk_cor": chk_cor, "cor_sat": cor_sat, "cor_cont": cor_cont, "chk_croma": chk_croma, "croma_shift": croma_shift,
        "chk_glitch": chk_glitch, "glitch_int": glitch_int, "chk_shake": chk_shake, "shake_int": shake_int, "chk_vinheta": chk_vinheta, "vinheta_int": vinheta_int,
        "chk_marca": chk_marca, "texto_marca": texto_marca, "pos_marca": pos_marca, "chk_barra": chk_barra, "cor_barra": cor_barra,
        "chk_comp": chk_comp, "compressao_bitrate": comp_bitrate, "chk_cleanup": chk_cleanup
    }

    output_path = os.path.join("outputs", f"shorts_{'preview_' if preview_n else ''}{timestamp_str()}.mp4")
    try: 
        montar_video(midias, audio_files, output_path, False if preview_n else ativar_efeitos, formato_video, intensidade, velocidade, kwargs_melhorias)
    except Exception as e:
        logger.error(f"Falha ao montar vídeo: {e}")
        raise gr.Error(f"Falha ao montar vídeo: {str(e)}")
        
    if not preview_n:
        with STATE_LOCK: STATE["last_video_path"] = output_path
    return f"✅ Vídeo {'Preview ' if preview_n else ''}montado: {output_path}", output_path

def disparar_youtube(titulo, desc, tags, priv):
    with STATE_LOCK: vp = STATE.get("last_video_path")
    return publicar_youtube(vp, titulo, desc, tags, priv)

def chamar_export_capcut():
    with STATE_LOCK: j_path, t_path, a_paths, i_paths = STATE.get("last_json_path"), STATE.get("last_txt_path"), STATE.get("last_audio_files", []), STATE.get("last_image_files", [])
    try: return exportar_capcut(j_path, t_path, a_paths, i_paths)
    except Exception as e: raise gr.Error(str(e))

def exportar_zip():
    with STATE_LOCK: j_path, t_path, a_paths = STATE.get("last_json_path"), STATE.get("last_txt_path"), STATE.get("last_audio_files", [])
    if not j_path or not os.path.exists(j_path): raise gr.Error("Nenhum roteiro.")
    return criar_zip(j_path, t_path, a_paths)

def exportar_zip_audios():
    with STATE_LOCK: a_paths = STATE.get("last_audio_files", [])
    if not a_paths: raise gr.Error("Nenhum áudio.")
    return criar_zip_audios(a_paths)

def testar_conexao(k, m):
    ok, msg = GeminiClient(api_key=k, model_name=m).test_connection()
    return msg

def salvar_config(api_key, modelo, webhook_toggle, webhook_url, auto_tts, auto_imagens):
    env_path = ".env"
    set_key(env_path, "GEMINI_API_KEY", api_key or "")
    set_key(env_path, "GEMINI_MODEL", modelo or "gemini-2.5-flash")
    set_key(env_path, "WEBHOOK_ENABLED", str(webhook_toggle))
    set_key(env_path, "WEBHOOK_URL", webhook_url or "")
    set_key(env_path, "AUTO_TTS", str(auto_tts))
    set_key(env_path, "AUTO_IMAGENS", str(auto_imagens))
    load_dotenv(override=True)
    return "✅ Configurações salvas"

def listar_historico():
    hist = _load_history()
    if not hist: return "Nenhum roteiro."
    return "\n".join([f"{i}. [{h.get('timestamp','?')[:16].replace('T',' ')}] {h.get('tema','?')} (Int: {h.get('intensidade','?')})" for i, h in enumerate(hist, 1)])

def carregar_metricas():
    hist = _load_history()
    tot_rot = len(hist)
    tot_vid = sum(1 for h in hist if h.get("json_file"))
    nichos = [h.get("tema", "") for h in hist if h.get("tema")]
    ints = [h.get("intensidade", "") for h in hist if h.get("intensidade")]
    n_freq = max(set(nichos), key=nichos.count) if nichos else "N/A"
    i_freq = max(set(ints), key=ints.count) if ints else "N/A"
    ult = hist[0].get("timestamp", "N/A")[:16].replace("T", " ") if hist else "N/A"
    return tot_rot, tot_vid, n_freq, i_freq, ult

def abrir_historico(index_str):
    try: idx = int(index_str) - 1
    except: raise gr.Error("Número inválido.")
    hist = _load_history()
    if idx < 0 or idx >= len(hist): raise gr.Error("Fora do range.")
    entry = hist[idx]
    json_path = os.path.join("outputs", entry.get("json_file", ""))
    if not os.path.exists(json_path):
        matches = glob.glob(os.path.join("outputs", f"*roteiro_{entry['timestamp'][:8]}*.json"))
        if matches: json_path = matches[0]
        else: raise gr.Error("JSON não encontrado.")

    with open(json_path, "r", encoding="utf-8") as f: data = json.load(f)
    txt_path = json_path.replace(".json", ".txt")
    with STATE_LOCK:
        STATE["last_data"] = data
        STATE["last_json_path"] = json_path
        if os.path.exists(txt_path): STATE["last_txt_path"] = txt_path

    return (formatar_roteiro(data), "\n".join([f"{i+1:02d}. {f}" for i, f in enumerate(extrair_falas(data))]),
            "\n\n".join([f"【{i+1:02d}】{p}" for i, p in enumerate(extrair_prompts_imagem(data))]),
            "\n\n".join([f"【{i+1:02d}】{p}" for i, p in enumerate(extrair_prompts_video(data))]), "Carregado.")

def limpar_historico():
    _clear_history(); return "🗑 Histórico limpo."

def build_ui():
    with gr.Blocks(title="Shorts Generator V3.0", css=".output-box { min-height: 200px; }") as demo:
        gr.Markdown("# 🎬 Shorts Generator V3.0\n### Máquina Universal de Vídeos Virais")

        with gr.Tab("⚡ Gerador Principal"):
            with gr.Row():
                with gr.Column(scale=1):
                    template_nicho = gr.Dropdown(label="📋 Carregar Template de Nicho", choices=list(TEMPLATES_NICHO.keys()), value="-- Nenhum --")
                    with gr.Row():
                        url_ref = gr.Textbox(label="🔗 URL de Referência (opcional)", lines=1)
                        btn_scraper = gr.Button("🔍 Extrair Conteúdo", size="sm")
                    out_scraper = gr.Textbox(label="📄 Conteúdo Extraído", lines=3, interactive=False, visible=False)
                    
                    tema_input = gr.Textbox(label="✏️ Digite o Tema ou Nicho", lines=2)
                    intensidade = gr.Radio(label="🔥 Nível de Energia", choices=["🟢 Suave & Educativo", "🟡 Dinâmico & Informativo", "🟠 Misterioso & Intrigante", "🔴 Tenso & Sombrio", "⚫ Visceral & Assustador"], value="🟠 Misterioso & Intrigante")
                    template_nicho.change(fn=aplicar_template, inputs=[template_nicho], outputs=[tema_input, intensidade])
                    btn_scraper.click(fn=extrair_resumo_url, inputs=[url_ref], outputs=[out_scraper, out_scraper])
                    
                    qtd_cenas = gr.Number(label="🎬 Quantidade de Cenas", value=20, precision=0)
                    modo_batch = gr.Checkbox(label="📦 Modo Batch", value=False)
                    qtd_batch = gr.Slider(label="Qtd Roteiros", minimum=2, maximum=20, step=1, value=2, visible=False)
                    modo_batch.change(fn=lambda m: gr.update(visible=m), inputs=modo_batch, outputs=qtd_batch)
                    
                    with gr.Row():
                        btn_gerar = gr.Button("1️⃣ Gerar Roteiro", variant="primary")
                        btn_cancel_batch = gr.Button("⏹ Cancelar", variant="stop")
                    status_batch = gr.Textbox(label="Status Batch", visible=False)
                    
                with gr.Column(scale=2):
                    out_roteiro = gr.Textbox(label="📜 Roteiro Completo", lines=10, interactive=False)
                    with gr.Accordion("✏️ Editar Roteiro Cena a Cena", open=False):
                        df_editor = gr.Dataframe(headers=["Cena", "Fala TTS", "Prompt Imagem", "Efeito Câmera"], col_count=(4, "fixed"), interactive=True, wrap=True)
                        with gr.Row():
                            btn_salvar_edicoes = gr.Button("💾 Salvar Edições inteiras da Tabela")
                            n_cena_regen = gr.Number(label="Nº Cena para Regenerar", precision=0)
                            btn_regen = gr.Button("🔄 Regenerar Cena na IA")
                        status_edicao = gr.Textbox(label="Status", lines=1, interactive=False)
                        
                    with gr.Accordion("🌍 Tradução Multilíngue", open=False):
                        lang_trad = gr.Dropdown(label="Traduzir Roteiro para", choices=["🇺🇸 Inglês", "🇪🇸 Espanhol", "🇫🇷 Francês", "🇩🇪 Alemão", "🇯🇵 Japonês"], value="🇺🇸 Inglês")
                        chk_regerar_trad = gr.Checkbox(label="Regerar áudios TTS automaticamente", value=True)
                        btn_trad = gr.Button("🌍 Traduzir Roteiro")
                        msg_trad = gr.Textbox(label="Status Tradução", interactive=False)
                        
                    with gr.Accordion("🧠 Análise de Roteiro com IA", open=False):
                        btn_analise = gr.Button("🧠 Analisar Retenção e Qualidade")
                        out_analise = gr.Textbox(label="📊 Análise da IA", lines=5, interactive=False)
                        btn_analise.click(fn=analisar_roteiro_ia, outputs=out_analise)

                    with gr.Accordion("📂 Ver prompts e extras", open=False):
                        out_falas = gr.Textbox(label="🎙 Falas", lines=5)
                        out_imgs = gr.Textbox(label="🖼 Prompts de Imagem", lines=5)
                        out_vids = gr.Textbox(label="🎬 Prompts de Vídeo", lines=5)
                        out_meta = gr.Textbox(label="📢 Metadata SEO", lines=5)
                        
                    btn_salvar_edicoes.click(fn=salvar_edicoes_roteiro, inputs=[df_editor], outputs=[status_edicao, out_falas, out_imgs])

            gr.Markdown("---")
            with gr.Row():
                with gr.Column(scale=1):
                    voz_tts = gr.Dropdown(label="🎙 Voz TTS Padrão", choices=[(v["desc"], k) for k, v in VOZES.items()], value="antonio")
                    with gr.Row():
                        taxa_tts = gr.Slider(label="🚀 Taxa", minimum=-50, maximum=50, step=1, value=0)
                        tom_tts = gr.Slider(label="🎵 Tom", minimum=-50, maximum=50, step=1, value=-5)
                    
                    chk_vozes_mistas = gr.Checkbox(label="🎭 Usar vozes diferentes por cena", value=False)
                    df_vozes = gr.Dataframe(headers=["Cena", "Voz"], interactive=True, visible=False)
                    chk_vozes_mistas.change(fn=lambda x: gr.update(visible=x), inputs=chk_vozes_mistas, outputs=df_vozes)
                    
                    with gr.Accordion("📻 Efeitos de Áudio", open=False):
                        chk_radio = gr.Checkbox(label="📻 Efeito Rádio FM Clássico", value=False)
                        radio_ruido = gr.Slider(label="Intensidade do Ruído", minimum=0.001, maximum=0.05, step=0.001, value=0.01, visible=False)
                        radio_grave = gr.Slider(label="Corte Grave (Hz)", minimum=100, maximum=500, step=10, value=300, visible=False)
                        radio_agudo = gr.Slider(label="Corte Agudo (Hz)", minimum=2000, maximum=5000, step=100, value=3400, visible=False)
                        chk_radio.change(fn=lambda x: [gr.update(visible=x)]*3, inputs=chk_radio, outputs=[radio_ruido, radio_grave, radio_agudo])
                    
                    with gr.Row():
                        btn_play_preview = gr.Button("▶ Ouvir Prévia", scale=1)
                        btn_tts = gr.Button("2️⃣ Gerar Áudios", variant="primary", scale=2)
                    
                    audio_preview = gr.Audio(label="Prévia", visible=False, autoplay=True)
                    tts_status = gr.Textbox(label="Status TTS", interactive=False, lines=1)
                    
                    btn_regen.click(fn=regenerar_cena_individual, inputs=[n_cena_regen, voz_tts, taxa_tts, tom_tts], outputs=[status_edicao, df_editor, out_roteiro, out_falas])
                    btn_trad.click(fn=traduzir_roteiro_ui, inputs=[lang_trad, chk_regerar_trad, voz_tts, taxa_tts, tom_tts], outputs=[msg_trad, df_editor])
                
                with gr.Column(scale=2):
                    gr.Markdown("### 3️⃣ Mídias Visuais")
                    btn_imagens = gr.Button("🖼 Gerar Rascunhos Rápido (Pollinations)")
                    btn_flow = gr.Button("🚀 Gerar Imagens de Alta Qualidade (Playwright + Flow)", variant="primary")
                    pasta_midias = gr.Textbox(label="Ou digite a pasta local", value=os.getenv("LAST_MEDIA_FOLDER", ""))
                    upload_midias = gr.File(label="📂 Upload Manual", file_count="multiple", file_types=["image", "video"])
                    
                    with gr.Accordion("🖼 Thumbnail", open=False):
                        btn_thumb = gr.Button("🖼 Gerar Thumbnail (Pollinations)")
                        w_thumb = gr.Slider(label="Largura", minimum=720, maximum=1920, step=10, value=1280)
                        h_thumb = gr.Slider(label="Altura", minimum=720, maximum=1920, step=10, value=720)
                        img_thumb = gr.Image(label="Thumbnail", interactive=False, type="filepath")
                        btn_thumb.click(fn=gerar_thumbnail_ui, inputs=[w_thumb, h_thumb], outputs=img_thumb)
                    
                    with gr.Accordion("🎵 Música de Fundo (Mubert API)", open=False):
                        chk_musica = gr.Checkbox(label="🎵 Adicionar Música de Fundo", value=False)
                        estilo_musica = gr.Dropdown(label="Estilo Musical", choices=["Horror Ambient", "Dark Cinematic", "Suspense", "Epic Trailer"], visible=False)
                        vol_musica = gr.Slider(label="Volume", minimum=0.0, maximum=1.0, step=0.05, value=0.15, visible=False)
                        mubert_key = gr.Textbox(label="Mubert API Key (PAT)", type="password", value=os.getenv("MUBERT_API_KEY", ""), visible=False)
                        btn_mubert = gr.Button("🎵 Gerar e Baixar Trilha", visible=False)
                        status_mubert = gr.Textbox(label="Trilha", interactive=False, visible=False)
                        chk_musica.change(fn=lambda x: [gr.update(visible=x)]*5, inputs=chk_musica, outputs=[estilo_musica, vol_musica, mubert_key, btn_mubert, status_mubert])
                        btn_mubert.click(fn=chamar_mubert, inputs=[estilo_musica, vol_musica, mubert_key], outputs=[status_mubert, gr.Audio(visible=False)])

            gr.Markdown("---")
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 4️⃣ Controles de Montagem")
                    formato_video = gr.Radio(label="📺 Formato", choices=["9:16 (Vertical)", "16:9 (Horizontal)"], value="9:16 (Vertical)")
                    chk_efeitos = gr.Checkbox(label="✨ Efeitos (Ken Burns)", value=True)
                    with gr.Row():
                        intensidade_efeito = gr.Slider(label="💥 Intensidade (Zoom/Pan)", minimum=0.5, maximum=3.0, step=0.1, value=1.0)
                        velocidade_efeito = gr.Slider(label="🚀 Velocidade do Efeito", minimum=0.5, maximum=3.0, step=0.1, value=1.0)
                    chk_ordenar_data = gr.Checkbox(label="🕒 Ordenar por Data", value=False)
                    
                    with gr.Accordion("🎬 Efeitos de Transição", open=False):
                        chk_transicoes = gr.Checkbox(label="Ativar Transições", value=False)
                        tipo_transicao = gr.Dropdown(label="Tipo", choices=["Fade to Black", "Fade to White"], value="Fade to Black", visible=False)
                        dur_transicao = gr.Slider(label="Duração (segundos)", minimum=0.1, maximum=1.5, step=0.1, value=0.5, visible=False)
                        chk_transicoes.change(fn=lambda x: [gr.update(visible=x)]*2, inputs=chk_transicoes, outputs=[tipo_transicao, dur_transicao])
                        
                    with gr.Accordion("🔤 Legendas Automáticas", open=False):
                        chk_legenda = gr.Checkbox(label="Gerar Legenda (SRT)", value=False)
                        estilo_legenda = gr.Dropdown(label="Estilo", choices=["Branca simples", "Amarela com borda", "Horror (vermelho/preto)", "Neon verde"], value="Amarela com borda", visible=False)
                        tam_legenda = gr.Slider(label="Tamanho da Fonte", minimum=20, maximum=80, step=2, value=40, visible=False)
                        pos_legenda = gr.Dropdown(label="Posição", choices=["Inferior Centro", "Superior Centro"], value="Inferior Centro", visible=False)
                        chk_queimar_legenda = gr.Checkbox(label="🔥 Queimar legenda no vídeo (hardcode)", value=True, visible=False)
                        chk_legenda.change(fn=lambda x: [gr.update(visible=x)]*4, inputs=chk_legenda, outputs=[estilo_legenda, tam_legenda, pos_legenda, chk_queimar_legenda])

                    with gr.Accordion("📝 Overlay de Texto Animado", open=False):
                        chk_overlay_texto = gr.Checkbox(label="Ativar Overlay de Texto (Word-by-Word)", value=False)
                        overlay_estilo = gr.Dropdown(label="Estilo do Texto", choices=["Branco/Sombra", "Amarelo/Borda Preta", "Horror Vermelho", "Neon Verde"], value="Amarelo/Borda Preta", visible=False)
                        overlay_tam = gr.Slider(label="Tamanho da Fonte", minimum=20, maximum=80, step=2, value=45, visible=False)
                        overlay_pos = gr.Dropdown(label="Posição", choices=["Centro", "Superior", "Inferior"], value="Centro", visible=False)
                        chk_overlay_texto.change(fn=lambda x: [gr.update(visible=x)]*3, inputs=chk_overlay_texto, outputs=[overlay_estilo, overlay_tam, overlay_pos])
                        
                    # ==========================================
                    # FASE 3: UI EFEITOS MATRICIAIS E OVERLAYS
                    # ==========================================
                    with gr.Accordion("🎨 Efeitos Visuais Avançados (Matricial)", open=False):
                        aviso_tempo = gr.Markdown("⏳ **Tempo Estimado de Renderização:** ~Calculando...")
                        
                        chk_cor = gr.Checkbox(label="🎨 21. Cor Forte (Saturação/Contraste)", value=False)
                        with gr.Row():
                            cor_sat = gr.Slider(label="Saturação", minimum=1.0, maximum=3.0, step=0.1, value=1.5, visible=False)
                            cor_cont = gr.Slider(label="Contraste", minimum=1.0, maximum=3.0, step=0.1, value=1.2, visible=False)
                        chk_cor.change(fn=lambda x: [gr.update(visible=x)]*2, inputs=chk_cor, outputs=[cor_sat, cor_cont])
                        
                        chk_croma = gr.Checkbox(label="🌈 22. Aberração Cromática", value=False)
                        croma_shift = gr.Slider(label="Intensidade (Deslocamento RGB)", minimum=1, maximum=20, step=1, value=5, visible=False)
                        chk_croma.change(fn=lambda x: gr.update(visible=x), inputs=chk_croma, outputs=croma_shift)
                        
                        chk_glitch = gr.Checkbox(label="📺 23. Efeito Glitch", value=False)
                        glitch_int = gr.Slider(label="Intensidade do Glitch", minimum=1, maximum=50, step=1, value=10, visible=False)
                        chk_glitch.change(fn=lambda x: gr.update(visible=x), inputs=chk_glitch, outputs=glitch_int)
                        
                        chk_shake = gr.Checkbox(label="📳 24. Câmera Shake", value=False)
                        shake_int = gr.Slider(label="Tremor (Pixels)", minimum=1, maximum=30, step=1, value=5, visible=False)
                        chk_shake.change(fn=lambda x: gr.update(visible=x), inputs=chk_shake, outputs=shake_int)
                        
                        chk_vinheta = gr.Checkbox(label="🌑 25. Vinheta (Escurecer Bordas)", value=False)
                        vinheta_int = gr.Slider(label="Intensidade da Sombra", minimum=0.1, maximum=1.0, step=0.1, value=0.5, visible=False)
                        chk_vinheta.change(fn=lambda x: gr.update(visible=x), inputs=chk_vinheta, outputs=vinheta_int)
                        
                    with gr.Accordion("🏷️ Utilitários de Interface e Otimização", open=False):
                        chk_marca = gr.Checkbox(label="19. Marca D'água (Watermark)", value=False)
                        texto_marca = gr.Textbox(label="Texto (Ex: @MeuCanal)", value="@MeuCanal", visible=False)
                        pos_marca = gr.Dropdown(label="Posição", choices=["bottom-right", "top-left", "bottom-center"], value="bottom-right", visible=False)
                        chk_marca.change(fn=lambda x: [gr.update(visible=x)]*2, inputs=chk_marca, outputs=[texto_marca, pos_marca])
                        
                        chk_barra = gr.Checkbox(label="20. Barra de Progresso", value=False)
                        cor_barra = gr.Dropdown(label="Cor da Barra", choices=["Vermelho", "Branco", "Amarelo", "Verde"], value="Vermelho", visible=False)
                        chk_barra.change(fn=lambda x: gr.update(visible=x), inputs=chk_barra, outputs=cor_barra)
                        
                        chk_comp = gr.Checkbox(label="26. Otimizar Compressão (Menor Peso)", value=False)
                        comp_bitrate = gr.Dropdown(label="Qualidade (Bitrate)", choices=["8000k (Alta)", "5000k (Padrão)", "2500k (Web/Leve)", "1000k (Preview Rápido)"], value="5000k (Padrão)", visible=False)
                        chk_comp.change(fn=lambda x: gr.update(visible=x), inputs=chk_comp, outputs=comp_bitrate)
                        
                        chk_cleanup = gr.Checkbox(label="27. Auto-Limpeza de Temporários pós Render", value=True)

                    with gr.Row():
                        btn_preview = gr.Button("👁 Preview (3)", size="sm")
                        prev_n = gr.Slider(minimum=1, maximum=10, step=1, value=3, show_label=False, container=False)
                        
                    btn_video = gr.Button("4️⃣ Montar Vídeo Final", variant="primary", size="lg")
                    video_status = gr.Textbox(label="Status Vídeo", interactive=False)
                    
                with gr.Column(scale=2):
                    video_output = gr.Video(label="🎬 Vídeo Montado", interactive=False)

            yt_titulo = gr.Textbox(visible=False); yt_desc = gr.Textbox(visible=False)

            # LÓGICA DO TEMPO DINÂMICO (Ajuste 3)
            efeitos_chks = [qtd_cenas, chk_cor, chk_croma, chk_glitch, chk_shake, chk_vinheta]
            def atualizar_estimativa(qtd, c1, c2, c3, c4, c5):
                n_ativos = sum(bool(x) for x in [c1, c2, c3, c4, c5])
                tempo = (int(qtd) * 3) * (1 + 0.3 * n_ativos)
                return f"⏳ **Tempo Estimado de Renderização:** ~{int(tempo)} segundos ({n_ativos} efeitos matriciais ativos. {'⚠️ Renderização pode ser longa!' if n_ativos >= 2 else ''})"
            
            for evt in efeitos_chks:
                evt.change(fn=atualizar_estimativa, inputs=efeitos_chks, outputs=aviso_tempo)

            btn_gerar.click(fn=gerar_roteiro, inputs=[url_ref, out_scraper, tema_input, intensidade, qtd_cenas, modo_batch, qtd_batch], outputs=[out_roteiro, out_falas, out_imgs, out_vids, out_meta, df_editor, df_vozes, yt_titulo, yt_desc])
            btn_cancel_batch.click(fn=cancelar_batch, outputs=status_batch)
            btn_play_preview.click(fn=preview_voz_tts, inputs=[voz_tts, taxa_tts, tom_tts], outputs=[audio_preview])
            btn_tts.click(fn=gerar_audios_tts, inputs=[voz_tts, taxa_tts, tom_tts, chk_vozes_mistas, df_vozes, chk_radio, radio_ruido, radio_grave, radio_agudo], outputs=[tts_status, gr.File(visible=False)])
            btn_imagens.click(fn=gerar_imagens, outputs=[gr.Textbox(visible=False), gr.Gallery(visible=False)])
            btn_flow.click(fn=gerar_imagens_flow_playwright, inputs=[pasta_midias], outputs=[gr.Textbox(visible=False), gr.Gallery(visible=False)])
            
            # ORDEM EXATA DOS ARGUMENTOS DA MONTAGEM 
            args_montagem = [
                pasta_midias, upload_midias, chk_ordenar_data, chk_efeitos, formato_video, intensidade_efeito, velocidade_efeito, 
                chk_transicoes, tipo_transicao, dur_transicao, chk_musica, vol_musica, 
                chk_legenda, estilo_legenda, tam_legenda, pos_legenda, chk_queimar_legenda,
                chk_overlay_texto, overlay_estilo, overlay_tam, overlay_pos,
                chk_cor, cor_sat, cor_cont, chk_croma, croma_shift, chk_glitch, glitch_int, chk_shake, shake_int, chk_vinheta, vinheta_int,
                chk_marca, texto_marca, pos_marca, chk_barra, cor_barra, chk_comp, comp_bitrate, chk_cleanup
            ]
            
            btn_video.click(fn=lambda *a: montar_video_core(*a, preview_n=None), inputs=args_montagem, outputs=[video_status, video_output])
            btn_preview.click(fn=lambda *a, n: montar_video_core(*a, preview_n=n), inputs=args_montagem + [prev_n], outputs=[video_status, video_output])

            with gr.Row():
                btn_json = gr.Button("⬇ Exportar JSON"); btn_txt = gr.Button("⬇ Exportar TXT")
                btn_zip = gr.Button("⬇ Exportar TUDO (.zip)"); btn_zip_audio = gr.Button("⬇ Exportar Áudios (.zip)")
                btn_capcut = gr.Button("📦 Exportar Pacote CapCut")

            btn_json.click(fn=lambda: STATE.get("last_json_path", ""), outputs=gr.File(label="JSON"))
            btn_txt.click(fn=lambda: STATE.get("last_txt_path", ""), outputs=gr.File(label="TXT"))
            btn_zip.click(fn=exportar_zip, outputs=gr.File(label="ZIP"))
            btn_zip_audio.click(fn=exportar_zip_audios, outputs=gr.File(label="ZIP Áudios"))
            btn_capcut.click(fn=chamar_export_capcut, outputs=gr.File(label="ZIP CapCut"))

        with gr.Tab("📊 Métricas"):
            gr.Markdown("### 📈 Dashboard de Produção")
            with gr.Row(): met_rot = gr.Number(label="Total de Roteiros", interactive=False); met_vid = gr.Number(label="Total de Sessões", interactive=False)
            with gr.Row(): met_nicho = gr.Textbox(label="Nicho Mais Usado", interactive=False); met_int = gr.Textbox(label="Intensidade", interactive=False)
            met_ult = gr.Textbox(label="Último Gerado", interactive=False)
            btn_met = gr.Button("🔄 Atualizar", variant="primary")
            btn_met.click(fn=carregar_metricas, outputs=[met_rot, met_vid, met_nicho, met_int, met_ult])

        with gr.Tab("🚀 Publicar"):
            gr.Markdown("### 📤 Integração YouTube")
            inp_titulo = gr.Textbox(label="Título do Vídeo"); inp_desc = gr.Textbox(label="Descrição", lines=4)
            inp_tags = gr.Textbox(label="Tags", placeholder="shorts, terror"); inp_priv = gr.Dropdown(label="Privacidade", choices=["private", "unlisted", "public"], value="private")
            btn_pub_yt = gr.Button("📤 Publicar", variant="primary"); out_pub_yt = gr.Textbox(label="Status", interactive=False)
            yt_titulo.change(fn=lambda t: gr.update(value=t), inputs=yt_titulo, outputs=inp_titulo)
            yt_desc.change(fn=lambda d: gr.update(value=d), inputs=yt_desc, outputs=inp_desc)
            btn_pub_yt.click(fn=disparar_youtube, inputs=[inp_titulo, inp_desc, inp_tags, inp_priv], outputs=out_pub_yt)

        with gr.Tab("⚙️ Configurações"):
            cfg_apikey = gr.Textbox(label="Gemini API", value=os.getenv("GEMINI_API_KEY", ""), type="password")
            cfg_modelo = gr.Dropdown(label="Modelo", choices=["gemini-2.5-flash", "gemini-2.5-pro"], value=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), allow_custom_value=True)
            btn_salvar_cfg = gr.Button("💾 Salvar", variant="primary")
            btn_salvar_cfg.click(fn=salvar_config, inputs=[cfg_apikey, cfg_modelo, gr.Checkbox(visible=False), gr.Textbox(visible=False), gr.Checkbox(visible=False), gr.Checkbox(visible=False)], outputs=gr.Textbox(label="Status", interactive=False))

        with gr.Tab("📜 Histórico"):
            hist_list = gr.Textbox(label="Últimos roteiros", lines=15, interactive=False, value=listar_historico())
            with gr.Row():
                hist_index = gr.Number(label="Nº para abrir", value=1, precision=0)
                btn_abrir_hist = gr.Button("📂 Abrir"); btn_limpar_hist = gr.Button("🗑 Limpar", variant="stop")
            hist_status = gr.Textbox(label="Status", interactive=False)
            btn_abrir_hist.click(fn=abrir_historico, inputs=hist_index, outputs=[out_roteiro, out_falas, out_imgs, out_vids, hist_status])
            btn_limpar_hist.click(fn=limpar_historico, outputs=hist_list)

    return demo

def iniciar_edge_silencioso():
    system = platform.system()
    caminho_edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" if system == "Windows" else "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" if system == "Darwin" else "/usr/bin/microsoft-edge"
    try: subprocess.run(["taskkill", "/F", "/IM", "msedge.exe"] if system == "Windows" else ["pkill", "-f", "Microsoft Edge"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except: pass
    if os.path.exists(caminho_edge) or system != "Windows":
        try: subprocess.Popen([caminho_edge, "--remote-debugging-port=9222"])
        except: pass

if __name__ == "__main__":
    iniciar_edge_silencioso()
    build_ui().launch(server_name="0.0.0.0", server_port=7860, show_error=True)