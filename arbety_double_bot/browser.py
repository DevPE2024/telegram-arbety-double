from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver import Firefox

from arbety_double_bot.driver import (
    click,
    find_element,
    find_elements,
    go_to_url,
)


def get_signals(driver: Firefox) -> str:
    go_to_url(driver, 'https://www.arbety.com/games/double')
    try:
        return ' - '.join(
            [
                s.get_attribute('class').split()[-1][0]
                for s in find_elements(driver, '.item')
            ]
        )
    except StaleElementReferenceException:
        get_signals(driver)


def to_bet(driver: Firefox, value: float, bet_color: str) -> None:
    go_to_url(driver, 'https://www.arbety.com/games/double')
    find_element(driver, '#betValue').send_keys(str(value))
    bet_color = (
        'red' if bet_color == 'r' else 'green' if bet_color == 'g' else 'white'
    )
    click(driver, f'.ball-{bet_color}')
    click(driver, '.button-primary')


def make_login(driver: Firefox, email: str, password: str) -> None:
    go_to_url(driver, 'https://www.arbety.com/home?modal=login')
    find_element(driver, '#email').send_keys(email)
    find_element(driver, '#current-password').send_keys(password)
    click(driver, 'button.button-primary:not(.register)')


def is_logged(driver: Firefox) -> bool:
    try:
        find_element(driver, '.user-name')
        return True
    except TimeoutException:
        return False
