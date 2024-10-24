"""Utility functions for the webdriver_browser package."""
from typing import Optional


def to_proxy_dict(proxy: Optional[str | dict] = None) -> Optional[dict]:
    """Convert a proxy string or dict to a proxy dict.

    Args:
        proxy(Optional[str | dict]): The proxy string or dict.
    Returns:
        Optional[dict]: The proxy dict.
    """
    if proxy is not None:
        if isinstance(proxy, str):
            proxy = {'http': proxy, 'https': proxy}
        elif hasattr(proxy, 'http_proxy'):
            http_proxy = getattr(proxy, 'http_proxy')
            proxy = {'http': http_proxy, 'https': http_proxy}
    return proxy
