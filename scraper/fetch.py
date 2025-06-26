import threading
import time
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

thread_local = threading.local()

def get_session():
    """
    Get a thread-local requests.Session with retry logic.
    """
    if not hasattr(thread_local, "session"):
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        thread_local.session = session
    return thread_local.session

def get_soup_with_retries(url: str, throttle: float = 0.7, max_retries: int = 3):
    """
    Fetch a URL and return a BeautifulSoup object, with retries and throttling.
    """
    last_exc = None
    for attempt in range(max_retries):
        try:
            session = get_session()
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
            time.sleep(throttle)
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            last_exc = e
            print(f"Fetch failed ({url}), attempt {attempt+1}/{max_retries}: {e}")
            time.sleep(1.5 * (attempt + 1))
    print(f"ERROR: Giving up on {url}: {last_exc}")
    return None

get_soup = get_soup_with_retries  # Alias for convenience
