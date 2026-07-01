"""
Motor de formatação e extração do roteiro JSON gerado pela IA.
"""

def formatar_roteiro(data):
    """
    Formata o dicionário JSON inteiro em um texto legível para exibição na interface principal.
    """
    if not isinstance(data, dict) or "roteiro" not in data:
        return "Formato de roteiro inválido ou não encontrado."
    
    linhas = []
    tema = data.get("tema_escolhido", "Tema não definido")
    linhas.append(f"🎭 TEMA: {tema}\n")
    linhas.append("=" * 50 + "\n")
    
    for cena in data["roteiro"]:
        num = cena.get("cena", "?")
        bloco = cena.get("bloco_narrativo", "Cena")
        fala = cena.get("fala_tts", "")
        img = cena.get("prompt_imagem_flux", "")
        cam = cena.get("efeito_camera", "")
        
        linhas.append(f"🎬 CENA {num} [{bloco}]")
        linhas.append(f"🎙️ FALA: {fala}")
        linhas.append(f"🖼️ IMAGEM: {img}")
        linhas.append(f"🎥 CÂMERA: {cam}")
        linhas.append("-" * 50)
        
    return "\n".join(linhas)


def extrair_falas(data):
    """
    Extrai as falas do JSON gerado, garantindo retorno em formato de lista.
    """
    try:
        if isinstance(data, dict) and "roteiro" in data:
            return [cena.get("fala_tts", "") for cena in data["roteiro"]]
        return []
    except Exception as e:
        print(f"Erro ao extrair falas: {e}")
        return []


def extrair_prompts_imagem(data):
    """
    Extrai os prompts de imagem do JSON, garantindo retorno em formato de lista.
    """
    try:
        if isinstance(data, dict) and "roteiro" in data:
            return [cena.get("prompt_imagem_flux", "") for cena in data["roteiro"]]
        return []
    except Exception as e:
        print(f"Erro ao extrair prompts de imagem: {e}")
        return []


def extrair_prompts_video(data):
    """
    Extrai os comandos de câmera do JSON, garantindo retorno em formato de lista.
    """
    try:
        if isinstance(data, dict) and "roteiro" in data:
            return [cena.get("efeito_camera", "") for cena in data["roteiro"]]
        return []
    except Exception as e:
        print(f"Erro ao extrair efeitos de câmera: {e}")
        return []


def extrair_metadata(data):
    """
    Extrai as informações de SEO e títulos do JSON.
    """
    if not isinstance(data, dict):
        return {}
    
    meta = data.get("metadata_seo", {})
    return {
        "titulos": meta.get("titulos_sugeridos", []),
        "descricao": meta.get("descricao_tiktok", ""),
        "thumbnail": meta.get("prompt_thumbnail", "")
    }