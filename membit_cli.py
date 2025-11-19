"""
CLI utility that surfaces live Membit clusters for a user question,
following https://docs.membit.ai/api-usage/python .
"""

import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

try:
    # Membit SDK
    from membit import MembitClient
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        "Missing membit SDK. Install with: pip install membit-python"
    ) from e

# Optional Gemini summarization
try:
    import google.generativeai as genai  # type: ignore
except ModuleNotFoundError:
    genai = None

# Load environment variables
load_dotenv()

MEMBIT_API_KEY = os.getenv("MEMBIT_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not MEMBIT_API_KEY:
    raise ValueError("Missing API key. Please set MEMBIT_API_KEY in your environment.")

# Configure optional Gemini
GEMINI_MODEL = None
if GOOGLE_API_KEY and genai is not None:
    genai.configure(api_key=GOOGLE_API_KEY)
    model_name = os.getenv("GOOGLE_GEMINI_MODEL", "models/gemini-2.0-flash")
    GEMINI_MODEL = genai.GenerativeModel(model_name)


def fetch_clusters(client: MembitClient, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Calls the official Membit SDK and returns the `clusters` list.
    - The SDK expects the query string as the first positional argument.
    - `limit` is clamped to [1, 50] per docs.
    - `output_format="json"` returns structured data.
    """
    limit = min(max(limit, 1), 50)
    # Per docs: clusters = client.cluster_search("your query", limit=3)
    # We also request JSON output explicitly.
    response = client.cluster_search(query, limit=limit, output_format="json")
    if isinstance(response, dict):
        return response.get("clusters") or []
    return []


def fetch_posts(client: MembitClient, query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetches raw posts for the query so we can surface direct tweet links.
    """
    limit = min(max(limit, 1), 25)
    response = client.post_search(query, limit=limit, output_format="json")
    if isinstance(response, dict):
        return response.get("posts") or []
    return []


def analyze_with_gemini(query: str, clusters: List[Dict[str, Any]]) -> Optional[str]:
    """
    Sends the retrieved clusters to Gemini for a quick synthesis.
    Returns None when Gemini is not configured.
    """
    if GEMINI_MODEL is None:
        return None

    lines = []
    for cluster in clusters:
        label = cluster.get("label")
        summary = cluster.get("summary")
        if summary:
            lines.append(f"- {summary}")
        elif label:
            lines.append(f"- {label}")

    context_text = "\n".join(lines) if lines else "(no cluster summaries available)"
    prompt = f"""
You are a social analyst AI. Using the real-time discussion data from Membit below,
summarize and interpret public sentiment and key insights around: "{query}".
---
{context_text}
---
"""
    try:
        response = GEMINI_MODEL.generate_content(prompt)
        return (response.text or "").strip()
    except Exception as e:
        return f"(Gemini summarization failed: {e})"


def format_clusters(clusters: List[Dict[str, Any]]) -> str:
    if not clusters:
        return "No related clusters found."

    lines: List[str] = []
    for idx, cluster in enumerate(clusters, 1):
        label = cluster.get("label") or "Untitled cluster"
        summary = cluster.get("summary") or "No summary provided."
        category = cluster.get("category") or "Uncategorized"
        engagement = cluster.get("engagement_score")
        search_score = cluster.get("search_score")

        lines.append(f"{idx}. {label} [{category}]")
        lines.append(f"   ↳ {summary}")
        stats: List[str] = []
        if isinstance(engagement, (int, float)):
            stats.append(f"engagement={engagement:.2f}")
        if isinstance(search_score, (int, float)):
            stats.append(f"relevance={search_score:.3f}")
        if stats:
            lines.append(f"   ({', '.join(stats)})")
    return "\n".join(lines)


def _extract_post_url(post: Dict[str, Any]) -> Optional[str]:
    for key in ("url", "link", "post_url", "permalink"):
        value = post.get(key)
        if value:
            return value
    return None


def format_posts(posts: List[Dict[str, Any]]) -> str:
    if not posts:
        return "No related posts (tweets) were found."

    lines: List[str] = []
    for idx, post in enumerate(posts, 1):
        platform = post.get("platform") or post.get("source") or "unknown"
        text = (post.get("text") or post.get("content") or "").strip()
        url = _extract_post_url(post) or "Link unavailable."

        snippet = text[:200] + ("…" if len(text) > 200 else "")
        lines.append(f"{idx}. [{platform}] {snippet}")
        lines.append(f"   ↳ {url}")

    return "\n".join(lines)


def run_cli():
    # Per docs, the client reads MEMBIT_API_KEY automatically if not provided,
    # but we pass it explicitly since we already validated it.
    client = MembitClient(api_key=MEMBIT_API_KEY)

    print("Ask me anything and I will fetch fresh Membit clusters (type 'exit' to quit).")

    while True:
        try:
            query = input("\nQuestion> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not query:
            continue
        if query.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        try:
            clusters = fetch_clusters(client, query, limit=10)
        except Exception as exc:
            print(f"Something went wrong: {exc}")
            continue

        print("\n=== Related clusters ===")
        print(format_clusters(clusters))

        try:
            posts = fetch_posts(client, query, limit=5)
        except Exception as exc:
            print(f"\n(Unable to fetch individual posts: {exc})")
            posts = []

        if posts:
            print("\n=== Related posts (with links) ===")
            print(format_posts(posts))

        gemini_summary = analyze_with_gemini(query, clusters)
        if gemini_summary:
            print("\n=== Gemini summary ===")
            print(gemini_summary)


if __name__ == "__main__":
    run_cli()
