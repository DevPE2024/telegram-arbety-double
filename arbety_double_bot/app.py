from dotenv import load_dotenv
from pyrogram import Client, filters
import pyromod

from arbety_double_bot.browser import create_driver, is_logged, make_login


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
            )
        )

    @app.on_message(filters.command('login'))
    async def login(client: Client, message: Message) -> None:
        email = await client.ask(message.chat.id, 'Digite seu email:')
        password = await client.ask(message.chat.id, 'Digite sua senha:')
        driver = create_driver()
        make_login(driver, email.text, password.text)
        if is_logged(driver):
            await client.send_message(message.chat.id, 'Login cadastrado')
        else:
            await client.send_message(message.chat.id, 'Login inválido')
        driver.quit()

    return app
