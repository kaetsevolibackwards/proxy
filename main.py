import httpx
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, Response
from urllib.parse import urlparse, urljoin
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of user agents to rotate for anonymity
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15",
]

BLOCKED_DOMAINS = []  # Add domains to block if needed

def get_random_user_agent():
    """Rotate user agents for anonymity"""
    import random
    return random.choice(USER_AGENTS)

def is_allowed(url: str) -> bool:
    """Check if URL is allowed"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        if domain in BLOCKED_DOMAINS:
            return False
        return True
    except:
        return False

async def fetch_with_retries(client: httpx.AsyncClient, url: str, method: str = "GET", **kwargs):
    """Fetch URL with retries and timeout"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await client.request(
                method,
                url,
                timeout=10.0,
                follow_redirects=True,
                **kwargs
            )
            return response
        except httpx.TimeoutException:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            raise

@app.get("/proxy")
async def proxy_get(request: Request, url: str):
    """Proxy GET requests"""
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter required")
    
    if not is_allowed(url):
        raise HTTPException(status_code=403, detail="URL not allowed")
    
    try:
        headers = {
            "User-Agent": get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        async with httpx.AsyncClient() as client:
            response = await fetch_with_retries(client, url, "GET", headers=headers)
            
            # Filter sensitive headers
            excluded_headers = {"content-encoding", "transfer-encoding", "content-length"}
            response_headers = {
                k: v for k, v in response.headers.items()
                if k.lower() not in excluded_headers
            }
            
            return StreamingResponse(
                iter([response.content]),
                status_code=response.status_code,
                headers=dict(response_headers),
                media_type=response.headers.get("content-type")
            )
    
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch URL")

@app.post("/proxy")
async def proxy_post(request: Request, url: str):
    """Proxy POST requests"""
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter required")
    
    if not is_allowed(url):
        raise HTTPException(status_code=403, detail="URL not allowed")
    
    try:
        body = await request.body()
        
        headers = {
            "User-Agent": get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Connection": "keep-alive",
        }
        
        # Preserve original content type
        if "content-type" in request.headers:
            headers["Content-Type"] = request.headers["content-type"]
        
        async with httpx.AsyncClient() as client:
            response = await fetch_with_retries(
                client, url, "POST", 
                headers=headers, 
                content=body
            )
            
            excluded_headers = {"content-encoding", "transfer-encoding", "content-length"}
            response_headers = {
                k: v for k, v in response.headers.items()
                if k.lower() not in excluded_headers
            }
            
            return StreamingResponse(
                iter([response.content]),
                status_code=response.status_code,
                headers=dict(response_headers),
                media_type=response.headers.get("content-type")
            )
    
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch URL")

@app.get("/")
async def root():
    """Health check and documentation"""
    return {
        "service": "Web Proxy",
        "version": "1.0.0",
        "usage": {
            "get": "/proxy?url=https://example.com",
            "post": "/proxy?url=https://example.com (with body)"
        }
    }

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)