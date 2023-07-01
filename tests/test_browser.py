import os

import pytest
from dotenv import load_dotenv
from selenium.webdriver import Firefox

from arbety_double_bot.browser import (
    get_signals,
    is_logged,
    make_login,
    to_bet,
)
from arbety_double_bot.driver import create_driver, find_element


@pytest.fixture(scope='module')
def driver() -> Firefox:
    return create_driver(visible=False)


def test_make_login(driver: Firefox) -> None:
    load_dotenv()
    make_login(driver, os.environ['EMAIL'], os.environ['PASSWORD'])
    assert is_logged(driver)


def test_get_signals(driver: Firefox) -> None:
    signals = get_signals(driver)
    assert len(signals) == 20


def test_to_bet(driver: Firefox) -> None:
    to_bet(driver, 1, 'r')
    to_bet(driver, 1, 'w')
    to_bet(driver, 1, 'g')
