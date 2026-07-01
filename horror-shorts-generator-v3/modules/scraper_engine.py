import requests
from bs4 import BeautifulSoup
from modules.gemini_client import GeminiClient

def extrair_e_resumir_url(url, api_key, model_name="gemini-2.5-flash"):
    """
    ✅ MELHORIA 14 — Scraper de URL com Resumo IA
    Faz o scraping de uma URL, extrai os parágrafos e gera um resumo enxuto para o roteiro.
    """
    if not url: return "URL vazia. Por favor, insira um link válido."
    if not api_key: return "A API Key do Gemini não está configurada."
    
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'lxml')
        
        # Pega o texto de todos os parágrafos e limita a 15.000 caracteres para não estourar o limite de tokens
        texto_extraido = ' '.join([p.text for p in soup.find_all('p')])[:15000] 
        
        if not texto_extraido.strip():
            return "Não foi possível encontrar texto útil nesta URL."
            
        client = GeminiClient(api_key=api_key, model_name=model_name)
        prompt = f"Por favor, faça um resumo de até 300 palavras do texto abaixo. Foque nos pontos mais bizarros, curiosos ou interessantes que dariam um bom vídeo viral:\n\n{texto_extraido}"
        
        # Geração de conteúdo bruto (sem JSON)
        resp = client.client.models.generate_content(model=client.model_name, contents=prompt)
        return resp.text
        
    except Exception as e:
        return f"❌ Erro ao extrair conteúdo da URL: {str(e)}"