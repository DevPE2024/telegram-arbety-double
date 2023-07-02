import re
from threading import Thread

from pyrogram.client import Client

from arbety_double_bot.browser import get_signals, make_login, to_bet
from arbety_double_bot.constants import COLORS
from arbety_double_bot.domain import Strategy
from arbety_double_bot.driver import create_driver


class Subscriber:
    def __init__(self, app: Client, strategy: Strategy) -> None:
        self._app = app
        self._strategy = strategy
        self._wait = False

    def notify(self, signals: str) -> None:
        strategy_pattern = re.compile(f'{self._strategy.strategy}$')
        if strategy_pattern.findall(signals) and not self._wait:
            self.send_bet_confirmation_message()
            driver = create_driver()
            print('Fazendo login')
            make_login(
                driver,
                self._strategy.user.email,
                self._strategy.user.password,
            )
            to_bet(driver, self._strategy.value, self._strategy.bet_color)
            print('Apostado')
            driver.quit()
            self._wait = True
        elif self._wait:
            self.send_result_message(signals)
            self._wait = False

    def send_bet_confirmation_message(self) -> None:
        message = (
            f'🔰 Entrada realizada 🔰\n💸 Valor: R$ {self._strategy.value}\n'
            f'🎯 Cor: {COLORS[self._strategy.bet_color]}'
        )
        self._app.send_message(self._strategy.user.name, message)

    def send_result_message(self, signals: str) -> None:
        result_regex = re.compile(
            f'{self._strategy.strategy} - {self._strategy.bet_color}$'
        )
        color_message = f'➡️ Cor: {COLORS[signals[-1]]}'
        if result_regex.findall(signals):
            message = f'➡️ RESULTADO 💚 WIN 💚\n{color_message}'
        else:
            message = f'➡️ RESULTADO ❌ LOSS ❌\n{color_message}'
        self._app.send_message(self._strategy.user.name, message)


class SignalsObserver:
    def __init__(self) -> None:
        self._subscribers = []
        self._driver = create_driver()
        self._signals = get_signals(self._driver)

    def add_subscriber(self, subscriber: Subscriber) -> None:
        self._subscribers.append(subscriber)

    def run(self) -> None:
        while True:
            new_signals = get_signals(self._driver)
            if self._signals != new_signals:
                self._signals = new_signals
                self.notify_subscribers()

    def notify_subscribers(self) -> None:
        print(self._signals)
        for subscriber in self._subscribers:
            Thread(target=subscriber.notify, args=[self._signals]).start()
