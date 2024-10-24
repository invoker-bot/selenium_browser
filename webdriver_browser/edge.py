"""Edge browser driver"""
from selenium import webdriver
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from seleniumwire import webdriver as wire_webdriver
from .chrome import ChromeBrowser, BrowserOptions
from .download import get_wdm_download_manager


__all__ = ['BrowserOptions', 'EdgeBrowser']


class EdgeBrowser(ChromeBrowser):
    """Edge browser"""
    browser_names = {'edge', 'msedge', 'microsoftedge', 'ms-edge', 'microsoft-edge'}

    def _driver_options(self):
        driver_options = webdriver.EdgeOptions()
        return self._config_driver_options(driver_options)

    def _driver_service(self, driver_manager):
        """Driver service"""
        return webdriver.EdgeService(driver_manager.install())

    def _default_driver_manager(self):
        """Default driver manager"""
        return EdgeChromiumDriverManager(download_manager=get_wdm_download_manager(self.options.proxy_downloader))

    def _new_driver(self, driver_options, service):
        if self._use_seleniumwire():
            return wire_webdriver.Edge(options=driver_options, service=service,
                                       seleniumwire_options=self._default_seleniumwire_config())
        return webdriver.Edge(options=driver_options, service=service)
