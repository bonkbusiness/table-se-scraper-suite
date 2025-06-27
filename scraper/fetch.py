import threading
import time
import random
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from logging_utils import get_logger
    logger = get_logger("fetch")
except ImportError:
    import logging
    logger = logging.getLogger("fetch")

DEFAULT_USER_AGENTS = [
    # Realistic and rotating user agents
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    # Add more as needed
]
DEFAULT_HEADERS = {
    "User-Agent": random.choice(DEFAULT_USER_AGENTS),
    "Accept-Language": "sv,en;q=0.9",
}
# Example proxy list - can be empty if not using proxies
PROXY_LIST = [
    # "http://user:pass@proxy1.example.com:8000",
    # "http://proxy2.example.com:8080",
    # Add more as needed
]

thread_local = threading.local()

# 2. Advanced Throttling & Rate Limiting with jitter
def throttle_delay(base_delay=0.7, jitter=0.3):
    delay = base_delay + random.uniform(0, jitter)
    logger.debug(f"Sleeping for {delay:.2f}s to throttle requests.")
    time.sleep(delay)

def get_session():
    """
    Get a thread-local requests.Session with retry logic and default headers.
    """
    if not hasattr(thread_local, "session"):
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        # User-Agent is randomized per-request (see below); so only set Accept-Language here
        session.headers.update({"Accept-Language": "sv,en;q=0.9"})
        thread_local.session = session
    return thread_local.session

# 4. User-Agent Rotation
def get_random_user_agent():
    return random.choice(DEFAULT_USER_AGENTS)

# 5. Better Error Handling / Retry Logic (with hooks for fallback or alerting)
def log_and_alert_error(url, error):
    logger.error(f"ERROR fetching {url}: {error}")
    # Hook for alerting/metrics (e.g., send to monitoring, email, etc.)
    # pass

# 6. Request/Response Hooks (stub - can add custom logic)
def pre_request_hook(url, headers, proxies):
    logger.debug(f"Requesting URL: {url} | Headers: {headers} | Proxies: {proxies}")

def post_response_hook(url, response):
    logger.info(f"Fetched {url} [status {response.status_code}]")
    # Hook for metrics, custom validation, etc.

# 7. Asynchronous Fetching with aiohttp (bonus: compatible with cache if needed)
import asyncio
import aiohttp

async def fetch_url_async(
    url: str,
    headers: dict = None,
    timeout: int = 20,
    throttle: float = 0.7,
    max_retries: int = 3,
    proxies: list = None
) -> str:
    """
    Asynchronously fetch a URL and return its text, with retries, throttling, and random User-Agent/proxy.
    """
    headers = headers or {}
    attempt = 0
    proxy = random.choice(proxies) if proxies else None
    while attempt < max_retries:
        ua = headers.get("User-Agent") or get_random_user_agent()
        all_headers = {**DEFAULT_HEADERS, **headers, "User-Agent": ua}
        pre_request_hook(url, all_headers, proxy)
        try:
            async with aiohttp.ClientSession(headers=all_headers) as session:
                async with session.get(url, timeout=timeout, proxy=proxy) as resp:
                    text = await resp.text()
                    post_response_hook(url, resp)
                    await asyncio.sleep(throttle + random.uniform(0, 0.3))
                    return text
        except Exception as e:
            logger.warning(f"Async fetch failed ({url}), attempt {attempt+1}/{max_retries}: {e}")
            await asyncio.sleep(1.5 * (attempt + 1))
            attempt += 1
    log_and_alert_error(url, f"Giving up after {max_retries} attempts.")
    raise Exception(f"Giving up on {url} after {max_retries} attempts")

# 8. Caching Layer with requests-cache (optional, opt-in)
try:
    import requests_cache
    CACHE_ENABLED = True
except ImportError:
    CACHE_ENABLED = False

def enable_requests_cache(backend="sqlite", expire_after=3600, cache_name="http_cache"):
    if CACHE_ENABLED:
        requests_cache.install_cache(cache_name=cache_name, backend=backend, expire_after=expire_after)
        logger.info(f"Enabled requests-cache: backend={backend}, expire_after={expire_after}s, cache_name={cache_name}")
    else:
        logger.warning("requests-cache not installed. Caching disabled.")

# 9. Headless Browser Support (fallback for JS-heavy pages)
def fetch_with_playwright(url, timeout=30, headless=True):
    """
    Fetch page content using Playwright (for JavaScript-heavy sites).
    Requires playwright and playwright browsers installed!
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("playwright not installed. Cannot fetch with browser.")
        raise

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(url, timeout=timeout * 1000)
        html = page.content()
        browser.close()
        logger.info(f"Fetched with Playwright: {url}")
        return html

def fetch_url(
    url: str,
    headers: dict = None,
    timeout: int = 20,
    throttle: float = 0.7,
    max_retries: int = 3,
    use_cache: bool = True,
    use_playwright: bool = False,
    proxies: list = None
) -> str:
    """
    Fetch a URL and return its text, with retries, advanced throttling, random User-Agent & optional proxy.
    Optionally use requests-cache or Playwright for JS-heavy sites.
    """
    if use_playwright:
        return fetch_with_playwright(url, timeout=timeout)
    last_exc = None
    proxy = random.choice(proxies or PROXY_LIST) if (proxies or PROXY_LIST) else None
    for attempt in range(max_retries):
        ua = (headers or {}).get("User-Agent") or get_random_user_agent()
        all_headers = {**DEFAULT_HEADERS, **(headers or {}), "User-Agent": ua}
        pre_request_hook(url, all_headers, proxy)
        try:
            session = get_session()
            # requests-cache is auto-installed if enabled
            resp = session.get(
                url,
                timeout=timeout,
                headers=all_headers,
                proxies={"http": proxy, "https": proxy} if proxy else None
            )
            post_response_hook(url, resp)
            resp.raise_for_status()
            throttle_delay(base_delay=throttle, jitter=0.3)
            return resp.text
        except Exception as e:
            last_exc = e
            logger.warning(f"Fetch failed ({url}), attempt {attempt+1}/{max_retries}: {e}")
            time.sleep(1.5 * (attempt + 1))
    log_and_alert_error(url, last_exc)
    raise last_exc

def get_soup(
    url: str,
    throttle: float = 0.7,
    max_retries: int = 3,
    headers: dict = None,
    timeout: int = 20,
    use_cache: bool = True,
    use_playwright: bool = False,
    proxies: list = None
):
    """
    Fetch a URL and return a BeautifulSoup object, with retries, throttling, rotating UA, etc.
    """
    html = fetch_url(
        url,
        headers=headers,
        timeout=timeout,
        throttle=throttle,
        max_retries=max_retries,
        use_cache=use_cache,
        use_playwright=use_playwright,
        proxies=proxies
    )
    return BeautifulSoup(html, "html.parser")

# Example usage for enabling cache
# enable_requests_cache(backend="sqlite", expire_after=3600)

# Example async usage:
# asyncio.run(fetch_url_async("https://www.table.se"))