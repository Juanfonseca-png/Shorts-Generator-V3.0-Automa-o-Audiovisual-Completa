# 🎬 Horror Shorts Generator V3.0 — A Máquina de Terror

Ferramenta desktop completa em Python para geração e montagem audiovisual de conteúdo viral de terror para YouTube Shorts e TikTok.

## Pilares do Sistema

1. **Roteirização:** API Google Gemini (gemini-2.5-flash)
2. **Narração (TTS):** edge-tts com vozes neurais otimizadas para suspense
3. **Geração de Imagens:** Pollinations.ai (tempo real)
4. **Montador de Vídeo:** moviepy para unir imagens, vídeos de background e áudio

## Requisitos

- Python 3.11+ (recomendado, evite 3.14 por incompatibilidades)
- FFmpeg (necessário para moviepy)

## Setup

### 1. Clone ou extraia o projeto
```bash
cd horror-shorts-generator-v3
```

### 2. Crie e ative o ambiente virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

> **⚠️ Atenção:** Se houver erro de compilação do Pillow, atualize os gerenciadores:
> ```bash
> pip install --upgrade pip setuptools wheel
> pip install Pillow
> ```

> **⚠️ Atenção:** Se houver erro com moviepy, force a versão correta:
> ```bash
> pip uninstall -y moviepy
> pip install moviepy==1.0.3
> ```

### 4. Configure a API Key
```bash
# Windows
copy .env.example .env
# Edite o arquivo .env e insira sua chave:
# GEMINI_API_KEY=sua_chave_aqui
```

> Obtenha sua chave gratuita em: https://aistudio.google.com/apikey

### 5. Execute
```bash
python main.py
```

### 6. Acesse no navegador
```
http://localhost:7860
```

## Estrutura de Pastas

```
horror-shorts-generator-v3/
├── .env                    # Variáveis de ambiente (NUNCA commitar)
├── .env.example            # Template de variáveis
├── requirements.txt        # Dependências Python
├── main.py                 # Entry point (Gradio UI)
├── README.md               # Este arquivo
├── modules/
│   ├── gemini_client.py    # Wrapper da API Gemini (google-genai)
│   ├── prompt_templates.py # Templates de system/user prompt
│   ├── script_engine.py    # Parser e formatador do roteiro
│   ├── tts_engine.py       # edge-tts com vozes sombrias
│   ├── image_engine.py     # Pollinations.ai (geração de imagens)
│   ├── video_engine.py     # moviepy (montagem de vídeo)
│   └── export_engine.py    # Exportação JSON/TXT/ZIP
└── outputs/
    ├── horror_roteiro_*.json
    ├── horror_roteiro_*.txt
    ├── audio_TIMESTAMP/     # Áudios MP3
    ├── imagens_TIMESTAMP/     # Imagens PNG
    └── horror_video_*.mp4   # Vídeos finais
```

## Funcionalidades

### Aba "Gerar Roteiro"
- Gera roteiros de 20 cenas (60 segundos) otimizados para retenção
- Estrutura: Gancho → Falsa Documentação → Uncanny Valley → Clímax + Loop
- Prompts de imagem prontos para Flux/NanoBanana2/Pollinations
- Instruções Ken Burns para edição
- Modo Batch: gere até 20 roteiros de uma vez
- **Geração de áudios TTS** com vozes otimizadas para terror
- **Geração de imagens** via Pollinations.ai
- **Montagem de vídeo final** unindo mídias + áudios
- Exportação em JSON, TXT, ZIP completo ou ZIP de áudios

### Aba "Configurações"
- Teste de conexão com API Gemini
- Escolha de modelo com `allow_custom_value=True` (gemini-2.5-flash, etc.)
- Webhook opcional para envio automático de JSON
- Toggle para geração automática de TTS e imagens
- Salva configurações no `.env`

### Aba "Histórico"
- Lista dos últimos 20 roteiros gerados
- Reabrir roteiros anteriores na interface
- Limpar histórico

## Vozes TTS Disponíveis

| Voz | Descrição | Configuração |
|-----|-----------|--------------|
| **Antônio Neural** | Voz de entidade arrastada e macabra | Pitch -15Hz, Rate -10% |
| **Florian Multilingual** | Narração investigativa poliglote | Pitch -5% |

## Guia de Solução de Erros

### ❌ "404 models/gemini-1.5-pro is not found..."
**Causa:** Google desativou ou renomeou o modelo.
**Solução:** Vá em Configurações e troque para `gemini-2.5-flash` ou cole o nome exato retornado pela API.

### ❌ "JSONDecodeError: Extra data" ou "list object has no attribute get"
**Causa:** O modelo retornou múltiplos blocos JSON ou metadados como lista.
**Solução:** O sistema já tem trava de segurança. Se persistir, gere o roteiro novamente.

### ❌ "edge_tts failed: No audio was received"
**Causa:** Nome da voz incorreto no servidor da Microsoft.
**Solução:** Use os nomes oficiais: `pt-BR-AntonioNeural` ou `de-DE-FlorianMultilingualNeural`.

### ❌ "ModuleNotFoundError: No module named 'moviepy.editor'"
**Causa:** MoviePy 2.0 mudou a estrutura e removeu `.editor`.
**Solução:**
```bash
pip uninstall -y moviepy
pip install moviepy==1.0.3
```

### ❌ Falha na compilação do Pillow (letras vermelhas no pip install)
**Causa:** Python 3.14 é muito recente, sem pacotes pré-compilados.
**Solução:**
```bash
pip install --upgrade pip setuptools wheel
pip install Pillow
```
Ou use Python 3.11/3.12.

## Arquitetura do Roteiro (60s / 20 Cenas)

| Bloco | Cenas | Tempo | Função |
|-------|-------|-------|--------|
| Gancho | 1-2 | 0-6s | Parar a rolagem |
| Falsa Documentação | 3-7 | 6-21s | Criar credibilidade |
| Uncanny Valley | 8-16 | 21-48s | Escalar o terror |
| Clímax + Loop | 17-20 | 48-60s | Jumpscare + loop infinito |

## Regras de Conteúdo
- ❌ Sem gore, violência gráfica ou nudez
- ✅ Terror psicológico, atmosfera, sugestão, distorção
- ✅ Loop infinito: última frase conecta-se à primeira palavra da cena 1

## Licença
Uso pessoal e comercial sob sua própria responsabilidade. Sempre inclua o disclaimer de ficção nos vídeos publicados.
