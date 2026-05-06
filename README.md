# Anonymous Web Proxy

A fast, anonymous web proxy built with Python and FastAPI. Fetches content from other websites while hiding your identity.

## Features

- **Anonymous browsing**: Rotates user agents and strips identifying headers
- **Fast async handling**: Built on FastAPI for high performance
- **GET/POST support**: Handles both request types
- **Streaming responses**: Efficient memory usage for large responses
- **Error handling**: Graceful error handling and retries
- **Configurable blocking**: Easy to add domain blacklist
- **Header filtering**: Removes tracking headers
- **Docker support**: Easy containerized deployment

## Installation

### Local Setup

```bash
git clone https://github.com/kaetsevolibackwards/proxy.git
cd proxy
pip install -r requirements.txt
```

### Docker Setup

```bash
docker-compose up -d
```

## Usage

### Local Running

Start the server:
```bash
python main.py
```

The proxy will run on `http://localhost:8000`

### GET Request

```bash
curl "http://localhost:8000/proxy?url=https://example.com"
```

### POST Request

```bash
curl -X POST "http://localhost:8000/proxy?url=https://example.com" \
  -d "data=value"
```

### Web Browser

Access via browser:
```
http://localhost:8000/proxy?url=https://example.com
```

### API Endpoints

- **GET** `/proxy?url=<URL>` - Fetch a webpage via GET
- **POST** `/proxy?url=<URL>` - Submit form data via POST
- **GET** `/` - Health check and API documentation

## Configuration

Edit `main.py` to customize:

```python
# Add blocked domains
BLOCKED_DOMAINS = ["facebook.com", "instagram.com"]

# Modify user agents
USER_AGENTS = [
    "Your custom user agent 1",
    "Your custom user agent 2",
]

# Adjust timeout
timeout=10.0  # Change timeout value
```

## Privacy Features

- ✅ User agent rotation (4 different agents)
- ✅ DNT (Do Not Track) header
- ✅ Removes tracking headers
- ✅ No cookies stored
- ✅ Connection privacy headers
- ✅ Header filtering

## Docker Commands

### Build Image
```bash
docker build -t proxy .
```

### Run Container
```bash
docker run -p 8000:8000 proxy
```

### Using Docker Compose
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f
```

## Advanced Usage

### Custom Domain Blocking

Edit `main.py` and add domains to block:

```python
BLOCKED_DOMAINS = [
    "tracking-site.com",
    "ads.example.com",
    "facebook.com"
]
```

### Timeout Configuration

Modify the timeout value (default 10 seconds):

```python
timeout=20.0  # Increase to 20 seconds
```

### Max Retries

Adjust retry attempts for failed requests:

```python
max_retries = 5  # Increase from 3 to 5
```

## Limitations

- May not work with JavaScript-heavy sites
- Some websites may block proxy traffic
- Large file streaming may have limitations
- Session persistence not maintained across requests

## Response Headers

The proxy filters sensitive headers:
- Removes `content-encoding`
- Removes `transfer-encoding`
- Removes `content-length`

## Status Codes

- `200` - Successful request
- `400` - Missing URL parameter
- `403` - URL blocked by domain filter
- `500` - Failed to fetch URL

## Example Responses

### Success Response (200)
Returns the HTML/content of the requested website

### Error Response (400)
```json
{
  "detail": "URL parameter required"
}
```

### Blocked Response (403)
```json
{
  "detail": "URL not allowed"
}
```

## Performance

- Handles multiple concurrent requests
- Async I/O for fast response times
- Streaming responses for large files
- Connection pooling for efficiency

## Troubleshooting

### "Repository not found" error
Ensure your GitHub repository exists and is accessible.

### Port already in use
Change the port in `main.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8001)
```

### Timeout errors
Increase the timeout value in the `fetch_with_retries` function:
```python
timeout=20.0
```

### SSL/Certificate errors
Some websites have strict SSL policies. Try different user agents or add exception handling.

## Legal Notice

⚠️ **Important**: Use this proxy responsibly and legally. 

- Respect website Terms of Service
- Follow local laws and regulations
- Don't use for illegal activities
- Respect website rate limits
- Comply with CFAA and similar laws

## Security Considerations

- This proxy does NOT provide encryption
- Use a VPN for true privacy
- Does not hide your IP from the destination server
- Website can still log your requests
- Use responsibly and legally

## Contributing

Feel free to fork and submit pull requests!

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check existing GitHub issues
2. Create a new issue with details
3. Include error messages and steps to reproduce

## Repository

GitHub: https://github.com/kaetsevolibackwards/proxy

---

**Built with:**
- Python 3.11+
- FastAPI
- HTTPX
- Uvicorn
