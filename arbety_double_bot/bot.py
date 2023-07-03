import re

from playwright.async_api import async_playwright
from pyrogram.client import Client

from arbety_double_bot.browser import get_signals, make_login, to_bet
from arbety_double_bot.constants import COLORS
from arbety_double_bot.domain import Strategy, User
from arbety_double_bot.repositories import get_strategies_from_user


async def create_browser(app: Client, user: User) -> callable:
    async with async_playwright() as p:
        browser = await p.firefox.launch()
        context = await browser.new_context()
        page = await context.new_page()
        await make_login(page, user.email, user.password)
        await page.goto('https://www.arbety.com/games/double')
        waits = [False for _ in get_strategies_from_user(user)]
        signals = await get_signals(page)
        while True:
            new_signals = await get_signals(page)
            if signals != new_signals:
                signals = new_signals
                if len(waits) < len(get_strategies_from_user(user)):
                    waits = [False for _ in get_strategies_from_user(user)]
                for e, strategy in enumerate(get_strategies_from_user(user)):
                    strategy_pattern = re.compile(f'{strategy.strategy}$')
                    print(waits)
                    print(waits[e])
                    try:
                        if strategy_pattern.findall(signals) and not waits[e]:
                            await to_bet(page, strategy.value, strategy.bet_color)
                            await send_bet_confirmation_message(app, strategy)
                            waits[e] = True
                        elif waits[e]:
                            await send_result_message(app, strategy, signals)
                            waits[e] = False
                    except IndexError:
                        waits.append(False)


async def send_bet_confirmation_message(
    app: Client, strategy: Strategy
) -> None:
    message = (
        f'🔰 Entrada realizada 🔰\n💸 Valor: R$ {strategy.value}\n'
        f'🎯 Cor: {COLORS[strategy.bet_color]}'
    )
    await app.send_message(strategy.user.name, message)


async def send_result_message(
    app: Client, strategy: Strategy, signals: str
) -> None:
    result_regex = re.compile(f'{strategy.strategy} - {strategy.bet_color}$')
    color_message = f'➡️ Cor: {COLORS[signals[-1]]}'
    if result_regex.findall(signals):
        message = f'➡️ RESULTADO 💚 WIN 💚\n{color_message}'
    else:
        message = f'➡️ RESULTADO ❌ LOSS ❌\n{color_message}'
    await app.send_message(strategy.user.name, message)
