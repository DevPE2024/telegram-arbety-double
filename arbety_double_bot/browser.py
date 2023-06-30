from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Firefox

from arbety_double_bot.common import click, find_element, find_elements
from arbety_double_bot.domain import Signal


def get_signals(driver: Firefox) -> list[Signal]:
    url = 'https://www.arbety.com/games/double'
    if driver.current_url != url:
        driver.get(url)
    result = []
    for e in range(20):
        signals = find_elements(driver, '.item')
        result.append(
            Signal(
                value=int(signals[e].get_attribute('textContent')),
                color=signals[e].get_attribute('class').split()[-1],
            )
        )
    return result


def to_bet(driver: Firefox, value: float, color: str) -> None:
    url = 'https://www.arbety.com/games/double'
    if driver.current_url != url:
        driver.get(url)
    find_element(driver, '#betValue').send_keys(str(value))
    click(driver, f'.ball-{color.lower()}')
    click(driver, '.button-primary')


def make_login(driver: Firefox, email: str, password: str) -> None:
    url = 'https://www.arbety.com/home?modal=login'
    if driver.current_url != url:
        driver.get(url)
    find_element(driver, '#email').send_keys(email)
    find_element(driver, '#current-password').send_keys(password)
    click(driver, 'button.button-primary:not(.register)')


def is_logged(driver: Firefox) -> bool:
    try:
        find_element(driver, '.user-name')
        return True
    except TimeoutException:
        return False
