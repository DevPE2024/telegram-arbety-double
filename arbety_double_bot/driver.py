from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager


def create_driver(visible: bool = False) -> Firefox:
    options = Options()
    if not visible:
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
    return Firefox(
        options=options, service=Service(GeckoDriverManager().install())
    )


def click(driver: Firefox, selector: str, element=None) -> None:
    if element is None:
        element = driver
    driver.execute_script(
        'arguments[0].click();',
        find_element(element, selector),
    )


def go_to_url(driver: Firefox, url: str) -> None:
    if not url == driver.current_url:
        driver.get(url)


def find_element(element, selector: str, wait: int = 30):
    return WebDriverWait(element, wait).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )


def find_elements(element, selector: str, wait: int = 30):
    return WebDriverWait(element, wait).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
    )
