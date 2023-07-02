import os
import re
from threading import Thread, active_count
from time import sleep

from dotenv import load_dotenv
from pyrogram.client import Client

from arbety_double_bot.app import create_app
from arbety_double_bot.browser import get_signals, to_bet
from arbety_double_bot.constants import COLORS
from arbety_double_bot.domain import Strategy
from arbety_double_bot.driver import create_driver
from arbety_double_bot.repositories import get_strategies


def send_result_message(app: Client, strategy: Strategy, signals: str) -> None:
    strategy_regex = re.compile(f'{strategy.strategy} - {strategy.bet_color}$')
    color_message = f'➡️ Cor: {COLORS[signals[-1]]}'
    print(color_message)
    print(signals)
    if strategy_regex.findall(signals):
        message = f'➡️ RESULTADO 💚 WIN 💚\n{color_message}'
    else:
        message = f'➡️ RESULTADO ❌ LOSS ❌\n{color_message}'
    app.send_message(strategy.user.name, message)


def send_bet_confirmation_message(app: Client, strategy: Strategy) -> None:
    message = (
        f'🔰 Entrada realizada 🔰\n💸 Valor: R$ {strategy.value}\n'
        f'🎯 Cor: {COLORS[strategy.bet_color]}'
    )
    app.send_message(strategy.user.name, message)


def to_bet_thread(strategy: Strategy) -> None:
    driver = create_driver()
    to_bet(driver, strategy.value, strategy.bet_color)
    driver.quit()


def run_bot(app: Client) -> None:
    load_dotenv()
    signals_driver = create_driver()
    signals = get_signals(signals_driver)
    while True:
        for strategy in get_strategies():
            if signals != get_signals(signals_driver):
                signals = get_signals(signals_driver)
                if re.compile(f'{strategy.strategy}$').findall(signals):
                    Thread(target=to_bet_thread, args=[strategy]).start()
                    send_bet_confirmation_message(app, strategy)
                    while signals == get_signals(signals_driver):
                        sleep(1)
                    signals = get_signals(signals_driver)
                    send_result_message(app, strategy, signals)


app = create_app()
Thread(target=run_bot, args=[app]).start()
app.run()
