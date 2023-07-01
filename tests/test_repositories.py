from arbety_double_bot.repositories import create_strategy, create_user


def test_create_user() -> None:
    email = 'richard@gmail.com'
    password = 'Richard123'
    create_user(email, password)
    expected = User(id=1, email=email, password=password)
    get_user_by_email(email) == expected


def test_create_strategy() -> None:
    strategy = 'r - r - g = g'
    value = 50
    create_strategy(user_id=1, strategy, value)
    expected = Strategy(strategy=strategy, value=value)
    get_strategies_from_user(user_id=1) == [expected]
