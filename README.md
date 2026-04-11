# Document Verification System

Evidence-grounded document verification with two modes:

- **Fact Verification** — extracts atomic claims, retrieves evidence from Wikipedia/arXiv, runs NLI alignment, and returns deterministic metrics
- **Guideline Compliance** — parses rules into REQUIREMENT/PROHIBITION constraints and checks whether a document satisfies them

No similarity scoring. No black-box confidence. Every result is traceable to an evidence chunk.

---

## Requirements

- Python 3.9+
- A free Google API key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/your-username/fact_checker.git
cd fact_checker
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your API key

```bash
cp .env.example .env
```

Open `.env` and fill in your key:

```
GOOGLE_API_KEY=your_key_here
```

---

## Running the app

### Streamlit UI (recommended)

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`.

### CLI — Fact Verification

```bash
# From inline text
python main.py fact --text "Transformers do not use recurrence. They outperform RNNs on many tasks."

# From a file
python main.py fact --document my_doc.txt

# With a reference document as extra evidence
python main.py fact --document my_doc.txt --reference reference.txt

# Disable specific evidence sources
python main.py fact --document my_doc.txt --no-wikipedia
python main.py fact --document my_doc.txt --no-arxiv

# JSON output
python main.py fact --document my_doc.txt --json

# Verbose (shows progress per claim)
python main.py fact --document my_doc.txt --verbose
```

### CLI — Guideline Compliance

```bash
# From inline text
python main.py guideline \
  --text "Transformers use attention mechanisms. They were introduced in 2017." \
  --guidelines-text "Ensure the document: 1. Defines transformers 2. Does not mention RNNs 3. Includes a year"

# From files
python main.py guideline --document my_doc.txt --guidelines rules.txt

# JSON output
python main.py guideline --document my_doc.txt --guidelines rules.txt --json

# Verbose
python main.py guideline --document my_doc.txt --guidelines rules.txt --verbose
```

---

## Deploying to Streamlit Cloud

1. Push the repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select your repo and set **Main file** to `app.py`
4. Go to **Settings → Secrets** and add:

```toml
GOOGLE_API_KEY = "your_key_here"
```

5. Click **Deploy** — done.

---

## How it works

### Fact Verification pipeline

```
Document
  └─► Claim Extraction (Gemini)
        └─► For each claim:
              ├─► Evidence Retrieval (Wikipedia + arXiv)
              ├─► Chunking (deterministic, sentence-level)
              ├─► NLI Alignment per chunk (Gemini)
              └─► Aggregation (CONTRADICTED > SUPPORTED > NOT_FOUND)
                    └─► Metrics
```

**Metrics:**

| Metric | Formula |
|---|---|
| Accuracy | `(Supported / Total) × 100` |
| Coverage | `((Supported + Contradicted) / Total) × 100` |
| Contradiction Rate | `(Contradicted / Total) × 100` |
| Risk Score | `(0.3 × Not Found + 0.7 × Contradicted) / Total` |

### Guideline Compliance pipeline

```
Document + Guidelines
  ├─► Document Chunking (deterministic)
  └─► Constraint Parsing (Gemini) → REQUIREMENT / PROHIBITION
        └─► For each constraint:
              ├─► Alignment against every chunk (Gemini)
              └─► Aggregation
                    └─► Metrics
```

**Aggregation rules:**
- `REQUIREMENT` → SATISFIED if any chunk satisfies it, otherwise MISSING
- `PROHIBITION` → VIOLATED if any chunk contains the prohibited content, otherwise SATISFIED

**Metrics:**

| Metric | Formula |
|---|---|
| Compliance | `(Satisfied / Total) × 100` |
| Violation Rate | `(Violated / Total) × 100` |
| Missing Rate | `(Missing / Total) × 100` |

---

## Project structure

```
fact_checker/
├── app.py                  # Streamlit UI
├── main.py                 # CLI entry point
├── requirements.txt
├── .env                    # GOOGLE_API_KEY (not committed)
├── .env.example
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
└── fact_checker/           # Python package
    ├── components/
    │   ├── aggregator.py   # Deterministic aggregation logic
    │   ├── aligner.py      # NLI alignment (Gemini)
    │   ├── chunker.py      # Sentence-level text chunker
    │   ├── claim_extractor.py
    │   ├── evidence_retriever.py
    │   ├── guideline_parser.py
    │   └── metrics.py
    ├── pipelines/
    │   ├── fact_verification.py
    │   └── guideline_compliance.py
    ├── sources/
    │   ├── arxiv.py
    │   ├── web_search.py   # mcp-use (Python 3.11+) or requests fallback
    │   └── wikipedia.py
    └── utils/
        ├── json_parser.py  # Robust JSON extraction from LLM responses
        └── llm_client.py   # Gemini wrapper (gemini-2.0-flash)
```

---

## Notes

- **LLM is used for language only** — claim extraction, guideline parsing, and NLI alignment. It never decides truth from its own knowledge; it only compares a claim against provided evidence.
- **mcp-use web search** — `sources/web_search.py` is ready for mcp-use (`mcp-server-fetch`) but requires Python 3.11+. On Python 3.9 it falls back to plain `requests` automatically.
- **Free tier** — `gemini-2.0-flash` is free within Google AI Studio's quota limits (15 requests/minute). Large documents with many claims will take longer. The app auto-retries on rate-limit errors.
- **Tip:** For large documents (30+ claims), keep both evidence source toggles on but expect 2-5 minutes of processing time.
