"""Firefox web driver."""
import os
import tempfile
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from seleniumwire import webdriver as wire_webdriver
from webdriver_manager.firefox import GeckoDriverManager
from . import config_driver, config_selenium_wire


def web_driver(headless=False, data_dir: str = None, proxy_server: str = None, extensions_dirs: list[str] = None,
               download_manager: GeckoDriverManager = None):
    """Firefox web driver."""
    options = webdriver.FirefoxOptions()
    options.headless = headless
    if data_dir is not None:
        parent_data_dir = os.path.join(tempfile.gettempdir(), "selenium_browser_data")
        os.makedirs(parent_data_dir, exist_ok=True)
        options.profile = os.path.join(parent_data_dir, data_dir)

    if proxy_server is not None and proxy_server.find('@') == -1:
        result = urlparse(proxy_server)
        options.set_preference("network.proxy.type", 1)
        if result.scheme == 'socks5':
            options.set_preference("network.proxy.socks", result.hostname)
            options.set_preference("network.proxy.socks_port", result.port)
            options.set_preference("network.proxy.socks_version", 5)
        elif result.scheme in ('http', 'https'):
            options.set_preference("network.proxy.http", result.hostname)
            options.set_preference("network.proxy.http_port", result.port)
            options.set_preference("network.proxy.ssl", result.hostname)
            options.set_preference("network.proxy.ssl_port", result.port)
        else:
            raise ValueError(f"unsupported proxy server scheme: '{result.scheme}'")
        options.set_preference("network.proxy.no_proxies_on", "localhost, 127.0.0.1")
    if download_manager is None:
        download_manager = GeckoDriverManager()
    service = FirefoxService(download_manager.install())
    if proxy_server is not None and proxy_server.find('@') != -1:
        driver = wire_webdriver.Firefox(options=options, service=service,
                                        seleniumwire_options=config_selenium_wire(proxy_server))
    else:
        driver = webdriver.Firefox(options=options, service=service)

    if extensions_dirs is not None:
        for extensions_dir in extensions_dirs:
            for extension_name in os.listdir(extensions_dir):
                extension_dir = os.path.join(extensions_dir, extension_name)
                if os.path.isfile(extension_dir) and extension_dir.endswith('.xpi'):
                    driver.install_addon(extension_dir)
    return config_driver(driver)
