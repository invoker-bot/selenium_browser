"""Firefox web driver."""
import os
from urllib.parse import urlparse
from selenium import webdriver
from seleniumwire import webdriver as wire_webdriver
from webdriver_manager.firefox import GeckoDriverManager
from . import RemoteBrowser


class FirefoxBrowser(RemoteBrowser):
    """Firefox browser"""

    @classmethod
    def driver_options(cls, options):
        """Driver options"""
        driver_options = webdriver.FirefoxOptions()
        driver_options.accept_insecure_certs = True
        driver_options.headless = options.headless
        if options.data_dir is not None:
            cls.make_root_data_dir()
            options.profile = cls.get_data_dir(options.data_dir)
        if options.proxy_server is not None and not cls.use_seleniumwire(options):
            result = urlparse(options.proxy_server)
            if result.scheme == 'socks5':
                driver_options.set_preference("network.proxy.socks", result.hostname)
                driver_options.set_preference("network.proxy.socks_port", result.port)
                driver_options.set_preference("network.proxy.socks_version", 5)
            elif result.scheme in ('http', 'https'):
                driver_options.set_preference("network.proxy.http", result.hostname)
                driver_options.set_preference("network.proxy.http_port", result.port)
                driver_options.set_preference("network.proxy.ssl", result.hostname)
                driver_options.set_preference("network.proxy.ssl_port", result.port)
            else:
                raise ValueError(f"unsupported proxy server scheme: '{result.scheme}'")
            driver_options.set_preference("network.proxy.type", 1)
            driver_options.set_preference("network.proxy.no_proxies_on", "localhost, 127.0.0.1")
        return driver_options

    @classmethod
    def driver_service(cls, driver_manager):
        """Driver service"""
        return webdriver.FirefoxService(driver_manager.install())

    @classmethod
    def new_driver(cls, options, driver_options, service):
        """Default driver"""
        if cls.use_seleniumwire(options):
            return wire_webdriver.Firefox(options=driver_options, service=service,
                                          seleniumwire_options=cls.default_seleniumwire_config(options))
        return webdriver.Firefox(options=driver_options, service=service)

    @classmethod
    def default_driver_manager(cls):
        """Default driver manager"""
        return GeckoDriverManager()

    def config_driver(self):
        """Configure the driver"""
        if self.options.extensions_dirs is not None:
            for extensions_dir in self.options.extensions_dirs:
                for extension_name in os.listdir(extensions_dir):
                    extension_dir = os.path.join(extensions_dir, extension_name)
                    if os.path.isfile(extension_dir) and extension_dir.endswith('.xpi'):
                        self.driver.install_addon(extension_dir)
        super().config_driver()
