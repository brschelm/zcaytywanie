import streamlit as st
import pandas as pd
import base64
from io import BytesIO
from openai import OpenAI
import json
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()
from PIL import Image

# Funkcja do konwersji pliku na base64 (dla obrazów)
def file_to_base64(file):
    return base64.b64encode(file.read()).decode('utf-8')

# Funkcja do przygotowania payloadu dla OpenAI Vision
def prepare_payload(file, filetype):
    if filetype in ["image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"]:
        file.seek(0)
        image_data = file_to_base64(file)
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{filetype};base64,{image_data}",
                "detail": "high"
            }
        }
    else:
        return None

# Funkcja do ekstrakcji danych z dokumentu przez OpenAI Vision
def extract_document_data(openai_key, file, filetype, custom_prompt=None):
    client = OpenAI(api_key=openai_key)
    payload = prepare_payload(file, filetype)
    if not payload:
        raise ValueError("Nieobsługiwany typ pliku.")
    prompt = custom_prompt or "Wyciągnij wszystkie czytelne dane z dokumentu. Dane przedstaw w formacie JSON. Tylko dane, bez komentarzy."
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    payload,
                ],
            }
        ],
    )
    # Spróbuj wyciągnąć JSON z odpowiedzi
    content = response.choices[0].message.content
    try:
        # Usuń ewentualne ```json ... ```
        content = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        return data
    except Exception:
        return {"raw_response": content}

def estimate_vision_cost_pln(image_file, usd_to_pln=4.00, price_per_mpx_usd=0.01):
    # Odczytaj obraz z pliku przesłanego przez Streamlit
    image_file.seek(0)
    img = Image.open(image_file)
    width, height = img.size
    megapixels = (width * height) / 1_000_000
    cost_usd = megapixels * price_per_mpx_usd
    cost_pln = cost_usd * usd_to_pln
    return round(cost_pln, 4), round(megapixels, 2)

# Streamlit UI
def main():
    st.title("Ekstrakcja danych z dokumentów (OpenAI Vision)")
    st.write("Aby korzystać z aplikacji, musisz podać własny klucz OpenAI. Klucz nie jest nigdzie zapisywany.")

    # Obsługa klucza OpenAI w session_state
    if 'openai_key' not in st.session_state:
        st.session_state['openai_key'] = os.getenv("OPENAI_API_KEY")

    if not st.session_state['openai_key']:
        openai_key_input = st.text_input("Wprowadź swój klucz OpenAI:", type="password")
        if openai_key_input:
            st.session_state['openai_key'] = openai_key_input
        st.stop()  # Zatrzymaj aplikację, dopóki nie ma klucza

    openai_key = st.session_state['openai_key']

    # Reszta aplikacji widoczna tylko po podaniu klucza
    custom_prompt = st.text_area("Własny prompt (opcjonalnie)", value="Wyciągnij wszystkie czytelne dane z dokumentu. Dane przedstaw w formacie JSON. Tylko dane, bez komentarzy.")
    uploaded_files = st.file_uploader("Wybierz pliki (PNG, JPEG, JPG, WEBP, GIF)", type=["png", "jpg", "jpeg", "webp", "gif"], accept_multiple_files=True)

    if uploaded_files:
        st.write(f"**Wczytano {len(uploaded_files)} plik(ów):**")
        
        # Szacowanie kosztu dla wszystkich plików
        total_cost = 0
        file_info = []
        
        for i, uploaded_file in enumerate(uploaded_files):
            cost_pln, megapixels = estimate_vision_cost_pln(uploaded_file)
            total_cost += cost_pln
            
            # Pobierz rozdzielczość obrazu
            uploaded_file.seek(0)
            img = Image.open(uploaded_file)
            width, height = img.size
            
            file_info.append({
                'name': uploaded_file.name,
                'cost': cost_pln,
                'megapixels': megapixels,
                'resolution': f"{width}×{height} px"
            })
            
            st.write(f"📄 **{uploaded_file.name}**: {cost_pln} PLN ({megapixels} MPx, {width}×{height} px)")
        
        st.info(f"**Łączny szacowany koszt: {total_cost:.4f} PLN**")
        
        # Przycisk do przetwarzania
        if st.button("🚀 Przetwórz dokumenty", type="primary"):
            all_results = []
            
            with st.spinner(f"Przetwarzanie {len(uploaded_files)} plików przez OpenAI Vision..."):
                for i, uploaded_file in enumerate(uploaded_files):
                    st.write(f"Przetwarzanie {i+1}/{len(uploaded_files)}: {uploaded_file.name}")
                    
                    try:
                        uploaded_file.seek(0)  # Reset, bo był już czytany
                        data = extract_document_data(openai_key, uploaded_file, uploaded_file.type, custom_prompt)
                        
                        # Dodaj nazwę pliku do wyników
                        if isinstance(data, dict):
                            data['plik'] = uploaded_file.name
                        elif isinstance(data, list):
                            for item in data:
                                item['plik'] = uploaded_file.name
                        
                        all_results.append(data)
                        st.success(f"✅ {uploaded_file.name} - przetworzony")
                        
                    except Exception as e:
                        st.error(f"❌ Błąd podczas przetwarzania {uploaded_file.name}: {e}")
                        all_results.append({"plik": uploaded_file.name, "błąd": str(e)})
            
            # Wyświetl wyniki
            if all_results:
                st.success("🎉 Wszystkie pliki przetworzone!")
                
                # Połącz wszystkie wyniki w jeden DataFrame
                combined_data = []
                for result in all_results:
                    if isinstance(result, dict) and "błąd" not in result:
                        combined_data.append(result)
                    elif isinstance(result, list):
                        combined_data.extend(result)
                
                if combined_data:
                    df = pd.json_normalize(combined_data)
                    st.dataframe(df)
                    
                    # Eksport do Excela
                    output = BytesIO()
                    df.to_excel(output, index=False)
                    output.seek(0)
                    now = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        label="📥 Pobierz wszystkie dane jako Excel",
                        data=output,
                        file_name=f"dane_z_dokumentow_{now}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

if __name__ == "__main__":
    main() 