# 1. Zaczynamy od pobrania Pythona 3.11.9
FROM python:3.11.9-slim

# 2. Tworzymy główny folder w kontenerze
WORKDIR /app

# 3. Kopiujemy listę pakietów
COPY requirements.txt .

# 4. Instalujemy biblioteki z listy
RUN pip install --no-cache-dir -r requirements.txt

# 5. Kopiujemy nasz folder z kodem z lokalnego "app"
COPY ./app ./app

# 6. Komenda włączająca uvicorn na całą sieć (0.0.0.0)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]