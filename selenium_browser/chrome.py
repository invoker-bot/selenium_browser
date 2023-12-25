"""ChromeDriver instance"""""
import os
from selenium import webdriver
import undetected_chromedriver as uc
import seleniumwire.undetected_chromedriver as wire_uc
from webdriver_manager.chrome import ChromeDriverManager
from . import RemoteBrowser, BrowserOptions


class ChromeBrowser(RemoteBrowser):
    """Chrome browser"""

    @classmethod
    def config_driver_options(cls, options: BrowserOptions, driver_options: webdriver.ChromeOptions):
        """Driver options"""
        driver_options.add_argument("--lang=en")
        driver_options.add_argument("--no-first-run")
        driver_options.add_argument("--disable-notifications")
        driver_options.add_argument("--ignore-certificate-errors")
        if options.headless:
            driver_options.add_argument("--headless")
            driver_options.add_argument("--no-sandbox")
            driver_options.add_argument("--disable-dev-shm-usage")
            driver_options.add_argument("--disable-gpu")
        if options.data_dir is not None:
            driver_options.add_argument(f"--user-data-dir={cls.get_data_dir(options.data_dir)}")
        if options.proxy_server is not None and not cls.use_seleniumwire(options):
            # proxy_server is not a proxy server with authentication
            driver_options.add_argument(f'--proxy-server={options.proxy_server}')
        if options.extensions_dirs is not None:
            load_extension_dirs = []
            for extensions_dir in options.extensions_dirs:
                for extension_name in os.listdir(extensions_dir):
                    extension_dir = os.path.join(extensions_dir, extension_name)
                    if os.path.isdir(extension_dir):
                        load_extension_dirs.append(extension_dir)
                    elif extension_dir.endswith('.crx'):
                        driver_options.add_extension(extension_dir)
            if len(load_extension_dirs) > 0:
                driver_options.add_argument(f'--load-extension={",".join(load_extension_dirs)}')
        return driver_options

    @classmethod
    def driver_options(cls, options):
        """Driver options"""
        driver_options = webdriver.ChromeOptions()
        return cls.config_driver_options(options, driver_options)

    @classmethod
    def driver_service(cls, driver_manager):
        """Driver service"""
        return webdriver.ChromeService(driver_manager.install())

    @classmethod
    def new_driver(cls, options, driver_options, service):
        """Default driver"""
        if cls.use_seleniumwire(options):
            return wire_uc.Chrome(options=driver_options, service=service,
                                  seleniumwire_options=cls.default_seleniumwire_config(options))
        return uc.Chrome(options=driver_options, service=service)

    @classmethod
    def default_driver_manager(cls):
        """Default driver manager"""
        return ChromeDriverManager()
