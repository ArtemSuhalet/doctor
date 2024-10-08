import telebot
import handlers
from telebot import types
from telebot.types import Message, BotCommand
from config_data.config import DEFAULT_COMMANDS
from loader import bot




if __name__ == '__main__':
    def set_default_commands(bot):
        bot.set_my_commands(
            [BotCommand(*i) for i in DEFAULT_COMMANDS]
        )
    bot.polling(none_stop=True, interval=0)