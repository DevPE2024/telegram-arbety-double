from datetime import date
import asyncio
import json
import os
import prettytable as pt
import re
import threading

from dotenv import load_dotenv
from playwright.async_api import async_playwright
from pyrogram import Client, filters
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
    get_bets_from_user,
    get_strategies_from_user,
    get_user,
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


@app.on_message(filters.command(['start']))
async def start(client: Client, message: Message) -> None:
    await show_main_menu(message.chat.id)


@app.on_callback_query()
async def answer(client, callback_query):
    functions = {
        'token': generate_token,
        'login': login,
        'gale': configure_gale,
        'stop_bot': stop_bot,
        'start_bot': start_bot,
        'stop_loss': lambda m: configure_stop(m, 'loss'),
        'stop_win': lambda m: configure_stop(m, 'win'),
        'add': add_strategy,
        'remove': remove_strategy,
        'show': show_strategies,
    }
    if functions.get(callback_query.data):
        await functions[callback_query.data](callback_query.message)
    await show_main_menu(callback_query.message.chat.id)


async def show_main_menu(user_id: int) -> None:
    menu = [
        [
            InlineKeyboardButton('⚙️ Login', callback_data='login'),
        ],
        [
            InlineKeyboardButton('🔴 Parar bot', callback_data='stop_bot'),
            InlineKeyboardButton(
                '🟢 Iniciar bot', callback_data='start_bot'
            ),
        ],
        [
            InlineKeyboardButton('❌ Stop LOSS', callback_data='stop_loss'),
            InlineKeyboardButton('✅ Stop WIN', callback_data='stop_win'),
        ],
        [
            InlineKeyboardButton('👍🏻 Adicionar', callback_data='add'),
            InlineKeyboardButton('👎🏻 Remover', callback_data='remove'),
        ],
        [InlineKeyboardButton('Listar', callback_data='show')],
    ]
    if user_id in json.load(open('.config.json', 'r'))['admins']:
        menu.insert(
            0,
            [InlineKeyboardButton('Token', callback_data='token')]
        )
    await app.send_message(
        user_id,
        'Escolha uma opção',
        reply_markup=InlineKeyboardMarkup(menu),
    )


def login_required(function: callable) -> callable:
    async def decorator(*args, **kwargs):
        if get_user(args[0].chat.id):
            await function(*args, **kwargs)
        else:
            await args[0].reply('Primeiro faça o login')

    return decorator


def token_required(function: callable) -> callable:
    async def decorator(*args, **kwargs):
        token_message = await args[0].chat.ask('Digite o token')
        token = get_token(token_message.text)
        users_with_token = [u for u in get_users() if u.token == token.value]
        if (
            users_with_token
            and users_with_token[0].name != args[0].chat.username
        ):
            await token_message.reply('Token já está em uso')
        elif token and token.expiration_date > date.today():
            await function(*args, token=token.value)
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
    days = await message.chat.ask(
        'Digite a quantidade de dias de duração do Token'
    )
    token = create_token(int(days.text))
    await days.reply(token)


@token_required
async def login(message: Message, token: str = '') -> None:
    email = await message.chat.ask('Digite seu email:')
    password = await message.chat.ask('Digite sua senha:')
    login = await password.reply('Fazendo login...')
    async with async_playwright() as p:
        browser = await p.firefox.launch()
        context = await browser.new_context()
        page = await context.new_page()
        await make_login(page, email.text, password.text)
        if await is_logged(page):
            user = get_user(message.chat.id)
            if user:
                user.email = email.text
                user.password = password.text
                edit_user(user)
            else:
                user = User(
                    id=message.chat.id,
                    email=email.text,
                    password=password.text,
                    gale=0,
                    stop_loss=0,
                    stop_win=0,
                    is_betting=True,
                    token=token,
                )
                create_user(user)
            await login.edit_text('Login realizado')
            await context.storage_state(path=f'{message.chat.id}.json')
        else:
            await login.edit_text('Login inválido')
        await browser.close()


@number_validator
@login_required
async def configure_gale(message: Message) -> None:
    user = get_user(message.chat.username)
    edit_gale = await message.chat.ask(
        f'Seu gale atual é de {user.gale}, deseja alterar o gale? (s ou n)'
    )
    if edit_gale.text[0].lower() == 's':
        gale = await message.chat.ask(
            'Digite a quantidade de gale que deseja para suas apostas'
        )
        user.gale = int(gale.text)
        edit_user(user)
        await gale.reply('Gale configurado')


@login_required
async def stop_bot(message: Message) -> None:
    await message.reply('Parou o bot')
    user = get_user(message.chat.id)
    user.is_betting = False
    edit_user(user)


@login_required
async def start_bot(message: Message) -> None:
    await message.reply('Bot iniciado')
    user = get_user(message.chat.id)
    user.is_betting = True
    exists_thread = bool(
        [t for t in threading.enumerate() if t.name == user.id]
    )
    if not exists_thread:
        threading.Thread(
            name=str(user.id),
            target=run_signals,
            args=[user],
        ).start()
    edit_user(user)


