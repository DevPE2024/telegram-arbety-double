import re
from threading import active_count, Thread

from dotenv import load_dotenv
from pyrogram.client import Client

from arbety_double_bot.browser import get_signals,  to_bet
from arbety_double_bot.constants import COLORS
from arbety_double_bot.domain import Strategy
from arbety_double_bot.driver import create_driver
from arbety_double_bot.repositories import get_strategies
from main import app


def send_result_message(app: Client, strategy: Strategy, signals: str) -> None:
    strategy_regex = re.compile(f'{strategy.strategy} - {strategy.bet_color}$')
    color_message = f'➡️ Cor: {COLORS[strategy.bet_color]}'
    if strategy_regex.findall(signals):
        message = f'➡️ RESULTADO 💚 WIN 💚\n{color_message}'
    else:
        message = f'➡️ RESULTADO ❌ LOSS ❌\n{color_message}'
    with app:
        app.send_message(strategy.user.name, message)


def send_bet_confirmation_message(app: Client, strategy: Strategy) -> None:
    message = (
        f'🔰 Entrada realizada 🔰\n💸 Valor: R$ {strategy.value}\n'
        f'🎯 Cor: {COLORS[strategy.bet_color]}'
    )
    with app:
        app.send_message(strategy.user.name, message)


def to_bet_thread() -> None:
    driver = create_driver()
    to_bet(driver, strategy.value, strategy.bet_color)
    driver.quit()


if __name__ == '__main__':
    load_dotenv()
    signals_driver = create_driver()
    signals = get_signals(signals_driver)
    while True:
        for strategy in get_strategies():
            if re.compile(f'{strategy.strategy}$').findall(signals):
                if active_count() < os.environ['MAX_BROWSERS']:
                    Thread(target=to_bet_thread).start()
                    send_bet_confirmation_message(app, strategy)
            if signals != get_signals(signals_driver):
                signals = get_signals(signals_driver)
                send_result_message(app, strategy, signals)
