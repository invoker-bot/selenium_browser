"""Selenium Browser"""
import os
import shutil
import tempfile
from abc import ABC, abstractmethod
from typing import Type
from dataclasses import dataclass
from selenium import webdriver
from requests.exceptions import RequestException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.service import Service as DriverService
from selenium.webdriver.common.options import ArgOptions as DriverOptions
from webdriver_manager.core.manager import DriverManager


@dataclass
class BrowserOptions:
    """options"""
    data_dir: str = None
    proxy_server: str = None
    extensions_dirs: list[str] = None
    headless: bool = False
    force_selenium_wire: bool = False
    wait_timeout: float = 15.0


class RemoteBrowser(ABC):
    """Remote browser"""
    options: BrowserOptions
    driver: Type[webdriver.Remote]
    wait: WebDriverWait

    def __init__(self, options: BrowserOptions = None, driver_manager: DriverManager = None):
        if options is None:
            options = BrowserOptions()
        self.options = options
        if driver_manager is None:
            driver_manager = self.default_driver_manager()
        self.driver = self.new_driver(options, self.driver_options(options), self.driver_service(driver_manager))
        self.config_driver()
        self.wait = WebDriverWait(self.driver, options.wait_timeout)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.__exit__(exc_type, exc_val, exc_tb)

    def quit(self):
        """Quit the browser"""
        self.driver.quit()

    @classmethod
    @abstractmethod
    def driver_options(cls, options: BrowserOptions) -> DriverOptions:
        """Driver options"""

    @classmethod
    @abstractmethod
    def driver_service(cls, driver_manager) -> DriverService:
        """Driver service"""

    @classmethod
    @abstractmethod
    def new_driver(cls, options: BrowserOptions, driver_options: DriverOptions, service: DriverService) -> webdriver.Remote:
        """Default driver"""

    @classmethod
    @abstractmethod
    def default_driver_manager(cls) -> DriverManager:
        """Default driver manager"""

    @classmethod
    def use_seleniumwire(cls, options: BrowserOptions):
        """Use seleniumwire or not"""
        return options.force_selenium_wire or (options.proxy_server is not None and options.proxy_server.find('@') != -1)

    @classmethod
    def default_seleniumwire_config(cls, options: BrowserOptions):
        """Default seleniumwire config"""
        return {
            'proxy': {
                'http': options.proxy_server,
                'https': options.proxy_server,
                'no_proxy': 'localhost, 127.0.0.1',
            }
        }

    @classmethod
    def is_installed(cls) -> bool:
        """Check if the browser is installed"""
        try:
            browser = cls(BrowserOptions(headless=True))
            browser.quit()
            return True
        except (WebDriverException, RequestException):
            return False

    def config_driver(self):
        """Configure the driver"""
        self.driver.set_window_size(int(os.getenv('SELENIUM_BROWSER_WINDOW_WIDTH', '1920')),
                                    int(os.getenv('SELENIUM_BROWSER_WINDOW_HEIGHT', '1080')))
        self.driver.implicitly_wait(float(os.getenv('SELENIUM_BROWSER_IMPLICITLY_WAIT', '3')))

    @classmethod
    def get_root_data_dir(cls):
        """Root data dir"""
        return os.path.join(os.getenv('SELENIUM_BROWSER_ROOT_DATA_DIR', tempfile.gettempdir()), "selenium_browser_data")

    @classmethod
    def make_root_data_dir(cls):
        """Make root data dir"""
        os.makedirs(cls.get_root_data_dir(), exist_ok=True)

    @classmethod
    def get_data_dir(cls, name: str):
        """Data dir"""
        return os.path.join(cls.get_root_data_dir(), name)

    @classmethod
    def clear_root_data_dir(cls):
        """Clear all data"""
        root_dir = cls.get_root_data_dir()
        if os.path.isdir(root_dir):
            shutil.rmtree(root_dir)

    @classmethod
    def clear_data_dir(cls, name: str):
        """Clear data"""
        data_dir = cls.get_data_dir(name)
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)

    @property
    def data_dir(self):
        """Data dir"""
        return self.get_data_dir(self.options.data_dir)

    @data_dir.setter
    def data_dir(self, value):  # pylint: disable=unused-argument
        """Data dir"""
        if self.options.data_dir is not None:
            self.make_root_data_dir()

    @data_dir.deleter
    def data_dir(self):
        """Data dir"""
        if self.options.data_dir is not None:
            self.clear_data_dir(self.options.data_dir)
