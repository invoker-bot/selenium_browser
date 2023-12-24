"""Firefox web driver."""
import os
import tempfile
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from seleniumwire import webdriver as wire_webdriver
from webdriver_manager.firefox import GeckoDriverManager
from . import config_driver


def web_driver(headless=False, data_dir: str = None, proxy_server: str = None, extensions_dirs: list[str] = None,
               download_manager: GeckoDriverManager = None):
    options = webdriver.FirefoxOptions()
    options.headless = headless
    if data_dir is not None:
        parent_data_dir = os.path.join(tempfile.gettempdir(), "selenium_browser_data")
        os.makedirs(parent_data_dir, exist_ok=True)
        data_dir = os.path.join(parent_data_dir, data_dir)
    profile = webdriver.FirefoxProfile(data_dir)
    profile.set_preference("intl.accept_languages", "en-us, en")
    profile.update_preferences()
    if headless:
        pass
    if proxy_server is not None:
        profile.set_preference("network.proxy.type", 1)
        profile.set_preference("network.proxy.http", proxy_server)
        profile.set_preference("network.proxy.http_port", 80)
        profile.set_preference("network.proxy.ssl", proxy_server)
        profile.set_preference("network.proxy.ssl_port", 80)
        profile.set_preference("network.proxy.ftp", proxy_server)
        profile.set_preference("network.proxy.ftp_port", 80)
        profile.set_preference("network.proxy.socks", proxy_server)
        profile.set_preference("network.proxy.socks_port", 80)
        profile.set_preference("network.proxy.socks_version", 5)
        profile.set_preference("network.proxy.socks_remote_dns", True)
        profile.set_preference("network.proxy.share_proxy_settings", True)
        profile.set_preference("network.proxy.no_proxies_on", "localhost, 127.0.0.1")

        # if proxy_server.find('@') == -1:

    if extensions_dirs is not None:
        for extensions_dir in extensions_dirs:
            for extension_name in os.listdir(extensions_dir):
                extension_dir = os.path.join(extensions_dir, extension_name)
                if os.path.isfile(extension_dir) and extension_dir.endswith('.xpi'):
                    profile.add_extension(extension_dir)
    service = FirefoxService(GeckoDriverManager().install())
    if proxy_server is not None and proxy_server.find('@') != -1:
        driver = wire_webdriver.Firefox(options=options, firefox_profile=profile, service=service)
    else:
        driver = webdriver.Firefox(options=options, service=service)
    return config_driver(driver)
