import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def publicar_youtube(video_path, titulo, descricao, tags, privacidade):
    if not os.path.exists(video_path):
        return "❌ Erro: O arquivo de vídeo não foi encontrado. Monte o vídeo primeiro."

    token_path = os.path.join("outputs", "youtube_token.json")
    client_secrets_path = "client_secrets.json"
    
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    if not creds or not creds.valid:
        if not os.path.exists(client_secrets_path):
            return "❌ Erro Crítico: 'client_secrets.json' não encontrado na raiz do projeto. Baixe este arquivo no Google Cloud Console."
            
        try:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        except Exception as e:
            return f"❌ Erro na Autenticação OAuth: {str(e)}"
            
    try:
        youtube = build("youtube", "v3", credentials=creds)
        body = {
            "snippet": {
                "title": titulo,
                "description": descricao,
                "tags": [t.strip() for t in tags.split(",") if t.strip()],
                "categoryId": "24" 
            },
            "status": {
                "privacyStatus": privacidade
            }
        }
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        
        response = request.execute()
        return f"✅ Publicação bem-sucedida! URL: https://youtu.be/{response.get('id')}"
        
    except Exception as e:
        return f"❌ Erro no upload para o YouTube: {str(e)}"