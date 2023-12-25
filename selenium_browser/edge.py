"""Edge browser driver"""
from selenium import webdriver
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from seleniumwire import webdriver as wire_webdriver
from .chrome import ChromeBrowser


class EdgeBrowser(ChromeBrowser):
    """Edge browser"""

    @classmethod
    def driver_options(cls, options):
        driver_options = webdriver.EdgeOptions()
        return cls.config_driver_options(options, driver_options)

    @classmethod
    def driver_service(cls, driver_manager):
        """Driver service"""
        return webdriver.EdgeService(driver_manager.install())

    @classmethod
    def default_driver_manager(cls):
        """Default driver manager"""
        return EdgeChromiumDriverManager()

    @classmethod
    def new_driver(cls, options, driver_options, service):
        if cls.use_seleniumwire(options):
            return wire_webdriver.Edge(options=driver_options, service=service,
                                       seleniumwire_options=cls.default_seleniumwire_config(options))
        return webdriver.Edge(options=driver_options, service=service)
