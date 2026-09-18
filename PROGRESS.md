# SanctionScope: Project Progress & Architecture Report

## Project Overview
SanctionScope is a standalone, AI-powered FastAPI service designed to screen company names against the global OpenSanctions dataset. It utilizes a three-tier matching architecture—exact string comparison, fuzzy matching, and semantic vector search—to accurately identify sanctioned entities, handle aliases/typos, and maintain a strict regulatory audit trail.

---

## Directory Structure & File Architecture
Based on the current project tree, here is the function of every component in the system:

### 1. The Core Application (`app/`)
This directory contains the main FastAPI service and business logic.
* **`main.py`**: The entry point for the FastAPI server. It defines the `/screen` endpoints and orchestrates the flow of data between the request, the matching engines, and the audit logger.
* **`normalization.py`**: A utility module that cleans incoming text (removing punctuation, standardizing casing, stripping whitespace) to ensure accurate comparisons.
* **`schemas.py`**: Contains Pydantic models that strictly define the structure of incoming API requests and outgoing JSON responses.
* **`audit.py`**: Handles the compliance logging, writing every screening attempt, its input, and its final risk decision to the SQLite database.

### 2. The Matching Engine (`app/matching/`)
This directory houses the three independent screening algorithms.
* **`exact.py`**: The baseline strategy. It checks for a direct, 1-to-1 string match between the query and the database.
* **`fuzzy.py`**: Implements RapidFuzz (Jaro-Winkler/Levenshtein) to catch typographical errors, misspellings, and minor naming variations.
* **`semantic.py`**: The AI differentiator. It connects to the Qdrant vector database to catch complex structural changes, transliterations, and conceptual translations (e.g., matching "Defense" to "Defence").

### 3. Data Storage (`data/`)
This directory acts as the local storage for flat files and relational databases.
* **`raw_targets.csv`**: The initial bulk dataset downloaded directly from OpenSanctions.
* **`processed_entities.json`**: The cleaned, filtered version of the raw data, containing only relevant company entities and their aliases.
* **`audit.db`**: The SQLite database where `audit.py` permanently logs screening records.

### 4. Vector Database (`qdrant_data/`)
* This directory is a Docker volume mount. It persistently stores the AI vector embeddings locally so that the Qdrant container doesn't lose its data when restarted.

### 5. Setup Scripts (`scripts/`)
These utilities are run prior to starting the API to format and load the intelligence data.
* **`ingest.py`**: Parses `raw_targets.csv`, filters out non-company entities, extracts aliases, and outputs `processed_entities.json`.
* **`embed_and_load.py`**: Uses a HuggingFace `SentenceTransformer` to generate 384-dimensional mathematical vectors for all 24,000+ entities and uploads them into the Qdrant database in batches.

### 6. Environment & Configuration
* **`docker-compose.yml`**: Defines the infrastructure, specifically used to spin up the local Qdrant vector database container.
* **`requirements.txt`**: A strictly pinned list of Python dependencies (NumPy, PyTorch, FastAPI, RapidFuzz) optimized for local CPU execution.
* **`venv/`**: The isolated Python virtual environment.

---

## How We Built It (Progress & Milestones)

**Phase 1: Environment & Dependency Resolution**
* Initialized the Python virtual environment and resolved complex version conflicts between PyTorch, Transformers, and SciPy on the local architecture by strictly pinning legacy stable releases.
* Spun up the Qdrant vector database via Docker Compose.

**Phase 2: Data Engineering**
* Downloaded the OpenSanctions CSV.
* Developed `ingest.py` to filter the data down to 24,880 highly relevant company targets, stripping out unnecessary noise.

**Phase 3: AI Embedding Pipeline**
* Engineered `embed_and_load.py` to pass the processed JSON entities through the `all-MiniLM-L6-v2` transformer model. 
* Handled connection timeouts by implementing a batching architecture, successfully uploading all 24,880 high-dimensional vectors into Qdrant.

**Phase 4: API & Matching Construction**
* Built the FastAPI framework with strict Pydantic schemas.
* Implemented Exact and Fuzzy matching for rapid string analysis.
* Connected the Semantic matching layer to Qdrant to enable transliteration and translation detection.
* Built the regulatory audit logger using SQLite.

**Phase 5: Final Validation**
* Simulated API traffic using cURL.
* Verified exact matching functionality.
* Verified typo tolerance (successfully matching "Rosobornexport").
* Verified semantic translation tolerance (successfully matching "Russian Defense Export" to "Rosoboronexport").

## Current Status
**COMPLETED.** The application is fully operational. It accepts queries, screens them across three distinct layers, calculates an accurate risk score (RED/YELLOW/GREEN), and maintains a persistent audit trail.# SanctionScope: Project Progress & Architecture Report

