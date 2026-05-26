import time
from typing import Optional

import requests

from .. import config


class FetchError(Exception):
    pass


def fetch_list_html(url: str = config.NOTICE_LIST_URL) -> str:
    headers = {"User-Agent": config.USER_AGENT}
    last_err: Optional[Exception] = None

    for attempt in range(1, config.HTTP_RETRY_COUNT + 1):
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=config.HTTP_TIMEOUT_SEC,
            )
            response.raise_for_status()
            response.encoding = "utf-8"
            return response.text
        except Exception as exc:
            last_err = exc
            print(
                f"[fetcher] attempt {attempt}/{config.HTTP_RETRY_COUNT} "
                f"failed: {exc!r}"
            )
            if attempt < config.HTTP_RETRY_COUNT:
                time.sleep(config.HTTP_RETRY_DELAY_SEC)

    raise FetchError(f"HTTP fetch failed after 3 retries: {last_err!r}")
