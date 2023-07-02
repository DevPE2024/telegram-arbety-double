import re

from pyrogram.client import Client

from arbety_double_bot.browser import get_signals, to_bet
from arbety_double_bot.constants import COLORS
from arbety_double_bot.domain import Strategy, User
from arbety_double_bot.driver import create_driver
from arbety_double_bot.repositories import get_strategies_from_user


class Subscriber:
    def __init__(self, app: Client, user: User) -> None:
        self._app = app
        self._user = user
        self._wait_result = False

    def notify(self, signals: str) -> None:
        for strategy in get_strategies_from_user(self._user):
            strategy_pattern = re.compile(f'{strategy.strategy}$')
            if strategy_pattern.findall(signals) and not self._wait_result:
                driver = create_driver()
                to_bet(driver, strategy.value, strategy.bet_color)
                driver.quit()
                self.send_bet_confirmation_message(strategy)
                self._wait_result = True
            elif self._wait_result:
                self.send_result_message(strategy, signals)
                self._wait_result = False

    def send_result_message(self, strategy: Strategy, signals: str) -> None:
        result_regex = re.compile(
            f'{strategy.strategy} - {strategy.bet_color}$'
        )
        color_message = f'➡️ Cor: {COLORS[signals[-1]]}'
        if result_regex.findall(signals):
            message = f'➡️ RESULTADO 💚 WIN 💚\n{color_message}'
        else:
            message = f'➡️ RESULTADO ❌ LOSS ❌\n{color_message}'
        self._app.send_message(strategy.user.name, message)

    def send_bet_confirmation_message(self, strategy: Strategy) -> None:
        message = (
            f'🔰 Entrada realizada 🔰\n💸 Valor: R$ {strategy.value}\n'
            f'🎯 Cor: {COLORS[strategy.bet_color]}'
        )
        self._app.send_message(strategy.user.name, message)


class SignalsObserver:
    def __init__(self) -> None:
        self._subscribers = []
        self._driver = create_driver()
        self._signals = get_signals(self._driver)

    def run(self) -> None:
        while True:
            new_signals = get_signals(self._driver)
            if self._signals != new_signals:
                self._signals = new_signals
                self.notify_subscribers()

    def add_subscriber(self, subscriber: Subscriber) -> None:
        self._subscribers.append(subscriber)

    def notify_subscribers(self) -> None:
        for subscriber in self._subscribers:
            subscriber.notify(self._signals)
