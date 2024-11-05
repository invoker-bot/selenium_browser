"""Selenium Browser"""
import os
import time
import shutil
import tempfile
import logging
from contextlib import suppress
from urllib.parse import urlparse, ParseResult
from abc import ABC, abstractmethod
from typing import Callable, Optional, Union, TypeVar
from dataclasses import dataclass
from functools import partial
import psutil
from tenacity import Retrying as _Retrying, retry as _retry, stop_after_attempt, wait_random_exponential, after_log, before_log, \
    retry_if_exception_type
from requests.exceptions import RequestException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.service import Service as DriverService
from selenium.webdriver.common.options import ArgOptions as DriverOptions
from webdriver_manager.core.manager import DriverManager
from .patch import pack_dir_with_ref, unpack_dir_with_ref
from .session import Sessionium
from .utils import to_proxy_dict


D = TypeVar("D", bound=Union[WebDriver, WebElement])
T = TypeVar("T")
R = TypeVar("R")
logger = logging.getLogger('selenium_browser')


class RetryingException(Exception):
    """Retry exception"""


default_stop_condition = stop_after_attempt(3)
default_wait_action = wait_random_exponential(max=30)
default_retry_condition = retry_if_exception_type(
    (WebDriverException, RequestException, TimeoutError, RetryingException))
before_log_action = before_log(logger, logging.DEBUG)
after_log_action = after_log(logger, logging.DEBUG)
retry = partial(_retry, stop=default_stop_condition, wait=default_wait_action, retry=default_retry_condition,
                before=before_log_action, after=after_log_action)
Retrying = partial(_Retrying, stop=default_stop_condition, wait=default_wait_action, retry=default_retry_condition,
                   before=before_log_action, after=after_log_action)


@dataclass
class BrowserOptions:
    """options"""
    data_dir: str = None
    proxy_server: str = None
    extensions_dirs: list[str] = None
    headless: bool = False
    force_selenium_wire: bool = False
    wait_timeout: float = 15.0
    compressed: bool = False
    singleton: bool = False
    disable_image: bool = False
    use_multi_procs: bool = False
    undetected_chrome_driver: bool = True
    proxy_downloader: str = None


