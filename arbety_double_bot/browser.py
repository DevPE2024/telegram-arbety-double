from asyncio import sleep
from datetime import timedelta

from playwright.async_api import TimeoutError


async def create_browser(strategy: Strategy, signals: str) -> callable:
    async with async_playwright() as p:
        browser = await p.firefox.launch()
        context = await browser.new_context(storage_state=f'{user.name}.json')
        page = await context.new_page()
        await page.goto('https://www.arbety.com/games/double')
        show_result = False
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
                if strategy.user.gale <= num_loss or num_loss == 0:
                    value = strategy.value
                else:
                    value = strategy.value + strategy.value * num_loss
                await to_bet(page, value, strategy.bet_color)
                await send_bet_confirmation_message(strategy, value)
                show_result = True
            elif show_result:
                await send_result_message(strategy, signals)
                break


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
