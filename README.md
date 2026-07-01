# 🎬 Shorts Generator V3.0 — Automação Audiovisual Completa

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Gradio](https://img.shields.io/badge/UI-Gradio-orange)
![Gemini](https://img.shields.io/badge/AI-Google_Gemini-yellow)
![Playwright](https://img.shields.io/badge/RPA-Playwright-green)

O **Shorts Generator V3.0** é uma ferramenta desktop open-source desenvolvida para automatizar ponta a ponta a criação de vídeos curtos virais. 

O objetivo deste projeto foi integrar múltiplos motores de processamento — desde a roteirização via LLMs até a manipulação matemática de pixels em pós-produção — criando uma verdadeira "ilha de edição autônoma" em Python.

---

## 🚀 Desafios Técnicos Resolvidos (Destaques da Arquitetura)

Este projeto foi construído para lidar com gargalos reais de produção de conteúdo, utilizando abordagens avançadas de engenharia de software:

* **RPA "Stealth" com Playwright:** Para contornar bloqueios de automação em geradores de imagem da web, a ferramenta assume o controle de uma instância real do Microsoft Edge via porta de depuração remota (`9222`), injetando scripts na DOM e extraindo imagens diretamente do Canvas via Base64.
* **Processamento de Vídeo Matricial (Numpy + MoviePy):** Em vez de depender de softwares pesados de edição, os efeitos de vídeo (Glitch, Aberração Cromática, Câmera Shake e Color Grading) foram programados do zero usando manipulação de arrays multidimensionais (Numpy) frame a frame.
* **Sincronização Dinâmica de Legendas sem Whisper:** Para evitar o peso de modelos de transcrição locais, foi desenvolvido um algoritmo matemático leve que calcula o timestamp de *overlays* de texto dividindo o tempo do áudio pelo peso silábico (contagem de vogais) de cada palavra.
* **Autenticação OAuth 2.0 do YouTube:** Implementação do fluxo completo do Google Client API para gerenciar tokens localmente e fazer upload direto sem intervenção manual após o primeiro login.
* **Fila de Processamento (Batch) Multithreading:** Uso de `threading.Event()` para gerenciar filas assíncronas no backend do Gradio, permitindo o cancelamento seguro de processos pesados sem travar a interface.

---

## ✨ Funcionalidades do Sistema

* **Cérebro de Conteúdo (Gemini 2.5):** Criação de roteiros, metadados de SEO e extração/resumo de conteúdo de URLs externas via `BeautifulSoup`.
* **Motor de Áudio:** Manipulação espectral com `PyDub` para aplicar filtros passa-alta/baixa (Efeito Rádio FM) sobre vozes neurais (Edge TTS).
* **Edição Não-Linear:** Movimentos de câmera (Ken Burns), transições e legendas em formato `SRT` (Hardcoded via subprocessamento do `FFmpeg`).
* **Tradução Multilíngue:** Tradução da estrutura JSON para múltiplos idiomas regenerando a cronologia de áudios automaticamente.
* **Exportação Modular:** Opção de empacotar imagens, áudios e instruções em um arquivo `.zip` mapeado para importação rápida no CapCut.

---

## 🛠️ Instalação e Configuração

**Pré-requisitos:** Python 3.10+, FFmpeg configurado no `PATH` e Microsoft Edge.

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/seu-usuario/horror-shorts-generator-v3.git](https://github.com/seu-usuario/horror-shorts-generator-v3.git)
   cd horror-shorts-generator-v3

1-Crie o ambiente virtual e instale as dependências:

Bash
python -m venv venv
# Ative no Windows: venv\Scripts\activate
# Ative no Linux/Mac: source venv/bin/activate

pip install -r requirements.txt
playwright install

2-Configuração de Variáveis de Ambiente:

Renomeie .env.example para .env.

Insira a sua GEMINI_API_KEY.

(Opcional) Para publicar via API, adicione o client_secrets.json do Google Cloud na raiz do projeto.

3-Inicie o servidor:

Bash
python main.py
