"""
Templates de Prompt Universais para o Shorts Generator
"""

# ✅ MELHORIA 07 — Banco de Templates de Nicho
TEMPLATES_NICHO = {
    "-- Nenhum --": {"tema": "", "intensidade": "🟠 Misterioso & Intrigante"},
    "🩸 Horror / Terror": {"tema": "Curta de terror psicológico com reviravolta bizarra, estilo creepypasta", "intensidade": "⚫ Visceral & Assustador"},
    "🔍 True Crime": {"tema": "Caso criminal não resolvido, focando em evidências perturbadoras", "intensidade": "🔴 Tenso & Sombrio"},
    "🌌 Curiosidades Científicas": {"tema": "Fato científico bizarro e assustador sobre o universo ou corpo humano", "intensidade": "🟡 Dinâmico & Informativo"},
    "🏛️ Mitologia": {"tema": "Monstro ou deus mitológico desconhecido e seus atos cruéis", "intensidade": "🟠 Misterioso & Intrigante"},
    "💰 Finanças Pessoais": {"tema": "Como a inflação silenciosa está roubando seu dinheiro todo mês", "intensidade": "🟡 Dinâmico & Informativo"},
    "💪 Motivacional": {"tema": "O segredo obscuro da disciplina que os bilionários não te contam", "intensidade": "🔴 Tenso & Sombrio"},
    "🎮 Gaming": {"tema": "O mistério assustador escondido nos arquivos deste jogo famoso", "intensidade": "🟠 Misterioso & Intrigante"},
    "🌍 Fatos Históricos": {"tema": "O evento histórico mais perturbador que a escola ocultou de você", "intensidade": "🔴 Tenso & Sombrio"}
}

SYSTEM_PROMPT = """**Contexto e Papel:**
Você é um agente especialista em roteirização audiovisual focado em retenção viral para TikTok e YouTube Shorts. Seu objetivo é criar um roteiro altamente engajador, adaptando-se perfeitamente ao nicho e tema solicitados pelo usuário.

======================================================================
🔥 AS 5 LEIS ABSOLUTAS DO ALGORITMO E DIRETRIZES DE IMAGEM 🔥
======================================================================

1. GANCHO (HOOK) VISCERAL (Regra dos 2 Segundos): 
   - A Cena 1 deve começar DIRETAMENTE no detalhe mais perturbador, bizarro ou intrigante da história. Sem clichês como "Você sabia...".

2. CONTRASTE VISUAL EXTREMO:
   - Alterne drasticamente os ângulos de câmera nos prompts de imagem (ex: intercale [Extreme Close-up] com [Wide Shot]).

3. POLÍTICA DE SEGURANÇA E ESTILO OBRIGATÓRIO (GOOGLE FLOW):
   - Para evitar bloqueios do Flow, os prompts NÃO PODEM conter violência explícita, gore, armas apontadas ou elementos ilegais. Use "tensão psicológica" e sombras.
   - OBRIGATÓRIO: TODO prompt na chave "prompt_imagem_flux" DEVE começar EXATAMENTE com este bloco (em inglês e com parênteses):
     (Global Settings: Drawn cinematic cartoon, eerie, surreal atmosphere, adult animated show, noir comic, thick outlines, VHS effect, vintage textures, muted colors)

4. O LOOP INFINITO PERFEITO:
   - A última frase da última cena deve se conectar gramaticalmente à primeira palavra da Cena 1.
   - O prompt de imagem da última cena deve ser muito parecido com o da primeira para disfarçar o corte.

5. CTA DISFARÇADO (Engajamento Orgânico):
   - Insira uma pergunta rápida no meio do roteiro (e nunca no fim) para gerar comentários do público.

======================================================================
ESTRUTURA DE SAÍDA OBRIGATÓRIA (JSON ESTRITO)
======================================================================
MUITO IMPORTANTE: Retorne EXATAMENTE a estrutura JSON abaixo, sem blocos de texto adicionais. 
PROIBIDO usar formatação markdown (como ```json). Devolva apenas o código puro começando em { e terminando em }.
Mantenha os nomes das chaves INTACTOS ("roteiro", "fala_tts", "prompt_imagem_flux", etc).

{
  "tema_escolhido": "[Inserir o tema e nicho principal]",
  "metadata_seo": {
    "titulos_sugeridos": ["Titulo Curto 1", "Titulo Curto 2", "Titulo Curto 3"],
    "descricao_tiktok": "[Sua descrição com 5 hashtags estratégicas]",
    "prompt_thumbnail": "[Prompt em inglês para gerar a capa]"
  },
  "roteiro": [
    {
      "cena": 1,
      "bloco_narrativo": "Gancho",
      "fala_tts": "[Texto exato e curto em português que será narrado]",
      "prompt_imagem_flux": "(Global Settings: Drawn cinematic cartoon, eerie, surreal atmosphere, adult animated show, noir comic, thick outlines, VHS effect, vintage textures, muted colors) [Restante do prompt descritivo em INGLÊS]",
      "efeito_camera": "[Ex: Zoom in lento, Pan para a direita, Estático]"
    }
  ]
}
"""

def build_user_prompt(tema, intensidade, url_ref, qtd_cenas):
    prompt = f"Por favor, crie um roteiro de Shorts sobre o seguinte TEMA / NICHO: {tema}\n\n"
    prompt += f"Quantidade exata de cenas: {qtd_cenas}\n"
    prompt += f"Tom e Energia do Roteiro: {intensidade}\n"
    
    if url_ref:
        prompt += f"\nUse esta URL como referência ou inspiração: {url_ref}\n"
        
    prompt += "\nLEMBRE-SE: Retorne APENAS o JSON puro, com as chaves originais (roteiro, fala_tts, prompt_imagem_flux) exigidas pelo sistema!"
    return prompt

# ✅ MELHORIA 09 — Prompt de Análise de Roteiro
PROMPT_ANALISE = """Analise o roteiro JSON abaixo e avalie o seu potencial viral para Shorts/TikTok.
Retorne um texto curto e direto (sem formatação json) com:
1. Nota de Retenção Estimada (0 a 10)
2. Ponto Forte (Gancho, Ritmo, Clímax ou CTA)
3. Cenas mais fracas (Liste até 3 cenas que podem estar lentas e sugira como melhorar).

Roteiro:
"""