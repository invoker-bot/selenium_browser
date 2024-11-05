"""Auto download driver functions and classes."""
from typing import Optional
import urllib.request
import requests
from webdriver_manager.core.download_manager import WDMDownloadManager
from webdriver_manager.core.http import WDMHttpClient
from .utils import to_proxy_dict


class ProxyHttpClient(WDMHttpClient):
    """HTTP client with proxy support."""
    def __init__(self, proxy: Optional[str | dict] = None):
        super().__init__()
        self.proxy = to_proxy_dict(proxy)

    def get(self, url: str, **kwargs):
        # print(f"ProxyHttpClient.get: {url}")
        try:
            resp = requests.get(
                url=url, verify=self._ssl_verify, stream=True, proxies=self.proxy, timeout=30, **kwargs)
        except requests.exceptions.ConnectionError as e:
            raise requests.exceptions.ConnectionError("Could not reach host. Are you offline?") from e
        self.validate_response(resp)
        return resp


def get_wdm_download_manager(proxy: Optional[str | dict] = None):
    """Get the download manager."""
    return WDMDownloadManager(http_client=ProxyHttpClient(proxy))


class ProxyConfig:
    """Context manager for setting urllib proxies."""
    def __init__(self, proxy: Optional[str | dict] = None):
        self.proxies = to_proxy_dict(proxy)
        self.opener = None
        self.old_opener = urllib.request._opener

    def __enter__(self):
        if self.proxies is not None:
            proxy_handler = urllib.request.ProxyHandler(self.proxies)
            self.opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(self.opener)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.proxies is not None:
            urllib.request.install_opener(self.old_opener)
