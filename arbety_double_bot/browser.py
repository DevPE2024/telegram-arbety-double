from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Firefox

from arbety_double_bot.domain import Strategy
from arbety_double_bot.driver import (
    click,
    go_to_url,
    find_element,
    find_elements,
)


def get_signals(driver: Firefox) -> str:
    go_to_url(driver, 'https://www.arbety.com/games/double')
    result = []
    for e in range(20):
        signals = find_elements(driver, '.item')
        result.append(signals[e].get_attribute('class').split()[-1][0])
    return ' - '.join(result)


def to_bet(driver: Firefox, strategy: Strategy) -> None:
    go_to_url(driver, 'https://www.arbety.com/games/double')
    find_element(driver, '#betValue').send_keys(str(strategy.value))
    click(driver, f'.ball-{strategy.bet_color}')
    click(driver, '.button-primary')


def make_login(driver: Firefox, user: User) -> None:
    go_to_url(driver, 'https://www.arbety.com/home?modal=login')
    find_element(driver, '#email').send_keys(user.email)
    find_element(driver, '#current-password').send_keys(user.password)
    click(driver, 'button.button-primary:not(.register)')


def is_logged(driver: Firefox) -> bool:
    try:
        find_element(driver, '.user-name')
        return True
    except TimeoutException:
        return False
