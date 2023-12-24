"""ChromeDriver instance"""""
import os
import tempfile
from selenium import webdriver
import undetected_chromedriver as uc
import seleniumwire.undetected_chromedriver as wire_uc
from selenium.webdriver.chrome.service import Service as ChromeService  # pylint: disable=ungrouped-imports
from selenium.webdriver.chromium.options import ChromiumOptions  # pylint: disable=ungrouped-imports
from webdriver_manager.chrome import ChromeDriverManager
from . import config_driver, config_selenium_wire


def config_chromium_options(options: ChromiumOptions, headless=False, data_dir: str = None, proxy_server: str = None,
                            extensions_dirs: list[str] = None):
    """Configure ChromiumOptions"""
    options.add_argument("--lang=en")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-notifications")
    if headless:
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
    if data_dir is not None:
        data_dir = os.path.join(tempfile.gettempdir(), "selenium_browser_data")
        os.makedirs(data_dir, exist_ok=True)
        user_data_dir = os.path.join(data_dir, data_dir)
        options.add_argument(f"--user-data-dir={user_data_dir}")
    if proxy_server is not None:
        if proxy_server.find('@') == -1:  # proxy_server is not a proxy server with authentication
            options.add_argument(f'--proxy-server={proxy_server}')
    if extensions_dirs is not None:
        load_extension_dirs = []
        for extensions_dir in extensions_dirs:
            for extension_name in os.listdir(extensions_dir):
                extension_dir = os.path.join(extensions_dir, extension_name)
                if os.path.isdir(extension_dir):
                    load_extension_dirs.append(extension_dir)
                elif extension_dir.endswith('.crx'):
                    options.add_extension(extension_dir)
        if len(load_extension_dirs) > 0:
            options.add_argument(f'--load-extension={",".join(load_extension_dirs)}')
    return options


def web_driver(headless=False, data_dir: str = None, proxy_server: str = None, extensions_dirs: list[str] = None,
               download_manager: ChromeDriverManager = None):
    """Create a ChromeDriver instance"""
    options = config_chromium_options(webdriver.ChromeOptions(), headless=headless, data_dir=data_dir,
                                      proxy_server=proxy_server, extensions_dirs=extensions_dirs)
    if download_manager is None:
        download_manager = ChromeDriverManager()
    service = ChromeService(download_manager.install())
    if proxy_server is not None and proxy_server.find('@') != -1:
        driver = wire_uc.Chrome(options=options, service=service,
                                seleniumwire_options=config_selenium_wire(proxy_server))
    else:
        driver = uc.Chrome(options=options, service=service)
    return config_driver(driver)
