from arbety_double_bot.app import create_app
from arbety_double_bot.browser import get_signals,  to_bet
from arbety_double_bot.common import create_driver
from arbety_double_bot.repositories import get_strategies_from_user, get_users


if __name__ == '__main__':
    signals = []
    app = create_app()
    app.start()
    while True:
        signals = get_signals()
        for user in get_users():
            for strategy in get_strategies_from_user(user.id):
                bet_color = strategy.strategy.split(' = ')[-1]
                strategy_list = strategy.strategy.split(' = ')[0].split(' - ')
                if strategy_list == sinals[-len(strategy_list):]:
                    to_bet(create_driver(), strategy.value, bet_color)
    app.stop()
