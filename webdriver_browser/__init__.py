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
from pyee import EventEmitter
from tenacity import Retrying, stop_after_attempt, wait_random_exponential, after_log, before_log, retry_if_exception_type, retry_if_not_result
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


D = TypeVar("D", bound=Union[WebDriver, WebElement])
T = TypeVar("T")
R = TypeVar("R")
logger = logging.getLogger('selenium_browser')


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


class RemoteBrowser(ABC):  # pylint: disable=too-many-public-methods
    """Remote browser"""

    def __init__(self, options: BrowserOptions = None, driver_manager: DriverManager = None):
        if options is None:
            options = BrowserOptions()
        self.options = options
        if driver_manager is None:
            driver_manager = self.default_driver_manager()
        if options.data_dir is not None:  # pylint: disable=too-many-nested-blocks
            self.make_root_data_dir()
            if options.compressed:
                if not os.path.isdir(self.get_data_dir('default')):
                    default_options = BrowserOptions(data_dir='default', headless=True, compressed=False)
                    default_driver = self.new_driver(default_options, self.driver_options(
                        default_options), self.driver_service(driver_manager))
                    default_driver.quit()
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
        self.driver = self.new_driver(options, self.driver_options(options), self.driver_service(driver_manager))
        self.config_driver()
        self.wait = WebDriverWait(self.driver, options.wait_timeout)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.__exit__(exc_type, exc_val, exc_tb)

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
        with suppress(WebDriverException):
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
    def new_driver(cls, options: BrowserOptions, driver_options: DriverOptions, service: DriverService) -> WebDriver:
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

    def get_until(self, url: str, method: Callable[[D], T]) -> T:
        """Get the url until the method is true"""
        current_result = self.normilize_url_result(self.driver.current_url)
        target_result = self.normilize_url_result(url)
        if current_result.netloc != target_result.netloc or current_result.path != target_result.path or not method(self.driver):
            self.driver.get(url)
        return self.wait.until(method)

    def scroll_to_view(self, locator: tuple[str, str], force=False) -> WebElement:
        """Scroll to the element"""
        elem = self.wait.until(EC.presence_of_element_located(locator))
        if force or not elem.is_displayed():
            self.driver.execute_script("arguments[0].scrollIntoView();", elem)
        return elem

    def select(self, locator: tuple[str, str]):
        """Select the element(radio or checkbox)"""
        elem = self.scroll_to_view(locator, force=True)
        elem = self.wait.until(EC.element_to_be_clickable(elem))
        if not elem.is_selected():
            elem.click()
            self.wait.until(EC.element_to_be_selected(locator))

    def click(self, locator: tuple[str, str]):
        """Click the element"""
        elem = self.scroll_to_view(locator)
        elem = self.wait.until(EC.element_to_be_clickable(elem))
        elem.click()

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


@dataclass
class WebActionContext:
    """Web action context"""
    browser: RemoteBrowser
    ee: EventEmitter
    data: dict


ActionCall = Callable[[WebActionContext, T], R]
ConditionCall = Callable[[WebActionContext, None], T]
MethodCall = Union[ActionCall, ConditionCall]


class WebAction:
    """Web action"""

    def __init__(self, fn: MethodCall, name=None):
        self.fn = fn
        if name is None:
            name = getattr(fn, '__name__', str(fn))
        self.name = name

    # whether the action is expected
    def expected_condition(self, context: WebActionContext) -> Callable[[WebDriver], T]:
        """Expected condition"""
        return lambda _driver: self.fn(context, None)

    def condition(self, context: WebActionContext, wait=False) -> T:  # whether to execute the action
        """Condition"""
        if wait:
            return context.browser.wait.until(self.expected_condition(context))
        return self.fn(context, None)

    def condition_noexcept(self, context: WebActionContext, wait=False) -> Optional[T]:
        """Condition no exception"""
        try:
            return self.condition(context, wait)
        except (WebDriverException, TimeoutError):
            return None

    def __call__(self, context: WebActionContext, wait=False, retry=1) -> tuple[T, Callable[[T], R]]:
        condition = self.condition(context, wait)
        retrying = Retrying(retry=(retry_if_exception_type((WebDriverException, TimeoutError)) | retry_if_not_result(lambda r: r)) &  # noqa: W504
                            (lambda _: self.condition_noexcept(context, wait)),
                            stop=stop_after_attempt(retry), wait=wait_random_exponential(multiplier=5, max=600, min=5), reraise=True,
                            before=before_log(logger, logging.DEBUG), after=after_log(logger, logging.DEBUG))
        return condition, partial(retrying, self.fn, context)


class ChainWebAction(WebAction):
    """Chain web action"""
    def __init__(self, *actions: WebAction, name=None, retry=1, reentry=False):
        assert len(actions) > 0, "At least one action"
        if name is None:
            name = f'chain({", ".join(action.name for action in actions)})'

        def fn(context: WebActionContext, condition: Optional[tuple[int, T]]) -> Optional[R]:
            if condition:  # pylint: disable=no-else-return
                idx, c = condition
                assert not (reentry and idx > 0), "Reentry is not allowed"
                result = None
                for action in actions[idx:]:
                    c, a = action(context, wait=True, retry=retry)
                    result = a(c)
                    if not (c and result):
                        return None
                    time.sleep(5)
                return result
            else:
                if reentry:
                    for idx, action in enumerate(actions):
                        c = action.condition_noexcept(context, wait=False)
                        if c:
                            return idx, c
                else:
                    c = actions[0].condition(context, wait=False)
                return (0, c) if c else None
        super().__init__(fn, name)


class SwitchWebAction(WebAction):
    """Switch web action"""
    def __init__(self, *actions: WebAction, name=None, retry=1):
        assert len(actions) > 0, "At least one action"
        if name is None:
            name = f'switch({", ".join(action.name for action in actions)})'

        def fn(context: WebActionContext, condition: Optional[tuple[int, T]]) -> Optional[R]:
            if condition:  # pylint: disable=no-else-return
                idx, c = condition
                c, a = actions[idx](context, wait=True, retry=retry)
                return a(c)
            else:
                for idx, action in enumerate(actions):
                    c = action.condition_noexcept(context, wait=False)
                    if c:
                        return idx, c
                return None
        super().__init__(fn, name)


def web_action(fn: MethodCall, name=None):
    """Web action"""
    return WebAction(fn, name=name)
