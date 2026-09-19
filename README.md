# SanctionScope

SanctionScope is a three-tier sanctions screening engine. It checks a company or entity name against a global sanctions dataset ([OpenSanctions](https://www.opensanctions.org/) — OFAC, EU, UN, and other lists) and returns a risk level, using exact matching, fuzzy string matching, and AI-powered semantic search together, not just one.

Exact string matching alone misses a lot: transliterations (a Cyrillic name romanized differently across databases), aliases and shell-company names, typos, and reordered legal suffixes. SanctionScope combines three matching strategies so a name can be caught even when it doesn't look identical to what's on file.

## How it works

1. **Exact match** — is the cleaned query character-for-character identical to a name or alias on file? If yes, it's an instant high-confidence match, no further scoring needed.
2. **Fuzzy match** ([RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) — Jaro-Winkler + Levenshtein) — catches spelling distance: typos, minor formatting differences, reordered legal suffixes ("JSC Electroagregat" vs. "Electroagregat JSC").
3. **Semantic match** (multilingual sentence embeddings + [Qdrant](https://qdrant.tech/) vector search) — catches conceptual and cross-script similarity that spelling-distance algorithms can't see, such as an English translation of a Cyrillic entity name.

The engine takes the **strongest signal across all three tiers**, not an average — a translation and a typo are different problems, and diluting one signal with another loses information. See [Risk scoring logic](#risk-scoring-logic) below for the exact thresholds.

## Benchmark: does the semantic tier actually help?

10 test queries run against a live dataset of 24,880 sanctioned entities, comparing each tier's top match:

| # | Test case | Exact | Fuzzy | Semantic | Combined | Risk |
|---|---|---|---|---|---|---|
| 1 | Exact canonical name | 1.00 | 1.00 | 0.97 | 1.00 | RED |
| 2 | Exact alias | 1.00 | 1.00 | 1.00 | 1.00 | RED |
| 3 | Canonical name with a typo | — | 0.98 | 0.95 | 0.98 | RED |
| 4 | Legal-suffix / word-order variant | 1.00 | 1.00 | 1.00 | 1.00 | RED |
| 5 | Transliterated Cyrillic → Latin alias | — | 0.97 | 1.00 | 1.00 | RED |
| 6 | Cyrillic canonical queried directly | 1.00 | 1.00 | 1.00 | 1.00 | RED |
| 7 | English translation of a Cyrillic entity | — | 0.99 | 1.00 | 1.00 | RED |
| 8 | Abbreviated / reworded alias | — | 0.84 | **0.96** | 0.96 | RED |
| 9 | Partial / abbreviated name | — | 0.84 | **0.95** | 0.95 | RED |
| 10 | Unrelated business (true negative) | — | 0.80 | 0.86 | 0.86 | YELLOW |

Rows 8 and 9 are where the semantic tier earns its place: fuzzy matching alone lands at a borderline 0.84, while semantic search recognizes the underlying entity at 0.95–0.96 by matching on meaning rather than spelling.

Row 10 is an honest edge case worth explaining rather than hiding: it was meant as a clean "unrelated business" control, but the semantic tier scored it 0.86 because it found genuinely topically related coffee-industry companies in the dataset. That's a real, known property of embedding-based search — it measures conceptual closeness, not identity — and it's exactly why the threshold logic routes anything below 0.90 to human review (`YELLOW`) instead of auto-clearing or auto-blocking it.

You can reproduce this yourself with `scripts/compare_test.py` (see [Testing](#testing) below) once you've loaded your own dataset.

## Architecture

* **Framework:** FastAPI (Python)
* **AI/Embeddings:** `intfloat/multilingual-e5-small` (Sentence Transformers) — multilingual, required for cross-script matches like Cyrillic ↔ Latin transliterations
* **Vector Database:** Qdrant (Docker)
* **Fuzzy Engine:** RapidFuzz (Jaro-Winkler + Levenshtein, computed independently)
* **Audit Trail:** SQLite (append-only)

## Project structure

```
sanctionscope/
├── app/
│   ├── main.py             # FastAPI app, /screen and /screen/compare routes
│   ├── normalization.py    # text normalization for fuzzy matching + semantic embedding
│   ├── matching/
│   │   ├── exact.py
│   │   ├── fuzzy.py
│   │   └── semantic.py
│   ├── schemas.py
│   └── audit.py
├── scripts/
│   ├── ingest.py            # download + filter + parse OpenSanctions data
│   ├── embed_and_load.py    # embed names + aliases, upsert to Qdrant
│   └── compare_test.py      # run a benchmark set of queries against /screen/compare
├── docker-compose.yml
├── requirements.txt
├── data/                    # gitignored — holds the downloaded dataset
└── README.md
```

## Prerequisites

* Python 3.10+
* Docker Desktop (for running the Qdrant vector database)

## Installation & setup

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

**3. Start the vector database**

```bash
docker-compose up -d
```

**4. Ingest data and generate AI vectors**

Download the OpenSanctions dataset, filter the entities, and embed + load canonical names and aliases into Qdrant:

```bash
mkdir -p data
python scripts/ingest.py
python scripts/embed_and_load.py
```

The embed step downloads a multilingual embedding model on first run and can take a few minutes given the dataset size (aliases are embedded individually alongside canonical names).

**5. Start the API server**

```bash
uvicorn app.main:app --reload
```

The API is now available at `http://127.0.0.1:8000` (interactive docs at `/docs`).

## Usage

Send a POST request to the `/screen` endpoint with an entity name. The engine evaluates the name against all three matching strategies and returns a risk level (`RED`, `YELLOW`, or `GREEN`) alongside matched evidence.

### Risk scoring logic

- An **exact match** on the cleaned query always sets `combined_score = 1.0` and the overall `risk_level` to `RED` — no further calculation needed.
- Otherwise, `combined_score` is the **maximum** of the Jaro-Winkler score, the Levenshtein score, and the semantic (vector) score for that entity — the strongest signal wins rather than averaging, since the algorithms measure fundamentally different things (spelling distance vs. conceptual/translation similarity).
- The top-level `risk_level` reflects the highest-scoring match:
  - `RED`: exact match, or `combined_score >= 0.90`
  - `YELLOW`: `0.65 <= combined_score < 0.90`
  - `GREEN`: `combined_score < 0.65`, or no matches found

**Example request:**

```bash
curl -X POST "http://127.0.0.1:8000/screen" \
     -H "Content-Type: application/json" \
     -d '{"name": "Russian Defense Export"}'
```

**Example response:**

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
        "levenshtein_score": 0.9123,
        "matched_on": "alias",
        "matched_alias_text": "Russian Defence Export"
      },
      "combined_score": 0.9545
    }
  ],
  "screened_at": "2026-09-18T19:09:46.800908"
}
```

### Matching strategy comparison

A debug endpoint, `GET /screen/compare?name=...`, returns each strategy's raw top candidates separately (rather than combined) — useful for demonstrating exactly what exact/fuzzy matching misses that semantic search catches, e.g. a Cyrillic canonical name matched only via a Latin-script alias.

```bash
curl -G "http://127.0.0.1:8000/screen/compare" --data-urlencode "name=Electroagregat JSC"
```

## Testing

`scripts/compare_test.py` runs a set of test queries against `/screen/compare` and prints each tier's top score, useful for benchmarking changes to the matching logic or reproducing the table above against your own loaded dataset:

```bash
python scripts/compare_test.py
```

## Audit trail

Every `/screen` call is logged to an append-only SQLite table (`screening_log`) with timestamp, query, full result, and processing time — no updates or deletes, by design, so the log can later be wrapped in tamper-evident hash chaining without any retrofit.

## Scope

This is a focused three-strategy comparison, not a full production entity-resolution system. It intentionally does not include lexical (BM25) retrieval, a trained ranking model, or rule-based override logic.

## License

MIT — see [LICENSE](LICENSE).