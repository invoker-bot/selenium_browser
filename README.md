# selenium_browser
More convenient methods for creating multiple selenium browsers.

## Example

```shell
pip install webdriver_browser
```

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