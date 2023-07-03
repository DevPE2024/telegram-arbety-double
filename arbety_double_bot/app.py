import os
import re

from dotenv import load_dotenv
from playwright.async_api import async_playwright
from pyrogram import Client, filters
from pyrogram.types import Message
from pyromod import listen

from arbety_double_bot.browser import is_logged, make_login
from arbety_double_bot.repositories import (
    create_strategy,
    create_user,
    edit_user,
    get_strategies_from_user,
    get_user_by_name,
)


def create_app() -> Client:
    load_dotenv()
    app = Client(
        os.environ['BOT_NAME'],
        api_id=os.environ['API_ID'],
        api_hash=os.environ['API_HASH'],
        bot_token=os.environ['BOT_TOKEN'],
    )

    @app.on_message(filters.command(['start', 'help']))
    async def start(client: Client, message: Message) -> None:
        await message.reply(
            (
                '/login - Para cadastrar o login da plataforma arbety\n'
                '/adicionar - Para adicionar uma estratégia, junto '
                'com o valor de aposta\n'
                '/listar - Para listar todas as estratégias adicionadas'
            )
        )

    @app.on_message(filters.command('login'))
    async def login(client: Client, message: Message) -> None:
        email = await message.chat.ask('Digite seu email:')
        password = await message.chat.ask('Digite sua senha:')
        login = await password.reply('Fazendo login...')
        async with async_playwright() as p:
            browser = await p.firefox.launch()
            page = await browser.new_page()
            await make_login(page, email.text, password.text)
            if await is_logged(page):
                user = get_user_by_name(message.chat.username)
                if user:
                    edit_user(user.id, email.text, password.text)
                else:
                    create_user(
                        message.chat.username, email.text, password.text
                    )
                await login.edit_text('Login realizado')
                os.system('systemctl restart arbety-double-bot')
            else:
                await login.edit_text('Login inválido')
            await browser.close()

    @app.on_message(filters.command('adicionar'))
    async def add_strategy(client: Client, message: Message) -> None:
        if get_user_by_name(message.chat.username):
            strategy = await message.chat.ask(
                (
                    'Digite sua estratégia utilizando r (red), g (green) e w '
                    '(white), exemplo: r - r - g = r\nNesse exemplo sempre que '
                    'der essa sequência ele vai apostar no vermelho'
                ),
            )
            value = await message.chat.ask(
                'Digite o valor para a aposta, exemplo: 50 ou 50,00'
            )
            try:
                strategy_regex = re.compile(r'[rwg]( - [rwg])+ = [rwg]')
                if strategy_regex.findall(strategy.text):
                    await strategy.reply('Estratégia adicionada')
                    strategy_text, bet_color = strategy.text.split(' = ')
                    user_id = get_user_by_name(message.chat.username).id
                    create_strategy(
                        user_id,
                        strategy_text,
                        bet_color,
                        float(value.text.replace(',', '.')),
                    )
                else:
                    await strategy.reply('Estratégia definida incorretamente')
            except ValueError:
                await value.reply(
                    'Digite apenas números para o valor da aposta'
                )
        else:
            await message.reply(
                'Primeiro faça o login para adicionar uma estratégia'
            )

    @app.on_message(filters.command('remover'))
    def remove_strategy(client: Client, message: Message) -> None:
        if get_user_by_name(message.chat.username):
            strategy_id = await message.chat.ask('Digite o ID da estrátegia:')
            try:
                remove_strategy(int(strategy_id.text))
                await message.reply('Estratégia removida')
            except ValueError:
                await message.reply('ID inválido, digite apenas números')
        else:
            await message.reply(
                'Primeiro faça o login para remover suas estratégias'
            )

    @app.on_message(filters.command('listar'))
    async def show_strategies(client: Client, message: Message) -> None:
        if get_user_by_name(message.chat.username):
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
        else:
            await message.reply(
                'Primeiro faça o login para mostrar suas estratégias'
            )

    return app
