async def get_signals(page) -> str:
    await page.goto('https://www.arbety.com/games/double')
    result = []
    for item in await page.locator('.item').all():
        print(await item.get_attribute('class'))
        result.append(item.get_attribute('class').split()[-1][0])
    return ' - '.join(result)


async def to_bet(page, value: float, bet_color: str) -> None:
    await page.goto('https://www.arbety.com/games/double')
    await page.locator('#betValue').fill(str(value))
    bet_color = (
        'red' if bet_color == 'r' else 'green' if bet_color == 'g' else 'white'
    )
    await page.locator(f'.ball-{bet_color}').click()
    await page.locator('.button-primary').click()


async def make_login(page, email: str, password: str) -> None:
    await page.goto('https://www.arbety.com/home?modal=login')
    await page.locator('#email').fill(email)
    await page.locator('#current-password').fill(password)
    await page.locator('button.button-primary:not(.register)').click()


async def is_logged(page) -> bool:
    return await page.locator('.user-name').count()
