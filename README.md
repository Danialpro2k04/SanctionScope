# SanctionScope

SanctionScope is a modern, standalone FastAPI regulatory compliance engine. It screens company names against the global [OpenSanctions](https://www.opensanctions.org/) dataset to identify sanctioned entities, calculate risk scores, and maintain an immutable audit trail.

To prevent bad actors from evading detection via transliterations, typos, or translations, SanctionScope uses a three-tier matching architecture:

1. **Exact Match:** Baseline 1-to-1 string comparison.
2. **Fuzzy Match:** Typo and misspelling detection using Jaro-Winkler and Levenshtein distance (`RapidFuzz`).
3. **Semantic Match:** AI-powered conceptual matching and translation detection using a Sentence Transformer and a `Qdrant` vector database.

## Architecture

* **Framework:** FastAPI (Python)
* **AI/Embeddings:** Sentence Transformer (multilingual model — required for cross-script matches like Cyrillic ↔ Latin transliterations)
* **Vector Database:** Qdrant (Docker)
* **Fuzzy Engine:** RapidFuzz
* **Audit Trail:** SQLite (append-only)

## Project Structure

```
sanctionscope/
├── app/
│   ├── main.py             # FastAPI app, /screen and /screen/compare routes
│   ├── normalization.py
│   ├── matching/
│   │   ├── exact.py
│   │   ├── fuzzy.py
│   │   └── semantic.py
│   ├── schemas.py
│   ├── qdrant_client.py
│   └── audit.py
├── scripts/
│   ├── ingest.py            # download + filter + parse OpenSanctions data
│   └── embed_and_load.py    # embed names + aliases, upsert to Qdrant
├── docker-compose.yml
├── requirements.txt
├── data/                    # gitignored — holds the downloaded dataset
└── README.md
```

## Prerequisites

* Python 3.10+
* Docker Desktop (for running the Qdrant vector database)

## Installation & Setup

**1. Clone the repository and navigate into it**

```bash
git clone https://github.com/Danialpro2k04/SanctionScope.git
cd SanctionScope
```

**2. Set up the virtual environment and install dependencies**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3. Configure environment variables**

Copy the example file and fill in any required values (e.g. Qdrant host/port if not using the defaults):

```bash
cp .env.example .env
```

**4. Start the Vector Database**

```bash
docker-compose up -d
```

**5. Ingest Data and Generate AI Vectors**

Download the latest OpenSanctions dataset, filter the entities, and load them into Qdrant:

```bash
mkdir -p data
python scripts/ingest.py
python scripts/embed_and_load.py
```

**6. Start the API Server**

```bash
uvicorn app.main:app --reload
```

The API is now available at `http://127.0.0.1:8000` (interactive docs at `/docs`).

## Usage

Send a POST request to the `/screen` endpoint with an entity name. The engine evaluates the name against all three matching strategies and returns a risk level (`RED`, `YELLOW`, or `GREEN`) alongside matched evidence.

**Example Request:**

```bash
curl -X POST "http://127.0.0.1:8000/screen" \
     -H "Content-Type: application/json" \
     -d '{"name": "Russian Defense Export"}'
```

**Example Response:**

```json
{
  "audit_id": "a1f14b87-29c0-47c7-ad94-6bc62d3633ed",
  "query_name": "Russian Defense Export",
  "risk_level": "RED",
  "matches": [
    {
      "matched_name": "Rosoboronexport OJSC (ROE)",
      "sanctions_programs": ["US-SSI", "EU-RUS"],
      "evidence": {
        "exact_match": false,
        "jaro_winkler_score": 0.9545,
        "matched_on": "alias",
        "matched_alias_text": "Russian Defence Export"
      },
      "combined_score": 0.9545
    }
  ],
  "screened_at": "2026-09-18T19:09:46.800908"
}
```

## Matching Strategy Comparison

A debug endpoint, `GET /screen/compare?name=...`, returns each strategy's raw top candidates separately (rather than combined), useful for demonstrating exactly what exact/fuzzy matching misses that semantic search catches — e.g. a Cyrillic canonical name matched only via a Latin-script alias.

## Audit Trail

Every `/screen` call is logged to an append-only SQLite table (`screening_log`) with timestamp, query, full result, and processing time — no updates or deletes, by design, so the log can later be wrapped in tamper-evident hash chaining without any retrofit.

## Scope

This is a focused three-strategy comparison, not a full production entity-resolution system — it intentionally does not include lexical (BM25) retrieval, a trained ranking model, or rule-based override logic.