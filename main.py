from datetime import date
import asyncio
import os
import re
import threading

from dotenv import load_dotenv
from playwright.async_api import async_playwright
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyromod import listen

from arbety_double_bot.browser import (
    is_logged,
    get_signals,
    make_login,
    to_bet,
)
from arbety_double_bot.constants import COLORS
from arbety_double_bot.domain import Bet, Strategy, User
from arbety_double_bot.repositories import (
    create_bet,
    create_strategy,
    create_user,
    create_token,
    edit_user,
    get_bets_from_strategy,
    get_strategies_from_users,
    get_user_by_name,
    get_users,
    get_token,
    remove_strategy_by_id,
)


app = Client(
    os.environ['BOT_NAME'],
    api_id=os.environ['API_ID'],
    api_hash=os.environ['API_HASH'],
    bot_token=os.environ['BOT_TOKEN'],
)

load_dotenv()
users = get_users()


@app.on_message(filters.command(['start']))
async def start(client: Client, message: Message) -> None:
    await show_main_menu(message.chat.username)


@app.on_callback_query()
async def answer(client, callback_query):
    functions = {
        'token': generate_token,
        'login': login,
        'gale': configure_gale,
        'stop_betting': stop_betting,
        'continue_betting': continue_betting,
        'stop_loss': lambda m: configure_stop(m, 'loss'),
        'stop_win': lambda m: configure_stop(m, 'win'),
        'add': add_strategy,
        'remove': remove_strategy,
        'show': show_strategies,
    }
    if functions.get(callback_query.data):
        await functions[callback_query.data](callback_query.message)
    await show_main_menu(callback_query.message.chat.username)


async def show_main_menu(username: str) -> None:
    menu = [
        [
            InlineKeyboardButton('Login', callback_data='login'),
            InlineKeyboardButton('Gale', callback_data='gale'),
        ],
        [
            InlineKeyboardButton(
                'Parar apostas', callback_data='stop_betting'
            ),
            InlineKeyboardButton(
                'Retomar apostas', callback_data='continue_betting'
            ),
        ],
        [
            InlineKeyboardButton('Stop LOSS', callback_data='stop_loss'),
            InlineKeyboardButton('Stop WIN', callback_data='stop_win'),
        ],
        [
            InlineKeyboardButton('Adicionar', callback_data='add'),
            InlineKeyboardButton('Remover', callback_data='remove'),
        ],
        [InlineKeyboardButton('Listar', callback_data='show')],
    ]
    if username == os.environ['USERNAME']:
        menu.insert(
            0,
            [InlineKeyboardButton('Token', callback_data='token')]
        )
    await app.send_message(
        username,
        'Escolha uma opção',
        reply_markup=InlineKeyboardMarkup(menu),
    )


def login_required(function: callable) -> callable:
    async def decorator(*args, **kwargs):
        if get_user_by_name(args[0].chat.username):
            await function(*args, **kwargs)
        else:
            await args[0].reply('Primeiro faça o login')

    return decorator


def token_required(function: callable) -> callable:
    async def decorator(*args, **kwargs):
        token_message = await args[0].chat.ask('Digite o token')
        token = get_token(token_message.text)
        if token and token.expiration_date > date.today():
            await function(*args, **kwargs)
        else:
            await token_message.reply('Token inválido ou expirado')

    return decorator


def number_validator(function: callable) -> callable:
    async def decorator(*args, **kwargs):
        try:
            await function(*args, **kwargs)
        except ValueError:
            await args[0].reply('Digite apenas números')

    return decorator


@number_validator
async def generate_token(message: Message) -> None:
    if message.chat.username == os.environ['USERNAME']:
        days = await message.chat.ask(
            'Digite a quantidade de dias de duração do Token'
        )
        token = create_token(int(days.text))
        await days.reply(token)


@token_required
async def login(message: Message) -> None:
    email = await message.chat.ask('Digite seu email:')
    password = await message.chat.ask('Digite sua senha:')
    login = await password.reply('Fazendo login...')
    async with async_playwright() as p:
        browser = await p.firefox.launch()
        context = await browser.new_context()
        page = await context.new_page()
        await make_login(page, email.text, password.text)
        if await is_logged(page):
            user = get_user_by_name(message.chat.username)
            if user:
                user.email = email.text
                user.password = password.text
                edit_user(user)
            else:
                user = User(
                    name=message.chat.username,
                    email=email.text,
                    password=password.text,
                    gale=0,
                    stop_loss=0,
                    stop_win=0,
                )
                create_user(user)
            await login.edit_text('Login realizado')
            await context.storage_state(
                path=f'{message.chat.username}.json'
            )
            threading.Thread(target=run_signals, args=(users)).start()
        else:
            await login.edit_text('Login inválido')
        await browser.close()


@number_validator
@login_required
async def configure_gale(message: Message) -> None:
    gale = await message.chat.ask(
        'Digite a quantidade de gale que deseja para suas apostas'
    )
    user = get_user_by_name(message.chat.username)
    user.gale = int(gale.text)
    edit_user(user)


@login_required
async def stop_betting(message: Message) -> None:
    await message.reply('Parou com as apostas')
    users.remove(get_user_by_name(message.chat.username))
    threading.Thread(target=run_signals, args=(users)).start()


@login_required
async def continue_betting(message: Message) -> None:
    await message.reply('Retomando apostas')
    threading.Thread(
        target=run_signals,
        args=([users, get_user_by_name(message.chat.username)])
    ).start()


