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
            st.experimental_rerun()
        st.stop()  # Zatrzymaj aplikację, dopóki nie ma klucza

    openai_key = st.session_state['openai_key']

    # Reszta aplikacji widoczna tylko po podaniu klucza
    custom_prompt = st.text_area("Własny prompt (opcjonalnie)", value="Wyciągnij wszystkie czytelne dane z dokumentu. Dane przedstaw w formacie JSON. Tylko dane, bez komentarzy.")
    uploaded_file = st.file_uploader("Wybierz plik (PNG, JPEG, JPG, WEBP, GIF)", type=["png", "jpg", "jpeg", "webp", "gif"])

    if uploaded_file:
        with st.spinner("Przetwarzanie pliku przez OpenAI Vision..."):
            try:
                # Szacowanie kosztu
                cost_pln, megapixels = estimate_vision_cost_pln(uploaded_file)
                st.info(f"Szacowany koszt przetworzenia tego obrazu: {cost_pln} zł (rozmiar: {megapixels} MPx)")
                uploaded_file.seek(0)  # Reset, bo był już czytany
                data = extract_document_data(openai_key, uploaded_file, uploaded_file.type, custom_prompt)
                if isinstance(data, dict):
                    df = pd.json_normalize(data)
                elif isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame({"raw_response": [str(data)]})
                st.success("Dane wyciągnięte!")
                st.dataframe(df)

                # Eksport do Excela
                output = BytesIO()
                df.to_excel(output, index=False)
                output.seek(0)
                now = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="Pobierz jako Excel",
                    data=output,
                    file_name=f"dane_z_dokumentu_{now}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Błąd podczas przetwarzania: {e}")

if __name__ == "__main__":
    main() 