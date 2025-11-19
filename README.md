# Membit CLI Insight Tool

Small Python utility that wires together the official [membit-python SDK](https://docs.membit.ai/api-usage/python) with an interactive prompt. Enter a question or topic and the script returns:

- Live **discussion clusters** from Membit’s `/clusters/search` endpoint
- A handful of related **raw posts/tweets** (with direct links when available)
- An optional **Gemini summary** that synthesizes the current sentiment (only shown if a Google Generative AI key is configured)

The project is intentionally lightweight so you can copy/paste the core logic into a notebook, serverless function, or agent.

## Requirements

- Python 3.12+
- A Membit API key (`MEMBIT_API_KEY`). Create one from the [Membit dashboard](https://docs.membit.ai/#getting-started).
- (Optional) A Google Generative AI key (`GOOGLE_API_KEY`) if you want automatic summaries.

Everything else (dotenv, membit SDK, etc.) is pinned in `requirements.txt`.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Populate `.env` with at least:

```
MEMBIT_API_KEY=<your membit key>
# Optional extras
GOOGLE_API_KEY=<google-genai key>
GOOGLE_GEMINI_MODEL=models/gemini-2.0-flash   # default already set
```

## Usage

```bash
source venv/bin/activate
python membit_cli.py
```

Example session:

```
Ask me anything and I will fetch fresh Membit clusters (type 'exit' to quit).

Question> bitcoin halving

=== Related clusters ===
1. Bitcoin Halving Discussion [Crypto Trading]
   ↳ Traders debate the impact of the upcoming halving…
   (engagement=4021.23, relevance=0.972)

=== Related posts (with links) ===
1. [twitter] Analysts expect volatility…
   ↳ https://twitter.com/<handle>/status/123

=== Gemini summary ===
Sentiment is cautiously bullish…
```

If you only want raw JSON, call the membit SDK directly (see `membit_cli.py` for a reference implementation).

## Project Structure

| File               | Purpose                                                                                  |
| ------------------ | ---------------------------------------------------------------------------------------- |
| `membit_cli.py`    | Interactive CLI wiring together Membit clusters/posts and optional Gemini summarization. |
| `requirements.txt` | Exact dependency versions.                                                               |
| `.env`             | Local secrets (not committed).                                                           |

## Extending

- Swap the CLI loop for a web or chat interface by reusing `fetch_clusters` and `fetch_posts`.
- Adjust `GOOGLE_GEMINI_MODEL` to any supported Gemini model once your account has access.
- Use the async `AsyncMembitClient` from the SDK if you need higher throughput.

## Troubleshooting

- **ImportError for `membit`** – run `pip install membit-python` inside your virtualenv.
- **HTTP errors** – double-check `MEMBIT_API_KEY`, or try again later if the Membit API is throttling.
- **Gemini 404/model errors** – confirm the model name matches your account (run `gcloud alpha genai models list` or check the Google console).

Feel free to adapt the script to your own agent/workflow and submit improvements!