class RemoteBrowser(ABC):  # pylint: disable=too-many-public-methods
    """Remote browser"""
    browser_names = {'msedge', 'chrome', 'firefox', 'firefox-bin'}

    def __init__(self, options: Optional[BrowserOptions] = None):
        if options is None:
            options = BrowserOptions()
        self.options = options
        self.session = Sessionium(driver_creater=self._initialize_driver, default_timeout=options.wait_timeout,
                                  headless=options.headless)
        self._wait = None

    def _initialize_driver(self):
        options = self.options
        if options.singleton:
            self.kill_all_browser()
        driver_manager = self._default_driver_manager()
        if options.data_dir is not None:  # pylint: disable=too-many-nested-blocks
            self.make_root_data_dir()
            if options.compressed:
                if not os.path.isdir(self.get_data_dir('default')):
                    default_options = BrowserOptions(data_dir='default', headless=True, compressed=False)
                    current_options = self.options
                    self.options = default_options
                    default_driver = self._new_driver(self._driver_options(), self._driver_service(driver_manager))
                    default_driver.quit()
                    self.options = current_options
                if not os.path.isdir(self.get_data_dir('default')):
                    options.compressed = False
                    logger.warning("Reference dir '%s' not created, using uncompressed data dir", options.data_dir)
                else:
                    compressed_file = self.get_data_dir(options.data_dir + ".patch")
                    if not os.path.exists(self.data_dir):
                        if os.path.exists(compressed_file):
                            try:
                                unpack_dir_with_ref(self.get_data_dir('default'), compressed_file, self.data_dir)
                            except ValueError:
                                logger.warning("Reference dir '%s' changed, using uncompressed data",
                                               self.get_data_dir('default'))
        driver = self._new_driver(self._driver_options(), self._driver_service(driver_manager))
        self.session._driver = driver  # pylint: disable=protected-access
        self._config_driver()
        if options.proxy_server is not None:
            self.session.proxies = to_proxy_dict(options.proxy_server)
        self._wait = WebDriverWait(driver, options.wait_timeout)
        return driver

    @property
    def driver(self):
        """Driver"""
        return self.session.driver

    @property
    def wait(self):
        """Should get the driver first or will return None"""
        return self._wait

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # self.driver.__exit__(exc_type, exc_val, exc_tb)
        self.quit()

    def __del__(self):
        pass

    def is_locked(self):
        """Check if the browser is locked"""
        data_dir = self.data_dir
        if data_dir is not None:
            for filename in ('lockfile', 'SingletonCookie', 'SingletonLock', 'parent.lock'):
                if os.path.exists(os.path.join(data_dir, filename)):
                    return True
        return False

    def quit(self):
        """Quit the browser"""
        if self.session._driver is None:  # pylint: disable=protected-access
            return
        with suppress(WebDriverException, ConnectionResetError):
            self.driver.quit()
        if self.options.data_dir is not None:
            self.wait.until_not(lambda _: self.is_locked())
            time.sleep(3)
            if self.options.compressed:
                if os.path.isdir(self.data_dir):
                    if os.path.isdir(self.get_data_dir('default')):
                        compressed_file = self.get_data_dir(self.options.data_dir + ".patch")
                        pack_dir_with_ref(self.get_data_dir('default'), compressed_file, self.data_dir)
                    else:
                        logger.warning("Default dir '%s' not found, removing data dir", self.get_data_dir('default'))
                        shutil.rmtree(self.get_data_dir(self.options.data_dir))
                else:
                    logger.warning("Data dir '%s' not found", self.data_dir)

    @abstractmethod
    def _driver_options(self) -> DriverOptions:
        """Driver options"""

    @abstractmethod
    def _driver_service(self, driver_manager: DriverManager) -> DriverService:
        """Driver service"""

    @abstractmethod
    def _new_driver(self, driver_options: DriverOptions, service: DriverService) -> WebDriver:
        """Default driver"""

    @abstractmethod
    def _default_driver_manager(self) -> DriverManager:
        """Default driver manager"""

    def _use_seleniumwire(self):
        """Use seleniumwire or not"""
        return self.options.force_selenium_wire or (self.options.proxy_server is not None and self.options.proxy_server.find('@') != -1)

    @classmethod
    def kill_all_browser(cls):
        """Kill all browsers"""
        for proc in psutil.process_iter(['pid', 'name']):
            proc_name = proc.info['name'].split('.')[0].lower()
            if proc_name in cls.browser_names:
                try:
                    process = psutil.Process(proc.info['pid'])
                    process.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    logger.warning("zombie process: %s(%s)", proc_name, proc.info['pid'])

    def _default_seleniumwire_config(self):
        """Default seleniumwire config"""
        return {
            'proxy': {
                'http': self.options.proxy_server,
                'https': self.options.proxy_server,
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

    def _config_driver(self):
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
        if os.path.isdir(data_dir):
            shutil.rmtree(data_dir, ignore_errors=True)
        if os.path.isfile(data_dir + ".patch"):
            os.remove(data_dir + ".patch")

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

    @staticmethod
    def normilize_url_result(url: str) -> ParseResult:
        """Normilize url"""
        result = urlparse(url)
        if not result.path:
            result.path = '/'
        return result

    @retry()
    def get_until(self, url: str, method: Callable[[D], T]) -> T:
        """Get the url until the method is true"""
        current_result = self.normilize_url_result(self.driver.current_url)
        target_result = self.normilize_url_result(url)
        if current_result.netloc != target_result.netloc or current_result.path != target_result.path or not method(self.driver):
            self.driver.get(url)
        return self.wait.until(method)

    @retry()
    def scroll_to_view(self, locator: tuple[str, str], force=False) -> WebElement:
        """Scroll to the element"""
        elem = self.wait.until(EC.presence_of_element_located(locator))
        if force or not elem.is_displayed():
            self.driver.execute_script("arguments[0].scrollIntoView();", elem)
        return elem

    @retry()
    def select(self, locator: tuple[str, str]):
        """Select the element(radio or checkbox)"""
        elem = self.scroll_to_view(locator, force=True)
        elem = self.wait.until(EC.element_to_be_clickable(elem))
        if not elem.is_selected():
            elem.click()
            self.wait.until(EC.element_to_be_selected(locator))

    @retry()
    def click(self, locator: tuple[str, str]):
        """Click the element"""
        elem = self.scroll_to_view(locator)
        elem = self.wait.until(EC.element_to_be_clickable(elem))
        elem.click()

    @retry()
    def input(self, locator: tuple[str, str], value: str, clear=False):
        """Input some value to the element"""
        elem = self.wait.until(EC.element_to_be_clickable(locator))
        if clear:
            length = len(elem.get_attribute('value'))
            for _ in range(length):
                elem.send_keys(Keys.BACKSPACE)
                time.sleep(self.wait._poll)  # pylint: disable=protected-access
            elem.send_keys(value)
        else:
            self.driver.execute_script("arguments[0].value = arguments[1];", elem, value)
