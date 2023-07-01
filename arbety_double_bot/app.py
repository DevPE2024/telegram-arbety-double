import pyromod
from dotenv import load_dotenv
from pyrogram import Client, filters

from arbety_double_bot.browser import is_logged, make_login
from arbety_double_bot.driver import create_driver
from arbety_double_bot.repositories import create_strategy, create_user


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
                '/adicionar_estrategia - Para adicionar uma estratégia, junto com o valor de aposta'
            )
        )

    @app.on_message(filters.command('login'))
    async def login(client: Client, message: Message) -> None:
        email = await client.ask(message.chat.id, 'Digite seu email:')
        password = await client.ask(message.chat.id, 'Digite sua senha:')
        driver = create_driver()
        make_login(driver, email.text, password.text)
        if is_logged(driver):
            create_user(email.text, password.text)
            await client.send_message(message.chat.id, 'Login cadastrado')
        else:
            await client.send_message(message.chat.id, 'Login inválido')
        driver.quit()

    @app.on_message(filters.command('adicionar_estrategia'))
    async def add_strategy(client: Client, message: Message) -> None:
        strategy = await client.ask(
            message.chat.id,
            (
                'Digite sua estratégia utilizando r (red), g (green) e w '
                '(white), exemplo: r - r - g = r\nNesse exemplo sempre que '
                'der essa sequência ele vai apostar no vermelho'
            ),
        )
        strategy_regex = re.compile()
        value = await client.ask(
            'Digite o valor para a aposta, exemplo: 50 ou 50,00'
        )
        try:
            if strategy_regex.findall(strategy.text):
                await strategy.reply('Estratégia adicionada')
                create_strategy(
                    strategy.text,
                    float(value.text.replace(',', '.')),
                )
            else:
                await strategy.reply('Estratégia definida incorretamente')
        except ValueError:
            await value.reply('Digite apenas números para o valor da aposta')

    return app
