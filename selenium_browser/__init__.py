"""Selenium Browser"""
import os
from typing import Type
from dataclasses import dataclass
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from webdriver_manager.core.manager import DriverManager


@dataclass
class BrowserOptions:
    """options"""
    data_dir: str = None
    proxy_server: str = None
    extensions_dirs: list[str] = None
    headless: bool = False


def driver_service(service_cls: Type[Service], driver_manager_cls: Type[DriverManager], driver_manager_kwargs: dict = None):
    if driver_manager_kwargs is None:
        driver_manager_kwargs = {}
    return service_cls(driver_manager_cls(**driver_manager_kwargs).install())


def config_driver(driver: webdriver.Remote):
    driver.set_window_size(int(os.getenv('SELENIUM_BROWSER_WINDOW_WIDTH', '1920'),
                           int('SELENIUM_BROWSER_WINDOW_HEIGHT', '1080')))
    driver.implicitly_wait(float(os.getenv('SELENIUM_BROWSER_IMPLICITLY_WAIT', '3')))
    return driver


def config_selenium_wire(proxy_server: str):
    return {
        'proxy': {
            'http': proxy_server,
            'https': proxy_server,
            'no_proxy': 'localhost, 127.0.0.1',
        }
    }
