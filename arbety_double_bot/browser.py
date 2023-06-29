from selenium.webdriver import Firefox

from arbety_double_bot.common import click, find_element, find_elements
from arbety_double_bot.domain import Signal


def get_signals(driver: Firefox) -> list[Signal]:
    driver.get('https://www.arbety.com/games/double')
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


def make_login(driver: Firefox, email: str, password: str) -> None:
    driver.get('https://www.arbety.com/home?modal=login')
    find_element(driver, '#email').send_keys(email)
    find_element(driver, '#current-password').send_keys(password)
    click(driver, 'button.button-primary:not(.register)')
