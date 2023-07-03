from asyncio import create_task, gather, run
import re
from threading import Thread

from playwright.async_api import async_playwright
from pyrogram.client import Client

from arbety_double_bot.browser import get_signals, make_login, to_bet
from arbety_double_bot.constants import COLORS
from arbety_double_bot.domain import Strategy


class Subscriber:
    def __init__(self, app: Client, strategy: Strategy) -> None:
        self._app = app
        self._strategy = strategy
        self._wait = False

    async def notify(self, signals: str) -> None:
        strategy_pattern = re.compile(f'{self._strategy.strategy}$')
        if strategy_pattern.findall(signals) and not self._wait:
            await self.send_bet_confirmation_message()
            async with async_playwright() as p:
                browser = await p.firefox.launch()
                page = await browser.new_page()
                await make_login(
                    page,
                    self._strategy.user.email,
                    self._strategy.user.password,
                )
                await to_bet(
                    page,
                    self._strategy.value,
                    self._strategy.bet_color,
                )
                await browser.close()
            self._wait = True
        elif self._wait:
            await self.send_result_message(signals)
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

    def add_subscriber(self, subscriber: Subscriber) -> None:
        self._subscribers.append(subscriber)

    async def run(self) -> None:
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=False)
            page = await browser.new_page()
            self._signals = get_signals(page)
            while True:
                new_signals = await get_signals(page)
                if self._signals != new_signals:
                    self._signals = new_signals
                    await self.notify_subscribers()

    async def notify_subscribers(self) -> None:
        tasks = []
        for subscriber in self._subscribers:
            tasks.append(create_task(subscriber.notify(self._signals)))
        await gather(tasks)
