import httpx
import json
import urllib.parse
from typing import Dict, Any, List
from html.parser import HTMLParser

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = False
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "header", "footer", "nav", "aside"):
            self.skip = True
    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "header", "footer", "nav", "aside"):
            self.skip = False
    def handle_data(self, data):
        if not self.skip:
            self.text.append(data)

async def fetch_and_extract(url: str) -> Dict[str, Any]:
    try:
        headers = {"User-Agent": "zyvo-clone/1.0 research"}
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "text/html" in content_type:
            parser = TextExtractor()
            parser.feed(resp.text)
            text = " ".join(parser.text)
            text = " ".join(text.split())[:8000]
            return {"url": url, "content": text, "title": extract_title(resp.text)}
        elif "application/json" in content_type:
            return {"url": url, "content": json.dumps(resp.json(), indent=2)[:8000]}
        else:
            return {"url": url, "content": resp.text[:8000]}
    except Exception as e:
        return {"url": url, "error": str(e)}

def extract_title(html: str) -> str:
    import re
    match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    return match.group(1).strip() if match else ""

async def summarize_with_llm(topic: str, sources: List[Dict]) -> str:
    from core.config import load_config, get_litellm_config
    import litellm
    config = load_config()
    params = get_litellm_config(config)
    
    source_text = "\n\n".join([f"SOURCE: {s.get('title', s['url'])}\n{s.get('content', s.get('error', ''))[:3000]}" for s in sources])
    prompt = f"""Research topic: {topic}

Sources:
{source_text}

Provide a structured summary with:
- Key findings (bullet points)
- Important details/data
- Contradictions or gaps
- Sources cited inline with [n]"""

    try:
        resp = await litellm.acompletion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            **params
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Summary failed: {e}"

async def research_topic(topic: str, urls: List[str] = None) -> Dict[str, Any]:
    if not urls:
        urls = [
            f"https://duckduckgo.com/html/?q={urllib.parse.quote(topic)}",
        ]
    
    results = []
    for url in urls[:5]:
        results.append(await fetch_and_extract(url))
    
    summary = await summarize_with_llm(topic, results)
    
    return {
        "summary": summary,
        "sources": [{"url": r["url"], "title": r.get("title", ""), "error": r.get("error")} for r in results]
    }


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "research_topic",
            "description": "Research a topic by fetching URLs and summarizing",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic to research"},
                    "urls": {"type": "array", "items": {"type": "string"}, "description": "Optional URLs to fetch"}
                },
                "required": ["topic"]
            }
        }
    }
]