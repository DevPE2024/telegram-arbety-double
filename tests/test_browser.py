import os

import pytest
from dotenv import load_dotenv
from selenium.webdriver import Firefox

from arbety_double_bot.browser import get_signals, make_login
from arbety_double_bot.common import create_driver, find_element


@pytest.fixture(scope='module')
def driver() -> Firefox:
    return create_driver(visible=True)


def test_make_login(driver: Firefox) -> None:
    load_dotenv()
    make_login(driver, os.environ['EMAIL'], os.environ['PASSWORD'])
    find_element(driver, '.user-name')


def test_get_signals(driver: Firefox) -> None:
    signals = get_signals(driver)
    assert len(signals) == 20
