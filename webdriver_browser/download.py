"""Auto download driver functions and classes."""
from typing import Optional
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
