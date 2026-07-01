import os
import time
import base64
from playwright.sync_api import sync_playwright

def gerar_imagens_no_flow(prompts: list[str], pasta_saida: str, url_da_ferramenta: str):
    os.makedirs(pasta_saida, exist_ok=True)
    arquivos_baixados = []
    urls_baixadas = set()
    
    print("A conectar ao Edge aberto...")
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()
            
            page.goto(url_da_ferramenta)
            print("Página carregada. A injetar botão de arranque...")
            
            page.evaluate("""
                () => {
                    const btnAntigo = document.getElementById('botao-injetor-espera') || document.getElementById('botao-injetor-clicado');
                    if(btnAntigo) btnAntigo.remove();

                    const btn = document.createElement('button');
                    btn.id = 'botao-injetor-espera'; 
                    btn.innerHTML = '🤖 INICIAR GERAÇÃO EM MASSA';
                    btn.style.position = 'fixed';
                    btn.style.bottom = '30px';
                    btn.style.left = '50%';
                    btn.style.transform = 'translateX(-50%)';
                    btn.style.zIndex = '999999';
                    btn.style.padding = '20px 40px';
                    btn.style.fontSize = '20px';
                    btn.style.fontWeight = 'bold';
                    btn.style.backgroundColor = '#FF4500';
                    btn.style.color = '#FFFFFF';
                    btn.style.border = 'none';
                    btn.style.borderRadius = '10px';
                    btn.style.cursor = 'pointer';
                    
                    btn.onclick = () => {
                        btn.id = 'botao-injetor-clicado'; 
                        btn.innerHTML = '⏳ A Trabalhar... Tire as mãos do teclado!';
                        btn.style.backgroundColor = '#555555';
                        btn.style.cursor = 'not-allowed';
                    };
                    document.body.appendChild(btn);
                }
            """)
            
            print("A aguardar que clique no botão no ecrã do Edge...")
            page.wait_for_selector("#botao-injetor-clicado", state="attached", timeout=0)
            print("Botão clicado! Iniciando Geração...")
            
            page.evaluate("() => { const btn = document.getElementById('botao-injetor-clicado'); if(btn) btn.remove(); }")
            
            for i, prompt in enumerate(prompts, start=1):
                print(f"\n🎬 Cena {i}/{len(prompts)} | Enviando prompt...")
                try:
                    caixa_texto = page.locator('textarea:visible, [contenteditable="true"]:visible').first
                    caixa_texto.wait_for(state="visible", timeout=10000)
                    
                    caixa_texto.click(force=True)
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")
                    time.sleep(0.5)
                    
                    page.keyboard.insert_text(prompt)
                    time.sleep(0.5)
                    page.keyboard.press("Enter")
                    
                    print(f"⏳ Aguardando IA do Google desenhar a imagem {i} (50 segundos)...")
                    page.wait_for_timeout(50000)
                    
                    imagens_geradas = page.locator('img[alt="Imagem gerada"]') 
                    qtd_imagens = imagens_geradas.count()
                    
                    elemento_img = None
                    if qtd_imagens > 0:
                        for idx in range(qtd_imagens):
                            el = imagens_geradas.nth(idx)
                            src = el.get_attribute("src")
                            if src and src not in urls_baixadas:
                                urls_baixadas.add(src)
                                elemento_img = el
                                break
                        
                        if not elemento_img:
                            elemento_img = imagens_geradas.first
                            
                        elemento_img.scroll_into_view_if_needed()
                        page.wait_for_timeout(1500) 
                        
                        base64_data = elemento_img.evaluate('''async (img) => {
                            try {
                                const canvas = document.createElement('canvas');
                                canvas.width = img.naturalWidth || 1024;
                                canvas.height = img.naturalHeight || 1024;
                                const ctx = canvas.getContext('2d');
                                ctx.drawImage(img, 0, 0);
                                return canvas.toDataURL('image/jpeg', 1.0);
                            } catch (e) {
                                const res = await fetch(img.src);
                                const blob = await res.blob();
                                return new Promise((resolve) => {
                                    const reader = new FileReader();
                                    reader.onloadend = () => resolve(reader.result);
                                    reader.readAsDataURL(blob);
                                });
                            }
                        }''')
                        
                        header, encoded = base64_data.split(",", 1)
                        caminho_imagem = os.path.join(pasta_saida, f"cena_{i:02d}.jpg")
                        with open(caminho_imagem, "wb") as f:
                            f.write(base64.b64decode(encoded))
                            
                        arquivos_baixados.append(caminho_imagem)
                        print(f"✅ Cena {i} salva!")
                    else:
                        print(f"❌ Imagem {i} não apareceu.")
                    time.sleep(2)
                except Exception as e:
                    print(f"❌ Erro na cena {i}: {e}")
                    
            print("\n🎉 Lote finalizado!")
            browser.close() 
            
        except Exception as e:
            if "Target closed" in str(e) or "connect" in str(e).lower():
                raise Exception("Erro de ligação. O Edge foi aberto com a porta 9222?")
            else:
                raise e
    return arquivos_baixados