@number_validator
@login_required
async def configure_stop(message: Message, for_result: str) -> None:
    user = get_user(message.chat.id)
    if for_result == 'win':
        edit_stop = await message.chat.ask(
            f'Seu Stop WIN atual é {user.stop_win}, deseja alterar? (s ou n)'
        )
    else:
        edit_stop = await message.chat.ask(
            f'Seu Stop LOSS atual é {user.stop_loss}, deseja alterar? (s ou n)'
        )
    if edit_stop.text[0].lower() == 's':
        stop_value_message = await message.chat.ask(
            (
                f'Digite o valor para o Stop {for_result.upper()}, '
                'exemplo: 50,00 ou 50'
            )
        )
        stop_value = float(stop_value_message.text.replace(',', '.'))
        if for_result == 'win':
            user.stop_win = stop_value
        else:
            user.stop_loss = -stop_value
        edit_user(user)
        await stop_value_message.reply(
            f'Stop {for_result.upper()} configurado'
        )


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
            user_id=message.chat.id,
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
    user = get_user(message.chat.id)
    if [
        s for s in get_strategies_from_user(user)
        if s.id == int(strategy_id.text)
    ]:
        remove_strategy_by_id(int(strategy_id.text))
        await message.reply('Estratégia removida')
    else:
        await message.reply('ID inválido')


@login_required
async def show_strategies(message: Message) -> None:
    table = pt.PrettyTable(['ID', 'Estratégia', 'Valor'])
    table.align['ID'] = 'l'
    table.align['Estratégia'] = 'c'
    table.align['Valor'] = 'l'
    user = get_user(message.chat.id)
    for strategy in get_strategies_from_user(user):
        table.add_row(
            [
                strategy.id,
                f'{strategy.strategy} = {strategy.bet_color}',
                f'R$ {strategy.value:.2f}'.replace('.', ','),
            ]
        )
    await message.reply(f'```\n{table}```')


def run_signals(user: User) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_signals_callback(user))
    loop.close()


async def run_signals_callback(user: User) -> None:
    await create_browser(user)


async def create_browser(user: User) -> callable:
    async with async_playwright() as p:
        browser = await p.firefox.launch()
        context = await browser.new_context(storage_state=f'{user.id}.json')
        page = await context.new_page()
        await page.goto('https://www.arbety.com/games/double')
        signals = await get_signals(page)
        while True:
            user = get_user(user.id)
            if not user.is_betting:
                break
            signals = await wait_for_new_signals(page, signals)
            for strategy in get_strategies_from_user(user):
                if re.compile(f'{strategy.strategy}$').findall(signals):
                    value = get_bet_value(strategy)
                    await to_bet(page, value, strategy.bet_color)
                    await send_bet_confirmation_message(strategy, value)
                    signals = await wait_for_new_signals(page, signals)
                    await send_result_message(strategy, value, signals)
                    exceeded_stop_loss = (
                        0 != user.stop_loss >= get_profit(user)
                    )
                    exceeded_stop_win = 0 != user.stop_win <= get_profit(user)
                    if exceeded_stop_loss or exceeded_stop_win:
                        user.is_betting = False
                        if exceeded_stop_loss:
                            await app.send_message(
                                user.id,
                                'Bot parou, Stop LOSS atingido',
                            )
                            user.stop_loss *= 2
                        elif exceeded_stop_win:
                            await app.send_message(
                                strategy.user.id,
                                'Bot parou, Stop WIN atingido',
                            )
                            user.stop_win *= 2
                        edit_user(user)
                        break
        await browser.close()


async def wait_for_new_signals(page, signals: str) -> str:
    while signals == await get_signals(page):
        await asyncio.sleep(1)
    return await get_signals(page)


def get_bet_value(strategy: Strategy) -> float:
    bets = get_bets_from_user(strategy.user)
    num_loss = get_number_of_loss(bets)
    if bets and bets[-1].value < 0 and num_loss <= strategy.user.gale:
        return abs(bets[-1].value * 2)
    return strategy.value


def get_number_of_loss(bets: list[Bet]) -> int:
    result = 0
    for bet in bets[::-1]:
        if bet.value < 0:
            result += 1
        else:
            break
    return result


async def send_bet_confirmation_message(
    strategy: Strategy, value: float
) -> None:
    message = (
        f'🔰 Entrada realizada 🔰\n💸 Valor: R$ {value:.2f}\n'
        f'🎯 Cor: {COLORS[strategy.bet_color]}'
    ).replace('.', ',')
    await app.send_message(strategy.user.id, message)


async def send_result_message(
    strategy: Strategy, value: float, signals: str
) -> None:
    result_regex = re.compile(
        f'{strategy.strategy} - {strategy.bet_color}$'
    )
    color_message = f'➡️ Cor: {COLORS[signals[-1]]}'
    bet = Bet(value=value, user_id=strategy.user.id)
    if result_regex.findall(signals):
        message = f'➡️ RESULTADO 💚 WIN 💚\n{color_message}'
    else:
        bet.value = -value
        message = f'➡️ RESULTADO ❌ LOSS ❌\n{color_message}'
    create_bet(bet)
    message += (
        f'\n💸 Lucro: R$ {get_profit(strategy.user):.2f}'.replace('.', ',')
    )
    await app.send_message(strategy.user.id, message)


def get_profit(user: User) -> float:
    return sum([b.value for b in get_bets_from_user(user)])


if __name__ == '__main__':
    app.run()
