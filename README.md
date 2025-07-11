# Ekstrakcja danych z dokumentów (OpenAI Vision + Streamlit)

Aplikacja webowa do wyciągania danych z faktur, rachunków i innych dokumentów graficznych (PNG, JPG, JPEG, WEBP, GIF) przy użyciu OpenAI Vision (GPT-4o).

## Funkcje
- Wgrywanie pliku graficznego (faktura, rachunek, inny dokument)
- Ekstrakcja danych przez GPT-4o (OpenAI Vision)
- Wyświetlanie danych w tabeli
- Pobieranie danych jako plik Excel
- Szacowanie kosztu przetwarzania obrazu przez OpenAI w PLN
- Obsługa klucza OpenAI przez plik `.env` lub pole w aplikacji

## Wymagania
- Python 3.8+
- Klucz OpenAI API (GPT-4o Vision)

## Instalacja i uruchomienie lokalnie

1. Sklonuj repozytorium lub pobierz pliki:
   ```
   git clone https://github.com/TWOJ_LOGIN/TWOJE_REPO.git
   cd TWOJE_REPO
   ```
2. Zainstaluj wymagane biblioteki:
   ```
   pip install -r requirements.txt
   ```
3. Utwórz plik `.env` i wpisz swój klucz OpenAI:
   ```
   OPENAI_API_KEY=tu_wklej_swoj_klucz
   ```
4. Uruchom aplikację:
   ```
   streamlit run streamlit_app.py
   ```

## Uruchomienie na Streamlit Community Cloud

1. Wgraj repozytorium na GitHub.
2. Wejdź na https://streamlit.io/cloud i połącz z repozytorium.
3. W panelu "Secrets" dodaj:
   ```
   OPENAI_API_KEY=tu_wklej_swoj_klucz
   ```
4. Deploy i korzystaj online!

## Uwaga
- Plik `.env` nie powinien być wrzucany do repozytorium (jest w `.gitignore`).
- Aplikacja nie obsługuje plików PDF – tylko obrazy.

## Licencja
MIT 