## Project Overview
SanctionScope is a standalone, AI-powered FastAPI service designed to screen company names against the global OpenSanctions dataset. It utilizes a three-tier matching architecture—exact string comparison, fuzzy matching, and semantic vector search—to accurately identify sanctioned entities, handle aliases/typos, and maintain a strict regulatory audit trail.

---

## Directory Structure & File Architecture
Based on the current project tree, here is the function of every component in the system:

### 1. The Core Application (`app/`)
This directory contains the main FastAPI service and business logic.
* **`main.py`**: The entry point for the FastAPI server. It defines the `/screen` endpoints and orchestrates the flow of data between the request, the matching engines, and the audit logger.
* **`normalization.py`**: A utility module that cleans incoming text (removing punctuation, standardizing casing, stripping whitespace) to ensure accurate comparisons.
* **`schemas.py`**: Contains Pydantic models that strictly define the structure of incoming API requests and outgoing JSON responses.
* **`audit.py`**: Handles the compliance logging, writing every screening attempt, its input, and its final risk decision to the SQLite database.

### 2. The Matching Engine (`app/matching/`)
This directory houses the three independent screening algorithms.
* **`exact.py`**: The baseline strategy. It checks for a direct, 1-to-1 string match between the query and the database.
* **`fuzzy.py`**: Implements RapidFuzz (Jaro-Winkler/Levenshtein) to catch typographical errors, misspellings, and minor naming variations.
* **`semantic.py`**: The AI differentiator. It connects to the Qdrant vector database to catch complex structural changes, transliterations, and conceptual translations (e.g., matching "Defense" to "Defence").

### 3. Data Storage (`data/`)
This directory acts as the local storage for flat files and relational databases.
* **`raw_targets.csv`**: The initial bulk dataset downloaded directly from OpenSanctions.
* **`processed_entities.json`**: The cleaned, filtered version of the raw data, containing only relevant company entities and their aliases.
* **`audit.db`**: The SQLite database where `audit.py` permanently logs screening records.

### 4. Vector Database (`qdrant_data/`)
* This directory is a Docker volume mount. It persistently stores the AI vector embeddings locally so that the Qdrant container doesn't lose its data when restarted.

### 5. Setup Scripts (`scripts/`)
These utilities are run prior to starting the API to format and load the intelligence data.
* **`ingest.py`**: Parses `raw_targets.csv`, filters out non-company entities, extracts aliases, and outputs `processed_entities.json`.
* **`embed_and_load.py`**: Uses a HuggingFace `SentenceTransformer` to generate 384-dimensional mathematical vectors for all 24,000+ entities and uploads them into the Qdrant database in batches.

### 6. Environment & Configuration
* **`docker-compose.yml`**: Defines the infrastructure, specifically used to spin up the local Qdrant vector database container.
* **`requirements.txt`**: A strictly pinned list of Python dependencies (NumPy, PyTorch, FastAPI, RapidFuzz) optimized for local CPU execution.
* **`venv/`**: The isolated Python virtual environment.

---

## How We Built It (Progress & Milestones)

**Phase 1: Environment & Dependency Resolution**
* Initialized the Python virtual environment and resolved complex version conflicts between PyTorch, Transformers, and SciPy on the local architecture by strictly pinning legacy stable releases.
* Spun up the Qdrant vector database via Docker Compose.

**Phase 2: Data Engineering**
* Downloaded the OpenSanctions CSV.
* Developed `ingest.py` to filter the data down to 24,880 highly relevant company targets, stripping out unnecessary noise.

**Phase 3: AI Embedding Pipeline**
* Engineered `embed_and_load.py` to pass the processed JSON entities through the `all-MiniLM-L6-v2` transformer model. 
* Handled connection timeouts by implementing a batching architecture, successfully uploading all 24,880 high-dimensional vectors into Qdrant.

**Phase 4: API & Matching Construction**
* Built the FastAPI framework with strict Pydantic schemas.
* Implemented Exact and Fuzzy matching for rapid string analysis.
* Connected the Semantic matching layer to Qdrant to enable transliteration and translation detection.
* Built the regulatory audit logger using SQLite.

**Phase 5: Final Validation**
* Simulated API traffic using cURL.
* Verified exact matching functionality.
* Verified typo tolerance (successfully matching "Rosobornexport").
* Verified semantic translation tolerance (successfully matching "Russian Defense Export" to "Rosoboronexport").

## Current Status
**COMPLETED.** The application is fully operational. It accepts queries, screens them across three distinct layers, calculates an accurate risk score (RED/YELLOW/GREEN), and maintains a persistent audit trail.