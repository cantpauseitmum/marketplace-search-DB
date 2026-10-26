# 🗄️ MarketplaceSearch - Database Module (`marketplace-search-DB`)

Dedykowany moduł bazy danych i persystencji dla aplikacji **MarketplaceSearch** (agregatora ogłoszeń z OLX, Allegro, Allegro Lokalnie oraz Facebook Marketplace).

Moduł odpowiada za:
- Rejestrację i historię zapytań użytkownika (`search_queries`)
- Zapis, aktualizację oraz deduplikację pobranych ofert (`offers`)
- Zarządzanie polubionymi/zapisanymi ofertami (bookmarking)
- Rejestrowanie telemetrii i logów scraperów (`scraper_logs`)
- Wsparcie dla trybu **SQLite WAL Mode** (Write-Ahead Logging) oraz kompatybilność z **PostgreSQL**

---

## 🏗️ Struktura bazy danych

### Schemat relacyjny (`schema.sql`)

```sql
search_queries (1) ───< (N) offers
search_queries (1) ───< (N) scraper_logs
```

### 1. Tabela `search_queries`
Przechowuje historię wyszukiwań użytkownika wraz z parametrami filtrowania:
- `id` (INTEGER, PK): Identyfikator zapytania
- `query_text` (TEXT): Wyszukiwana fraza (np. "Switch 2")
- `location` (TEXT): Nazwa miejscowości / lokalizacja
- `radius_km` (INTEGER): Promień poszukiwań w km
- `search_in_description` (INTEGER): Flaga wyszukiwania w opisie (0/1)
- `min_price` / `max_price` (REAL): Widełki cenowe
- `sources_used` (TEXT): Użyte źródła (np. "OLX,Allegro,Allegro Lokalnie,Facebook Marketplace")
- `results_count` (INTEGER): Liczba znalezionych unikalnych ofert
- `created_at` (TIMESTAMP): Znacznik czasu UTC

### 2. Tabela `offers`
Przechowuje zagregowane ogłoszenia ze wszystkich serwisów:
- `id` (INTEGER, PK): Unikalny identyfikator oferty w systemie
- `external_id` (TEXT): ID oferty w portalu źródłowym
- `source` (TEXT): Nazwa serwisu (`OLX`, `Allegro`, `Allegro Lokalnie`, `Facebook Marketplace`)
- `title` (TEXT): Tytuł ogłoszenia
- `description` (TEXT): Treść opisu
- `price` (REAL): Cena numeryczna
- `currency` (TEXT): Waluta (domyślnie `PLN`)
- `price_formatted` (TEXT): Cena sformatowana dla użytkownika (np. "1 850 zł")
- `url` (TEXT): Bezpośredni link do ogłoszenia
- `image_url` (TEXT): Link do miniatury zdjęcia
- `location` (TEXT): Lokalizacja tekstowa (np. "Warszawa, Mokotów")
- `city` (TEXT): Miasto
- `distance_km` (REAL): Obliczona odległość w km
- `published_at` (TEXT): Czas publikacji
- `query_id` (INTEGER, FK): Powiązanie z zapytaniem wyszukiwania
- `is_bookmarked` (INTEGER): Czy oferta jest polubiona/zapisana (0/1)
- `created_at` / `updated_at` (TIMESTAMP): Czas utworzenia / aktualizacji
- **Deduplikacja**: `CONSTRAINT uq_source_url UNIQUE (source, url)`

### 3. Tabela `scraper_logs`
Rejestruje wydajność i statusy każdego odpytania scrapera:
- `id` (INTEGER, PK): ID logu
- `source` (TEXT): Źródło (`OLX`, `Allegro`, itp.)
- `query_id` (INTEGER, FK): ID zapytania
- `status` (TEXT): Status wykonania (`OK`, `WARNING`, `ERROR`, `FALLBACK`)
- `items_found` (INTEGER): Liczba znalezionych ofert
- `latency_ms` (INTEGER): Czas wykonania zapytania w milisekundach
- `message` (TEXT): Dodatkowe informacje lub treść błędu
- `created_at` (TIMESTAMP): Czas logowania

---

## ⚡ Szybki start

Moduł działa na czystej instalacji Pythona 3.10+ (standard library `sqlite3`), bez konieczności instalowania zewnętrznych bibliotek.

### Inicjalizacja bazy i wypełnienie danymi testowymi
```bash
python3 init_db.py --seed
```

### Podgląd statystyk bazy danych
```bash
python3 init_db.py --stats
```

### Reset i wyczyszczenie bazy danych
```bash
python3 init_db.py --reset --seed
```

### Uruchomienie testów jednostkowych
```bash
python3 test_db.py
```

---

## 🐍 Wykorzystanie w kodzie Pythona

```python
from db_manager import DatabaseManager

# Inicjalizacja połączenia (automatycznie tworzy schemat i włącza WAL)
db = DatabaseManager("marketplace.db")

# 1. Zapis nowego zapytania
q_id = db.record_search_query(
    query_text="Switch 2",
    location="Warszawa",
    radius_km=25,
    search_in_description=True,
    min_price=1000,
    max_price=2500,
)

# 2. Zapis pojedynczej oferty z deduplikacją
offer_id = db.upsert_offer({
    "source": "OLX",
    "external_id": "olx-12345",
    "title": "Nintendo Switch 2 OLED",
    "price": 1850.0,
    "url": "https://www.olx.pl/d/oferta/test.html",
    "location": "Warszawa, Mokotów",
    "city": "Warszawa",
}, query_id=q_id)

# 3. Pobieranie ofert z filtrowaniem i paginacją
results = db.get_offers(
    query="Switch",
    location="Warszawa",
    min_price=1500,
    sort_by="price_asc",
    limit=20,
)
print(f"Znaleziono {results['total']} ofert:")
for item in results["items"]:
    print(f"- [{item['source']}] {item['title']}: {item['price_formatted']}")

# 4. Przełączenie polubienia (bookmark)
is_bookmarked = db.toggle_bookmark(offer_id)
```

---

## 🐳 Uruchomienie w Dockerze

```bash
docker compose up --build
```
