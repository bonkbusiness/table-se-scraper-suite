"""
scraper/fetch.py

Advanced HTTP fetching utilities for the Table.se Scraper Suite.

Features:
    - Robust synchronous and asynchronous URL fetching with retries, throttling, proxy, and rotating User-Agent.
    - Thread-local sessions with retry logic and default headers.
    - Optional caching (requests-cache), and Playwright support for JavaScript-heavy pages.
    - BeautifulSoup integration for HTML parsing.
    - Hooks for request/response logging and error alerting.
    - Utility to enable HTTP cache (requests-cache) for efficiency.
    - Configurable for proxies, throttle, retry, headers, and advanced use cases.

USAGE:
    from scraper.fetch import fetch_url, get_soup, enable_requests_cache

    html = fetch_url("https://www.table.se")
    soup = get_soup("https://www.table.se")

    # For async:
    # import asyncio
    # html = asyncio.run(fetch_url_async("https://www.table.se"))

    # To enable caching:
    # enable_requests_cache(backend="sqlite", expire_after=3600)

DEPENDENCIES:
    - requests, aiohttp
    - BeautifulSoup (bs4)
    - requests-cache (optional)
    - playwright (optional for JS-heavy pages)
    - urllib3

Author: bonkbusiness
License: MIT
"""

import threading
import time
import random
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from scraper.logging import get_logger
    logger = get_logger("fetch")
except ImportError:
    import logging
    logger = logging.getLogger("fetch")

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    # Add more as needed for better anti-blocking
]
DEFAULT_HEADERS = {
    "User-Agent": random.choice(DEFAULT_USER_AGENTS),
    "Accept-Language": "sv,en;q=0.9",
}
PROXY_LIST = [
    # "http://user:pass@proxy1.example.com:8000",
    # "http://proxy2.example.com:8080",
    # Add more as needed
]

thread_local = threading.local()

def throttle_delay(base_delay=0.7, jitter=0.3):
    """
    Sleep for a randomized duration to throttle requests and avoid detection.
    """
    delay = base_delay + random.uniform(0, jitter)
    logger.debug(f"Sleeping for {delay:.2f}s to throttle requests.")
    time.sleep(delay)

def get_session():
    """
    Return a thread-local requests.Session with retry logic and default headers.
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
        session.headers.update({"Accept-Language": "sv,en;q=0.9"})
        thread_local.session = session
    return thread_local.session

def get_random_user_agent():
    """
    Select a random User-Agent string.
    """
    return random.choice(DEFAULT_USER_AGENTS)

def log_and_alert_error(url, error):
    """
    Log and hook for alerting/metrics on fetch error.
    """
    logger.error(f"ERROR fetching {url}: {error}")
    # Hook for alerting: integrate with monitoring/email/etc.

def pre_request_hook(url, headers, proxies):
    """
    Hook for logging/debugging before each request.
    """
    logger.debug(f"Requesting URL: {url} | Headers: {headers} | Proxies: {proxies}")

def post_response_hook(url, response):
    """
    Hook for logging/metrics after each response.
    """
    logger.info(f"Fetched {url} [status {getattr(response, 'status', response.status_code)}]")

# --- Asynchronous Fetching (aiohttp) ---

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
    Asynchronously fetch a URL with retries, throttling, and rotating User-Agent/proxy.

    Args:
        url (str): URL to fetch.
        headers (dict): Additional headers.
        timeout (int): Timeout per request.
        throttle (float): Base throttle delay.
        max_retries (int): Number of attempts.
        proxies (list): List of proxies.

    Returns:
        str: Response text.
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

# --- requests-cache Support (optional) ---

try:
    import requests_cache
    CACHE_ENABLED = True
except ImportError:
    CACHE_ENABLED = False

def enable_requests_cache(backend="sqlite", expire_after=3600, cache_name="http_cache"):
    """
    Enable requests-cache for persistent HTTP caching.

    Args:
        backend (str): Backend type (e.g. 'sqlite').
        expire_after (int): Expiry in seconds.
        cache_name (str): Name for cache DB/file.

    Returns:
        None
    """
    if CACHE_ENABLED:
        requests_cache.install_cache(cache_name=cache_name, backend=backend, expire_after=expire_after)
        logger.info(f"Enabled requests-cache: backend={backend}, expire_after={expire_after}s, cache_name={cache_name}")
    else:
        logger.warning("requests-cache not installed. Caching disabled.")

# --- Playwright Headless Browser Fetching (optional) ---

def fetch_with_playwright(url, timeout=30, headless=True):
    """
    Fetch page content using Playwright for JavaScript-heavy sites.

    Args:
        url (str): URL to fetch.
        timeout (int): Timeout in seconds.
        headless (bool): Run browser headless.

    Returns:
        str: The HTML content.

    Raises:
        ImportError: If Playwright is not installed.
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

# --- Synchronous Fetching ---

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
    Fetch a URL synchronously with retries, advanced throttling, rotating UA & optional proxy.
    Optionally use requests-cache or Playwright for JS-heavy sites.

    Args:
        url (str): URL to fetch.
        headers (dict): Additional headers.
        timeout (int): Timeout per request.
        throttle (float): Base throttle delay.
        max_retries (int): Number of attempts.
        use_cache (bool): Use HTTP cache if enabled.
        use_playwright (bool): Use Playwright for JS-heavy sites.
        proxies (list): List of proxies.

    Returns:
        str: Response text.

    Raises:
        Exception: If all attempts fail.
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
    Fetch a URL and return a BeautifulSoup object with advanced retry/throttling.

    Args:
        url (str): URL to fetch.
        throttle (float): Base delay between requests.
        max_retries (int): Number of tries.
        headers (dict): Extra headers.
        timeout (int): Timeout per request.
        use_cache (bool): Use HTTP cache if enabled.
        use_playwright (bool): Use Playwright for JS-heavy pages.
        proxies (list): List of proxies.

    Returns:
        BeautifulSoup: Parsed soup object.
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