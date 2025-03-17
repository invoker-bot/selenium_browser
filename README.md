# selenium_browser

A Python library that provides more convenient methods for creating and managing multiple Selenium browsers.

## Features

- Easy browser management with context managers
- Support for Chrome, Firefox, and Edge browsers
- Built-in waiting mechanisms for elements
- Proxy configuration support
- Browser profile and extension management
- Headless mode support
- Retry mechanisms for common operations
- Integration with webdriver-manager for automatic driver installation

## Installation

```shell
pip install webdriver_browser
```

## Usage Examples

### Basic Usage with Chrome

```python
from webdriver_browser import BrowserOptions
from webdriver_browser.chrome import ChromeBrowser
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

with ChromeBrowser(BrowserOptions) as browser:
    browser.driver.get("https://example.org/")
    browser.wait.until(EC.visibility_of_element_located((By.TAG_NAME, 'h1')))
    assert browser.driver.title == 'Example Domain'
```

### Using Firefox with Custom Options

```python
from webdriver_browser import BrowserOptions
from webdriver_browser.firefox import FirefoxBrowser

options = BrowserOptions(
    headless=True,
    proxy_server="http://your-proxy-server:port",
    wait_timeout=10.0
)

with FirefoxBrowser(options) as browser:
    browser.driver.get("https://example.org/")
    # Your automation code here
```

### Using Edge Browser

```python
from webdriver_browser import BrowserOptions
from webdriver_browser.edge import EdgeBrowser

with EdgeBrowser(BrowserOptions) as browser:
    browser.driver.get("https://example.org/")
    # Your automation code here
```

### Using Convenience Methods

```python
from webdriver_browser import BrowserOptions
from webdriver_browser.chrome import ChromeBrowser
from selenium.webdriver.common.by import By

with ChromeBrowser(BrowserOptions) as browser:
    browser.driver.get("https://example.org/")
    
    # Click an element with automatic retry
    browser.click((By.ID, "submit-button"))
    
    # Input text with automatic retry
    browser.input((By.NAME, "search"), "search term")
    
    # Scroll element into view
    browser.scroll_to_view((By.CLASS_NAME, "footer"))
```

## License

This project is licensed under the terms of the license included in the repository.