"""Edge browser driver"""
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from seleniumwire import webdriver as wire_webdriver
from . import config_driver, config_selenium_wire
from .chrome import config_chromium_options


def web_driver(headless=False, data_dir: str = None, proxy_server: str = None, extensions_dirs: list[str] = None,
               download_manager: EdgeChromiumDriverManager = None):
    """Create a ChromeDriver instance"""
    options = config_chromium_options(webdriver.ChromeOptions(), headless=headless, data_dir=data_dir,
                                      proxy_server=proxy_server, extensions_dirs=extensions_dirs)
    if download_manager is None:
        download_manager = EdgeChromiumDriverManager()
    service = EdgeService(download_manager.install())
    if proxy_server is not None and proxy_server.find('@') != -1:
        driver = wire_webdriver.Edge(options=options, service=service,
                                     seleniumwire_options=config_selenium_wire(proxy_server))
    else:
        driver = webdriver.Edge(options=options, service=service)
    return config_driver(driver)
