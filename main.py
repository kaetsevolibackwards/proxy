import httpx
import asyncio
import random
import os

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from urllib.parse import urlparse

app = FastAPI()

# ---------------- STATIC FILES ----------------
# Put your image here: /static/bg.jpg
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------- USER AGENTS ----------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15",
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def is_allowed(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc)
    except:
        return False


async def fetch_with_retries(client, url, method="GET", **kwargs):
    for attempt in range(3):
        try:
            return await client.request(
                method,
                url,
                timeout=15.0,
                follow_redirects=True,
                **kwargs
            )
        except httpx.TimeoutException:
            if attempt == 2:
                raise
            await asyncio.sleep(2 ** attempt)


# ---------------- HOME PAGE ----------------
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
      <head>
        <title>Web Proxy</title>
        <style>
          body {
            font-family: Arial;
            background-image: url("/static/bg.jpg");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            color: white;
            text-align: center;
            padding: 60px;
          }

          .box {
            background: rgba(0,0,0,0.6);
            padding: 30px;
            border-radius: 12px;
            display: inline-block;
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

        <div class="box">
          <h1>Web Proxy</h1>

          <form onsubmit="go(event)">
            <input id="url" placeholder="Enter URL (google.com or https://example.com)">
            <button type="submit">Go</button>
          </form>

          <p>Example: google.com</p>
        </div>

        <script>
          function go(e) {
            e.preventDefault();
            let url = document.getElementById("url").value;

            if (!url.startsWith("http")) {
              url = "https://" + url;
            }

            window.location.href = "/proxy?url=" + encodeURIComponent(url);
          }
        </script>

      </body>
    </html>
    """


# ---------------- PROXY GET ----------------
@app.get("/proxy")
async def proxy_get(request: Request, url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL required")

    if not is_allowed(url):
        raise HTTPException(status_code=403, detail="Blocked URL")

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "*/*",
    }

    async with httpx.AsyncClient() as client:
        resp = await fetch_with_retries(client, url, "GET", headers=headers)

        excluded = {"content-encoding", "transfer-encoding", "content-length"}
        headers_out = {k: v for k, v in resp.headers.items() if k.lower() not in excluded}

        return StreamingResponse(
            iter([resp.content]),
            status_code=resp.status_code,
            headers=headers_out,
            media_type=resp.headers.get("content-type")
        )


# ---------------- PROXY POST ----------------
@app.post("/proxy")
async def proxy_post(request: Request, url: str):
    body = await request.body()

    headers = {
        "User-Agent": get_random_user_agent(),
    }

    if "content-type" in request.headers:
        headers["Content-Type"] = request.headers["content-type"]

    async with httpx.AsyncClient() as client:
        resp = await fetch_with_retries(client, url, "POST", content=body, headers=headers)

        excluded = {"content-encoding", "transfer-encoding", "content-length"}
        headers_out = {k: v for k, v in resp.headers.items() if k.lower() not in excluded}

        return StreamingResponse(
            iter([resp.content]),
            status_code=resp.status_code,
            headers=headers_out,
            media_type=resp.headers.get("content-type")
        )


# ---------------- RENDER STARTUP ----------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)