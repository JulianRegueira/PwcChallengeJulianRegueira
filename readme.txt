# Soccer Player Market Analysis

This project implements a **data engineering** and **API** pipeline for soccer player market analysis, leveraging:

* **Bronze → Silver → Gold** (medallion) architecture
* **Raw Ingestion** of CSV/JSON/PDF files
* **ETL** with **pandas** and **SQLModel** into SQLite databases
* **Star schema** in the Gold layer (1 fact + 5 dimensions)
* **FastAPI** REST API with:

  * CRUD (single & batch)
  * Search endpoint with fuzzy & filter support (Typesense + fallback)
  * HTTP Basic Authentication
* **Vector DB**: **Typesense**, containerized via Docker Compose
* **Repository Pattern**, type hints, Pydantic domain models

---

## Architecture

### Medallion Layers

* **Bronze**: Raw landing zone for `argentina_players.csv` and other files
* **Silver**: Cleaned raw table `player` in `silver.db`
* **Gold**: Star schema in `gold.db`:

  * Fact: `factplayerperformance`
  * Dimensions: `playerdimension`, `performancedimension`, `disciplinedimension`, `valuedimension`, `datedimension`

### Overall Flow

1. **Upload** raw files (`/upload/`) → stored in `bronze/`
2. **Silver ETL** (`load_csv_to_silver.py`) → loads raw into `silver.db`
3. **Gold ETL** (`silver_to_gold.py`) → transforms silver → gold star schema in `gold.db`
4. **Typesense** container indexes Silver data on startup
5. **API** exposes endpoints to serve data

---

## Getting Started

### Prerequisites

* Python 3.10+
* Docker & Docker Compose (for Typesense + API)
* Git

### Clone Repo

```bash
git clone https://github.com/<your-username>/soccer-player-market-analysis.git
cd soccer-player-market-analysis
```

### Environment Variables

Create a `.env` file:

```dotenv
API_USER=admin
API_PASS=secret
TYPESENSE_API_KEY=xyz123
TYPESENSE_HOST=localhost
TYPESENSE_PORT=8108
```

### Install Python Dependencies

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\\Scripts\\activate       # Windows
pip install --upgrade pip
pip install -r requirements.txt
```

### Run Locally (without Docker)

1. **Load Silver**:

   ```bash
   python -m app.etl.load_csv_to_silver
   ```
2. **Load Gold**:

   ```bash
   python -m app.etl.silver_to_gold
   ```
3. **Start API**:

   ```bash
   uvicorn app.main:app --reload
   ```
4. **Docs**:
   Open `http://127.0.0.1:8000/docs`

### Run with Docker Compose

```bash
docker-compose up --build
```

* API: `http://localhost:8000`
* Typesense: `http://localhost:8108`

---

## API Endpoints

All endpoints are protected by HTTP Basic Auth (`admin`/`secret` default).

### File Upload

* **POST** `/upload/` — upload CSV/JSON/PDF to `bronze/`

### Players CRUD & Batch

* **GET** `/players/` — list all players
* **GET** `/players/{player_id}` — retrieve single player
* **POST** `/players/` — batch create players
* **DELETE** `/players/{player_id}` — delete player

### Search & Analysis

* **GET** `/players/search` — search by name (fuzzy), filter by position & team
* **GET** `/players/{player_id}/price-ars` — market value in ARS
* **GET** `/players/ranking?limit=10` — top players by composite score

---

## Diagrams

See `diagrams.md` for Mermaid diagrams of:

* Bronze, Silver, Gold ER diagrams
* Overall data lake flow

---

## Future Improvements

* Add **unit & integration tests** for ETL and API
* Integrate **loguru** for structured logging
* Configure **Dev Container** for reproducible development
* Add a **GraphQL** endpoint
* Enhance **DVC** for data versioning

---

*© 2025 Soccer Player Market Analysis*
