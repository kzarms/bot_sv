import pytest
from telegram import Bot, BotCommand, Chat, Dice, Message, Update, User
from telegram.ext import CallbackContext

import src.bot as test_module


@pytest.fixture(scope="module")
def bot_command():
    return BotCommand(command="start", description="A command")


@pytest.fixture(scope="function")
def bot():
    return Bot("TEST_TOKEN")


@pytest.fixture(scope="function")
def update(bot):
    # Create a fake Update object with a /start command
    user = User(id=1, first_name="Test", is_bot=False)
    chat = Chat(id=1, type="private")
    message = Message(
        message_id=1, date=None, chat=chat, text="/start", from_user=user, bot=bot
    )
    return Update(update_id=1, message=message)


class TestReg:

    command = "/reg"
    description = "A command"

    async def test_reg(self, bot_command):
        # Test preparation
        context = CallbackContext.from_update(update, bot)
        update.message.reply_text = lambda text, **kwargs: setattr(
            update.message, "test_reply_text", text
        )
        # Test execution
        test_module.reg(bot, update)
        # Test validation
        assert update.message.test_reply_text == "Welcome to the bot!"
