from asyncio import sleep
from datetime import timedelta

from playwright.async_api import TimeoutError




async def get_signals(page) -> str:
    result = []
    await page.wait_for_selector('.item', state='attached')
    items = await page.query_selector_all('.item')
    for item in items:
        item_class = await item.get_attribute('class')
        result.append(item_class.split()[-1][0])
    return ' - '.join(result)


async def to_bet(page, value: float, bet_color: str) -> None:
    await page.locator('#betValue').fill(str(value))
    bet_color = (
        'red' if bet_color == 'r' else 'green' if bet_color == 'g' else 'white'
    )
    await page.locator(f'.ball-{bet_color}').first.click()
    await page.locator('.button-primary').first.click()


async def make_login(page, email: str, password: str) -> None:
    await page.goto('https://www.arbety.com/home?modal=login')
    await page.locator('#email').fill(email)
    await page.locator('#current-password').fill(password)
    await page.locator('button.button-primary:not(.register)').click()


async def is_logged(page) -> bool:
    try:
        await page.wait_for_selector('.user-name', state='attached')
    except TimeoutError:
        return False
    return True
