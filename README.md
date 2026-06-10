# Verdikt

Evidence-grounded document verification with two modes:

- **Fact Verification** — extracts atomic claims, retrieves evidence from Wikipedia/arXiv, runs NLI alignment, and returns deterministic metrics
- **Guideline Compliance** — parses rules into REQUIREMENT/PROHIBITION constraints and checks whether a document satisfies them

No similarity scoring. No black-box confidence. Every result is traceable to an evidence chunk.

---

## Requirements

- Python 3.9+
- An API key for at least one supported LLM provider (all have free tiers)

---

## Supported LLM Providers

| Provider | Env var | Free tier | Default model |
|---|---|---|---|
| **Groq** | `GROQ_API_KEY` | [console.groq.com](https://console.groq.com/) | `llama-3.3-70b-versatile` |
| **NVIDIA NIM** | `NVIDIA_API_KEY` | [build.nvidia.com](https://build.nvidia.com/) | `meta/llama-3.3-70b-instruct` |
| **OpenRouter** | `OPENROUTER_API_KEY` | [openrouter.ai/keys](https://openrouter.ai/keys) | `meta-llama/llama-3.3-70b-instruct:free` |
| **Google Gemini** | `GOOGLE_API_KEY` | [aistudio.google.com](https://aistudio.google.com/apikey) | `gemini-2.5-flash` |

You can configure multiple providers. The client uses the first one available and automatically falls back to others on rate-limit errors or failures.

**Priority order (when `LLM_PROVIDER` is not set):** Groq → NVIDIA NIM → OpenRouter → Google Gemini

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/your-username/verdikt.git
cd verdikt
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

### 4. Configure your API key(s)

```bash
cp .env.example .env
```

Open `.env` and fill in at least one provider key:

```dotenv
# Groq (recommended — fastest free tier)
GROQ_API_KEY=your_groq_key_here

# NVIDIA NIM
NVIDIA_API_KEY=your_nvidia_key_here

# OpenRouter
OPENROUTER_API_KEY=your_openrouter_key_here

# Google Gemini
GOOGLE_API_KEY=your_google_key_here
```

**Optional overrides:**

```dotenv
# Force a specific provider (groq | nvidia | openrouter | google)
LLM_PROVIDER=groq

# Use a different model than the provider default
LLM_MODEL=llama-3.3-70b-versatile
```

---

## Running the app

### Streamlit UI (recommended)

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. The sidebar shows only the providers for which a key is configured, and lets you switch between them and optionally override the model at runtime.

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
4. Go to **Settings → Secrets** and add one or more provider keys:

```toml
GROQ_API_KEY = "your_groq_key_here"
# NVIDIA_API_KEY = "..."
# OPENROUTER_API_KEY = "..."
# GOOGLE_API_KEY = "..."
```

5. Click **Deploy** — done.

---

## How it works

### Fact Verification pipeline

```
Document
  └─► Claim Extraction (LLM)
        └─► For each claim:
              ├─► Evidence Retrieval (Wikipedia + arXiv)
              ├─► Chunking (deterministic, sentence-level)
              ├─► NLI Alignment per chunk (LLM)
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
  └─► Constraint Parsing (LLM) → REQUIREMENT / PROHIBITION
        └─► For each constraint:
              ├─► Alignment against every chunk (LLM)
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
verdikt/
├── app.py                  # Streamlit UI
├── main.py                 # CLI entry point
├── requirements.txt
├── .env                    # API keys (not committed)
├── .env.example
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
└── verdikt/                # Python package
    ├── components/
    │   ├── aggregator.py   # Deterministic aggregation logic
    │   ├── aligner.py      # NLI alignment (LLM)
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
        └── llm_client.py   # Multi-provider LLM client with fallback
```

---

## Testing

The test suite covers every module that contains logic — pure functions are tested directly; LLM-dependent components are tested by mocking the `complete()` call so no API key or network access is needed.

### Run the tests

```bash
python -m pytest tests/ -v
```

### What is tested and why

| File | What it tests | Why it matters |
|---|---|---|
| `test_json_parser.py` | JSON extraction from LLM output (plain, fenced, with preamble); label normalisation | LLM responses are noisy — the parser must survive every format variant |
| `test_chunker.py` | Sentence splitting, merging within token budget, index assignment | Wrong chunk boundaries silently corrupt all downstream NLI results |
| `test_aggregator.py` | NLI precedence rules (`CONTRADICTED > SUPPORTED > NOT_FOUND`); REQUIREMENT vs PROHIBITION aggregation | These rules are the core of what makes results deterministic and traceable |
| `test_metrics.py` | Accuracy, risk, coverage, contradiction-rate, compliance formulas | Verifies the exact arithmetic so metric regressions are caught immediately |
| `test_llm_client.py` | Provider auto-detection from env vars; priority order; explicit `LLM_PROVIDER` override; fallback when one provider fails; errors when no key is set | Multi-provider routing is the main new behaviour — all paths need coverage |
| `test_claim_extractor.py` | Claim parsing, filtering non-strings and blank items, parse-error recovery | The first LLM call in the pipeline; bad output here kills everything downstream |
| `test_aligner.py` | NLI label parsing, alias normalisation, plain-text fallback for malformed JSON | Aligner is called hundreds of times per document — every edge case matters |
| `test_guideline_parser.py` | Constraint parsing, type validation, id assignment, filtering bad items | Invalid constraints silently drop compliance checks if not caught |

### Design principles

- **No API keys required** — every test that touches an LLM component mocks `llm_client.complete()` or `_call_provider()`. The suite runs entirely offline.
- **Isolated env** — `conftest.py` clears all provider env vars (`GROQ_API_KEY`, etc.) before every test via an `autouse` fixture, so a real `.env` file in the project never influences results.
- **No network** — evidence sources (Wikipedia, arXiv) are not tested here; they are external I/O with no logic worth unit-testing.

---

## Notes

- **LLM is used for language only** — claim extraction, guideline parsing, and NLI alignment. It never decides truth from its own knowledge; it only compares a claim against provided evidence.
- **Automatic fallback** — if the active provider hits a rate limit or returns an error, the client transparently retries with the next configured provider.
- **mcp-use web search** — `sources/web_search.py` supports mcp-use (`mcp-server-fetch`) on Python 3.11+; falls back to plain `requests` automatically on older versions.
- **Large documents** — for 30+ claims, keep both evidence source toggles on and expect 2-5 minutes of processing time. Groq's free tier is the fastest option for throughput.
