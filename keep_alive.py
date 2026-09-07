from playwright.sync_api import sync_playwright

URL_STREAMLIT = "https://jwozcpf8aabf7rq5g8gryt.streamlit.app" 

def despertar_app():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"🌍 Visitando {URL_STREAMLIT}...")
        try:
            page.goto(URL_STREAMLIT, wait_until="networkidle")
            page.wait_for_timeout(5000) 
            
            boton_despertar = page.locator("button:has-text('Yes, get this app back up!')")
            
            if boton_despertar.count() > 0:
                print("💤 ¡La app estaba dormida! Haciendo clic para despertarla...")
                boton_despertar.first.click()
                page.wait_for_timeout(15000) 
                print("🚀 App despertada con éxito.")
            else:
                print("✅ La app ya estaba despierta y operativa.")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    despertar_app()
