import httpx
import asyncio
import random
import os
import re

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from urllib.parse import urlparse, urljoin

app = FastAPI()

# Serve static files (for background image if you have one)
app.mount("/static", StaticFiles(directory="static"), name="static")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)",
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def is_allowed(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc)
    except:
        return False


async def fetch(client, url, method="GET", **kwargs):
    return await client.request(method, url, timeout=15.0, follow_redirects=True, **kwargs)


# ---------------- HOME PAGE ----------------
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
      <head>
        <title>Web Proxy</title>
        <style>
          body {
            font-family: Arial;
            background: #111;
            color: white;
            text-align: center;
            padding: 60px;
          }
          input {
            width: 60%;
            padding: 12px;
            border-radius: 8px;
            border: none;
          }
          button {
            padding: 12px 18px;
            margin-left: 10px;
            cursor: pointer;
          }
        </style>
      </head>
      <body>

        <h1>Web Proxy</h1>

        <form onsubmit="go(event)">
          <input id="url" placeholder="Enter URL (google.com)">
          <button type="submit">Go</button>
        </form>

        <p>This proxy loads pages. Some interactions may not work.</p>

        <script>
          function go(e) {
            e.preventDefault();
            let url = document.getElementById("url").value;

            if (!url.startsWith("http")) {
              url = "https://" + url;
            }

            // Open in new tab (prevents broken navigation issues)
            window.open("/proxy?url=" + encodeURIComponent(url), "_blank");
          }
        </script>

      </body>
    </html>
    """


# ---------------- PROXY ----------------
@app.get("/proxy")
async def proxy(url: str):
    if not is_allowed(url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "*/*",
    }

    async with httpx.AsyncClient() as client:
        resp = await fetch(client, url, headers=headers)

        content = resp.content
        content_type = resp.headers.get("content-type", "")

        # LIGHT HTML rewriting (basic fix)
        if "text/html" in content_type:
            text = content.decode(errors="ignore")

            def repl(match):
                link = match.group(1)
                full = urljoin(url, link)
                return f'="/proxy?url={full}"'

            text = re.sub(r'="([^"]+)"', repl, text)

            # Make forms open in new tab (avoid breaking UX)
            text = text.replace("<form", '<form target="_blank"')

            content = text.encode()

        excluded = {"content-encoding", "transfer-encoding", "content-length"}
        headers_out = {k: v for k, v in resp.headers.items() if k.lower() not in excluded}

        return StreamingResponse(
            iter([content]),
            status_code=resp.status_code,
            headers=headers_out,
            media_type=content_type
        )


# ---------------- START ----------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)