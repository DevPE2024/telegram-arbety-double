from arbety_double_bot.domain import Strategy, User
from arbety_double_bot.repositories import (
    create_strategy,
    create_user,
    get_strategies_from_user,
    get_users,
)


def test_create_user() -> None:
    email = 'richard@gmail.com'
    password = 'Richard123'
    create_user(email, password)
    expected = User(id=1, email=email, password=password)
    get_users()[0] == expected


def test_create_strategy() -> None:
    strategy = 'r - r - g = g'
    value = 50
    create_strategy(1, strategy, value)
    expected = Strategy(strategy=strategy, value=value)
    get_strategies_from_user(1) == [expected]
