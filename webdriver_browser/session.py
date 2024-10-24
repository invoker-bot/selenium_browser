"""This module contains the Session class.
"""
import requestium


class Sessionium(requestium.Session):
    """A subclass of the requestium.Session class.
    """
    def __init__(self, *args, driver_creater, **kwargs):
        super().__init__(*args, **kwargs)
        self._args = args
        self._kwargs = kwargs
        self._driver_creater = driver_creater
        self._driver_initializer = self._start_chrome_browser

    def _start_chrome_browser(self, headless=False):
        if self._driver is None:
            driver = self._driver_creater()
            self._kwargs['driver'] = driver
            super().__init__(*self._args, **self._kwargs)
        return self._driver
