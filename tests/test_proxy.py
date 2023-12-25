# pylint: disable=missing-function-docstring
"""Test proxy."""
import os
import shutil
from multiprocessing import Process
from urllib.parse import urlparse
import pytest
from pproxy.server import main as pproxy_main
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium_browser import BrowserOptions
from selenium_browser.chrome import ChromeBrowser
from selenium_browser.edge import EdgeBrowser
from selenium_browser.firefox import FirefoxBrowser


@pytest.fixture(scope="module", params=[None, 'http://localhost:9999', 'http://user:password@localhost:10000'])
def proxy_server(request):
    if request.param is None:
        yield None
        return
    url = request.param
    result = urlparse(url)
    pproxy_format = f'{result.scheme}://:{result.port}/'
    if result.username:
        pproxy_format += f'#{result.username}:{result.password}'
    proxy_process = Process(target=pproxy_main, args=(['-l', pproxy_format], ), daemon=True)
    proxy_process.start()
    yield url
    proxy_process.terminate()
    proxy_process.join(15)


def valid_browsers():
    if os.getenv('BROWSER'):
        return [{'chrome': ChromeBrowser, 'firefox': FirefoxBrowser, 'edge': EdgeBrowser}[os.getenv('BROWSER')]]
    return [ChromeBrowser]


@pytest.mark.xfail(reason="network is not available occasionally")
@pytest.mark.parametrize('browser_cls', valid_browsers())
def test_proxy(proxy_server, browser_cls):  # pylint: disable=redefined-outer-name
    # print(f"Testing with proxy server at: {proxy_server}")
    assert proxy_server is None or urlparse(proxy_server).scheme in ('http', 'https')
    options = BrowserOptions(headless=True, proxy_server=proxy_server)
    browser = browser_cls(options)
    browser.driver.get("https://example.org/")
    browser.wait.until(EC.visibility_of_element_located((By.TAG_NAME, 'h1')))
    assert browser.driver.title == 'Example Domain'
    assert browser.driver.find_element(By.TAG_NAME, 'h1').text == 'Example Domain'
    browser.quit()


@pytest.mark.parametrize('browser_cls', valid_browsers())
def test_data_dir(browser_cls):
    options = BrowserOptions(headless=True, data_dir='test')
    browser = browser_cls(options)
    # browser.driver.get("https://example.org/")
    # backup_dir = browser_cls.get_data_dir('test_backup')
    # if os.path.exists(backup_dir):
    #    shutil.rmtree(backup_dir)
    # shutil.copytree(browser.data_dir, backup_dir, symlinks=True)
    browser.quit()
    # browser = browser_cls(options, 0)
