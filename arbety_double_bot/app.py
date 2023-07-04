import os
import re

from dotenv import load_dotenv
from playwright.async_api import async_playwright
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyromod import listen

from arbety_double_bot.browser import is_logged, make_login
from arbety_double_bot.repositories import (
    create_bet,
    create_strategy,
    create_user,
    edit_user,
    get_bets_from_strategy,
    get_strategies_from_user,
    get_users,
    get_user_by_name,
    remove_strategy_by_id,
)


async def main(users: list[User] = get_users()) -> Client:
    load_dotenv()
    app = Client(
        os.environ['BOT_NAME'],
        api_id=os.environ['API_ID'],
        api_hash=os.environ['API_HASH'],
        bot_token=os.environ['BOT_TOKEN'],
    )

    @app.on_message(filters.command(['start', 'help']))
    async def start(client: Client, message: Message) -> None:
        await show_main_menu(message.chat.id)

    @app.on_callback_query()
    async def answer(client, callback_query):
        functions = {
            'login': login,
            'gale': configure_gale,
            'stop_loss': configure_stop_loss,
            'stop_win': configure_stop_win,
            'add': add_strategy,
            'remove': remove_strategy,
            'show': show_strategies,
        }
        if functions.get(callback_query.data):
            await functions[callback_query.data](
                client,
                callback_query.message,
            )
        await show_main_menu(callback_query.message.chat.id)

    async def show_main_menu(chat_id: int) -> None:
        menu = [
            [
                InlineKeyboardButton('Login', callback_data='login'),
                InlineKeyboardButton('Gale', callback_data='gale')
            ],
            [
                InlineKeyboardButton('Stop LOSS', callback_data='stop_loss'),
                InlineKeyboardButton('Stop WIN', callback_data='stop_win')
            ],
            [
                InlineKeyboardButton('Adicionar', callback_data='add'),
                InlineKeyboardButton('Remover', callback_data='remove')
            ],
            [InlineKeyboardButton('Listar', callback_data='show')],
        ]
        await app.send_message(
            chat_id,
            'Escolha uma opção',
            reply_markup=InlineKeyboardMarkup(menu),
        )

    def login_required(function: callable) -> callable:
        async def decorator(*args, **kwargs):
            if get_user_by_name(args[1].chat.username):
                await function(args, kwargs)
            else:
                await args[1].reply('Primeiro faça o login')

        return decorator

    async def login(client: Client, message: Message) -> None:
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
                await main()
            else:
                await login.edit_text('Login inválido')
            await browser.close()

    @login_required
    async def configure_gale(client: Client, message: Message) -> None:
        gale = await message.chat.ask(
            'Digite a quantidade de gale que deseja para suas apostas'
        )
        try:
            user = get_user_by_name(message.chat.username)
            user.gale = int(gale.text)
            edit_user(user)
        except ValueError:
            await message.reply('Digite apenas números para configurar o gale')

    @login_required
    async def configure_stop_loss(client: Client, message: Message) -> None:
        stop_loss = await message.chat.ask(
            'Digite o valor para o Stop LOSS, exemplo: 50,00 ou 50'
        )
        try:
            user = get_user_by_name(message.chat.username)
            user.stop_loss = float(stop_loss.replace(',', '.'))
            edit_user(user)
        except ValueError:
            await message.reply(
                'Digite apenas números para configurar o Stop LOSS'
            )

    @login_required
    async def configure_stop_win(client: Client, message: Message) -> None:
        stop_win = await message.chat.ask(
            'Digite o valor para o Stop WIN, exemplo: 50,00 ou 50'
        )
        try:
            user = get_user_by_name(message.chat.username)
            user.stop_win = float(stop_win.replace(',', '.'))
            edit_user(user)
        except ValueError:
            await message.reply(
                'Digite apenas números para configurar o Stop WIN'
            )

    @login_required
    async def add_strategy(client: Client, message: Message) -> None:
        strategy = await message.chat.ask(
            (
                'Digite sua estratégia utilizando r (red), g (green) e w '
                '(white), exemplo: r - r - g = r\nNesse exemplo sempre que '
                'der essa sequência ele vai apostar no vermelho:'
            ),
        )
        value = await message.chat.ask(
            'Digite o valor para a aposta, exemplo: 50 ou 50,00:'
        )
        try:
            strategy_regex = re.compile(r'[rwg]( - [rwg])+ = [rwg]')
            if strategy_regex.findall(strategy.text):
                await strategy.reply('Estratégia adicionada')
                strategy_text, bet_color = strategy.text.split(' = ')
                user_id = get_user_by_name(message.chat.username).id
                strategy = Strategy(
                    user_id=user_id,
                    strategy=strategy_text,
                    bet_color=bet_color,
                    value=float(value.text.replace(',', '.')),
                )
                create_strategy(strategy)
            else:
                await strategy.reply('Estratégia definida incorretamente')
        except ValueError:
            await value.reply(
                'Digite apenas números para o valor da aposta'
            )

    @login_required
    async def remove_strategy(client: Client, message: Message) -> None:
        strategy_id = await message.chat.ask('Digite o ID da estrátegia:')
        try:
            remove_strategy_by_id(int(strategy_id.text))
            await message.reply('Estratégia removida')
        except ValueError:
            await message.reply('ID inválido, digite apenas números')

    @login_required
    async def show_strategies(client: Client, message: Message) -> None:
        text_format = '{:<4}{:<18}{:<4}{}\n'
        text = 'ID Estratégia Cor Valor\n'
        user = get_user_by_name(message.chat.username)
        for strategy in get_strategies_from_user(user):
            text += text_format.format(
                strategy.id,
                strategy.strategy,
                strategy.bet_color,
                strategy.value,
            )
        await message.reply(text)

    async def create_browser(strategy: Strategy, signals: str) -> callable:
        async with async_playwright() as p:
            browser = await p.firefox.launch()
            context = await browser.new_context(storage_state=f'{user.name}.json')
            page = await context.new_page()
            await page.goto('https://www.arbety.com/games/double')
            show_result = False
            value = strategy.value
            while True:
                while signals == await get_signals(page):
                    await sleep(1)
                signals = get_signals(page)
                strategy_pattern = re.compile(f'{strategy.strategy}$')
                if strategy_pattern.findall(signals) and not show_result:
                    num_loss = 0
                    for bet in get_bets_from_strategy(strategy)[::-1]:
                        if bet.result == 'loss':
                            num_loss += 1
                        else:
                            break
                    if strategy.user.gale > num_loss and num_loss > 0:
                        value = strategy.value + strategy.value * num_loss
                    await to_bet(page, value, strategy.bet_color)
                    await send_bet_confirmation_message(strategy, value)
                    show_result = True
                elif show_result:
                    await send_result_message(strategy, value, signals)
                    break
            await browser.close()

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
        bet = Bet(
            value=value,
            color=strategy.bet_color,
            result='win',
            strategy_id=strategy.id,
        )
        if result_regex.findall(signals):
            message = f'➡️ RESULTADO 💚 WIN 💚\n{color_message}'
        else:
            bet.result = 'loss'
            message = f'➡️ RESULTADO ❌ LOSS ❌\n{color_message}'
        create_bet(bet)
        await app.send_message(strategy.user.name, message)

    if users:
        async with async_playwright() as p:
            browser = await p.firefox.launch()
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto('https://www.arbety.com/games/double')
            signals = get_signals(page)
            while True:
                while signals == get_signals(page):
                    await sleep(1)
                signals = get_signals(page)
                for user in users:
                    for strategy in get_strategies_from_user(user):
                        strategy_pattern = re.compile(r'.+( - [rwg] = [rwg])')
                        strategy_text = strategy_pattern.sub(
                            '',
                            strategy.strategy,
                        )
                        if signals[-len(strategy_text):] == strategy_text:
                            await create_browser(strategy, signals)
    else:
        await app.run()