@number_validator
@login_required
async def configure_stop(message: Message, for_result: str) -> None:
    stop_value_message = await message.chat.ask(
        (
            f'Digite o valor para o Stop {for_result.upper()}, '
            'exemplo: 50,00 ou 50'
        )
    )
    user = get_user_by_name(message.chat.username)
    stop_value = float(stop_value_message.text.replace(',', '.'))
    if for_result == 'win':
        user.stop_win = stop_value
    else:
        user.stop_loss = -stop_value
    edit_user(user)


@number_validator
@login_required
async def add_strategy(message: Message) -> None:
    strategy = await message.chat.ask(
        (
            'Digite sua estratégia utilizando r (red), g (green) e w '
            '(white), exemplo: r - r - g = r\nNesse exemplo sempre que '
            'der essa sequência ele vai apostar no vermelho:'
        ),
    )
    value = await message.chat.ask(
        'Digite o valor para a aposta, exemplo: 50 ou 50,00'
    )
    if re.compile(r'[rwg]( - [rwg])+ = [rwg]').findall(strategy.text):
        await strategy.reply('Estratégia adicionada')
        strategy_text, bet_color = strategy.text.split(' = ')
        strategy = Strategy(
            user_id=get_user_by_name(message.chat.username).id,
            strategy=strategy_text,
            bet_color=bet_color,
            value=float(value.text.replace(',', '.')),
        )
        create_strategy(strategy)
    else:
        await strategy.reply('Estratégia definida incorretamente')


@number_validator
@login_required
async def remove_strategy(message: Message) -> None:
    strategy_id = await message.chat.ask('Digite o ID da estrátegia:')
    remove_strategy_by_id(int(strategy_id.text))
    await message.reply('Estratégia removida')


@login_required
async def show_strategies(message: Message) -> None:
    text_format = '{:<4}{:<18}{:<4}{}\n'
    text = 'ID Estratégia Cor Valor\n'
    user = get_user_by_name(message.chat.username)
    for strategy in get_strategies_from_users([user]):
        text += text_format.format(
            strategy.id,
            strategy.strategy,
            strategy.bet_color,
            strategy.value,
        )
    await message.reply(text)


async def run_signals_callback(users: list[User]) -> None:
    async with async_playwright() as p:
        browser = await p.firefox.launch()
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto('https://www.arbety.com/games/double')
        signals = get_signals(page)
        while True:
            signals = await wait_for_new_signals(page, signals)
            for strategy in get_strategies_from_users(users):
                strategy_pattern = re.compile(r'.+( - [rwg] = [rwg])')
                strategy_text = strategy_pattern.sub('', strategy.strategy)
                if signals[-len(strategy_text) :] == strategy_text:
                    await create_browser(strategy, signals)


def run_signals(users: list[User]) -> None:
    print(threading.enumerate())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_signals_callback(users))
    loop.close()


async def create_browser(strategy: Strategy, signals: str) -> callable:
    async with async_playwright() as p:
        browser = await p.firefox.launch()
        context = await browser.new_context(
            storage_state=f'{strategy.user.name}.json'
        )
        page = await context.new_page()
        await page.goto('https://www.arbety.com/games/double')
        signals = await wait_for_new_signals(page, signals)
        if re.compile(f'{strategy.strategy}$').findall(signals):
            value = get_bet_value(strategy)
            await to_bet(page, value, strategy.bet_color)
            await send_bet_confirmation_message(strategy, value)
            signals = await wait_for_new_signals(page, signals)
            await send_result_message(strategy, value, signals)
            if exceeded_stop_win_or_loss(strategy):
                users.remove(strategy.user)
                threading.Thread(target=run_signals, args=(users)).start()
        await browser.close()


async def wait_for_new_signals(page, signals: str) -> str:
    while signals == await get_signals(page):
        await asyncio.sleep(1)
    return await get_signals(page)


def get_bet_value(strategy: Strategy) -> float:
    num_loss = get_number_of_loss(strategy)
    if strategy.user.gale > num_loss > 0:
        return strategy.value + strategy.value * num_loss
    return strategy.value


def get_number_of_loss(strategy: Strategy) -> int:
    result = 0
    for bet in get_bets_from_strategy(strategy)[::-1]:
        if bet.result < 0:
            result += 1
        else:
            break
    return result


async def send_bet_confirmation_message(
    strategy: Strategy, value: float
) -> None:
    message = (
        f'🔰 Entrada realizada 🔰\n💸 Valor: R$ {value}\n'
        f'🎯 Cor: {COLORS[strategy.bet_color]}'
    )
    await app.send_message(strategy.user.name, message)


async def send_result_message(
    strategy: Strategy, value: float, signals: str
) -> None:
    result_regex = re.compile(
        f'{strategy.strategy} - {strategy.bet_color}$'
    )
    color_message = f'➡️ Cor: {COLORS[signals[-1]]}'
    bet = Bet(value=value, strategy_id=strategy.id)
    if result_regex.findall(signals):
        message = f'➡️ RESULTADO 💚 WIN 💚\n{color_message}'
    else:
        bet.value = -value
        message = f'➡️ RESULTADO ❌ LOSS ❌\n{color_message}'
    create_bet(bet)
    await app.send_message(strategy.user.name, message)


def exceeded_stop_win_or_loss(strategy: Strategy) -> bool:
    user = strategy.user
    return user.stop_loss < get_profit() or user.stop_win < get_profit()


def get_profit(strategy: Strategy) -> float:
    return sum([b.value for b in get_bets_from_strategy(strategy)])


if __name__ == '__main__':
    app.start()
    if users:
        threading.Thread(target=run_signals, args=(users)).start()
    idle()
    app.stop()
