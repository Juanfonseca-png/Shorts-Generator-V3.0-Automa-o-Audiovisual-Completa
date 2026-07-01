import json
import time
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def test_connection(self):
        try:
            self.client.models.generate_content(model=self.model_name, contents="Ping")
            return True, "✅ Conexão OK!"
        except Exception as e:
            logger.error(f"Erro de conexão com o Gemini: {e}")
            return False, f"❌ Erro de conexão: {str(e)}"

    def generate_script(self, system_prompt: str, user_prompt: str, retries: int = 3):
        for attempt in range(retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        temperature=0.7
                    )
                )
                
                text_response = response.text.strip()
                if text_response.startswith("```json"):
                    text_response = text_response.replace("```json", "").replace("```", "").strip()
                    
                return json.loads(text_response)
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON inválido retornado pelo Gemini: {e}")
                raise ValueError(f"O Gemini retornou um JSON inválido: {e}")
            except Exception as e:
                logger.error(f"Falha na tentativa {attempt + 1}: {e}")
                if "429" in str(e) or "quota" in str(e).lower():
                    if attempt < retries - 1:
                        time.sleep(30)
                        continue
                raise Exception(f"Erro na API: {str(e)}")