"""ChromeDriver instance"""""
import os
import shutil
from selenium import webdriver
import undetected_chromedriver as uc
import seleniumwire.webdriver as wire_webdriver
import seleniumwire.undetected_chromedriver as wire_uc
from undetected_chromedriver.patcher import Patcher
from webdriver_manager.chrome import ChromeDriverManager
from . import RemoteBrowser, BrowserOptions


class ChromeBrowser(RemoteBrowser):
    """Chrome browser"""
    browser_names = {'chrome', 'googlechrome', 'google-chrome', 'gc'}

    @classmethod
    def config_driver_options(cls, options: BrowserOptions, driver_options: webdriver.ChromeOptions):
        """Driver options"""
        driver_options.add_argument("--lang=en")
        driver_options.add_argument("--no-first-run")
        driver_options.add_argument("--disable-notifications")
        driver_options.add_argument("--ignore-certificate-errors")
        if options.disable_image:
            driver_options.add_argument('--blink-settings=imagesEnabled=false')
        if options.headless:
            if options.extensions_dirs is not None:
                driver_options.add_argument("--headless=new")
            else:
                driver_options.add_argument("--headless")
            # driver_options.add_argument("--no-sandbox")
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
    def driver_service(cls, options, driver_manager):
        """Driver service"""
        return None if cls.use_undetected_driver(options) else webdriver.ChromeService(driver_manager.install())

    @classmethod
    def use_undetected_driver(cls, options: BrowserOptions):
        """Undetected driver"""
        if options.undetected_chrome_driver is not None:
            return options.undetected_chrome_driver
        return os.getenv('UNDETECTED_CHROME_DRIVER', 'true').lower() not in ('false', '0', 'off', 'no', '')

    @classmethod
    def new_driver(cls, options, driver_options, service):
        """Default driver
        set UNDETECTED_CHROME_DRIVER=false will not use undetected_chromedriver
        """
        user_data_dir = None
        if cls.use_undetected_driver(options):
            if options.data_dir is None:  # should set tmp
                options.data_dir = user_data_dir = cls.get_data_dir('.tmp')
                shutil.rmtree(user_data_dir, ignore_errors=True)
            chrome_driver_manager = cls.default_driver_manager()
            #  driver_executable_path = chrome_driver_manager.install()
            version = chrome_driver_manager.driver.get_browser_version_from_os()
            driver_executable_path = os.path.join(
                Patcher.data_path, f'chromedriver_{version}.exe'
            )
            if isinstance(version, str) and len(version) > 0:
                version_main = int(version.split('.')[0])
            else:
                version_main = None
            params = {
                'options': driver_options,
                'user_data_dir': user_data_dir,
                'no_sandbox': False,
                'user_multi_procs': options.use_multi_procs,
                'version_main': version_main,
                'driver_executable_path': driver_executable_path if os.path.exists(driver_executable_path) else None,
            }
            if cls.use_seleniumwire(options):
                chrome = wire_uc.Chrome(seleniumwire_options=cls.default_seleniumwire_config(options),
                                        **params)
            else:
                chrome = uc.Chrome(**params)
            if not os.path.isfile(driver_executable_path):
                shutil.copyfile(chrome.patcher.executable_path, driver_executable_path)
            return chrome
        if cls.use_seleniumwire(options):
            return wire_webdriver.Chrome(options=driver_options, seleniumwire_options=cls.default_seleniumwire_config(options), service=service)
        return webdriver.Chrome(options=driver_options, service=service)

    def quit(self):
        if self.use_undetected_driver(self.options) and os.name == 'nt':
            os.system(f"taskkill /F /T /PID {self.driver.browser_pid} >NUL")
        super().quit()

    @classmethod
    def default_driver_manager(cls):
        """Default driver manager"""
        return ChromeDriverManager()
