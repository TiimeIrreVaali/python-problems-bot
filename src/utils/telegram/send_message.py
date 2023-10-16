import logging
import pathlib

from telegram import Bot, InlineKeyboardMarkup, LabeledPrice, Message, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.error import Forbidden

from settings import IS_DEBUG, SUBSCRIPTION_PRICE, BotSettings
from src.images import IMAGE_TYPE_TO_IMAGE_PATH, ImageType
from src.services.questions import Question, QuestionsService
from src.texts import PREPAYMENT_TEXT
from src.utils.formaters import format_question
from src.utils.logging.init_logger import init_logger
from src.utils.telegram.inline_keyboard import (
    format_inline_keyboard,
    format_inline_keyboard_for_question,
)

init_logger(is_debug=IS_DEBUG)
logger = logging.getLogger(__name__)


async def _send_message(
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    message: Message | None = None,
    bot: Bot | None = None,
    chat_id: int | None = None,
    photo_path: pathlib.Path = None
) -> bool:
    if not message and not bot:
        raise ValueError('message or bot should be passed to send message')

    if not reply_markup:
        reply_markup = ReplyKeyboardRemove()
    try:
        if message:
            if photo_path:
                await message.reply_photo(
                    photo=photo_path,
                    caption=text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                )
            else:
                await message.reply_text(
                    text=text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                )
        elif bot:
            if photo_path:
                await bot.send_photo(
                    photo=photo_path,
                    caption=text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                )
    except Forbidden:
        logger.error('User has blocked bot')
        return False

    return True


async def send_message(
    text: str,
    choices: list[str] | None = None,
    message: Message | None = None,
    bot: Bot | None = None,
    chat_id: int | None = None,
    image: ImageType | None = None
) -> None:
    await _send_message(
        message=message,
        bot=bot,
        chat_id=chat_id,
        text=text,
        reply_markup=format_inline_keyboard(choices=choices) if choices else None,
        photo_path=IMAGE_TYPE_TO_IMAGE_PATH.get(image) or None
    )


async def send_question(
    question: Question,
    questions_service: QuestionsService,
    user_id: int,
    message: Message | None = None,
    bot: Bot | None = None,
    chat_id: int | None = None
) -> bool:
    reply_markup = format_inline_keyboard_for_question(
        choices=question.choices,
        question_id=question.id
    )
    is_sent = await _send_message(
        message=message,
        bot=bot,
        chat_id=chat_id,
        text=format_question(question=question),
        reply_markup=reply_markup,
    )
    if is_sent:
        await questions_service.send_question(user_id=user_id, question_id=question.id)
        logger.info('Send question to user %d', user_id)
    return is_sent


async def send_payment(
    telegram_user_id: int,
    message: Message | None = None,
    bot: Bot | None = None,
    chat_id: int | None = None
) -> bool:
    bot_settings = BotSettings()
    is_sent = await _send_message(
        message=message,
        bot=bot,
        chat_id=chat_id,
        text=PREPAYMENT_TEXT
    )
    if not is_sent:
        return False

    title = 'Оплата (Python каждый день)'
    description = 'Оплата 1 месяца тренажера для подготовки к собеседованиям на Python разработчика'
    prices = [LabeledPrice('Python каждый день', SUBSCRIPTION_PRICE * 100)]
    currency = 'RUB'
    payload = str(telegram_user_id)

    kwargs = {
        'title': title,
        'description': description,
        'provider_token': bot_settings.PAYMENT_PROVIDER_TOKEN,
        'currency': currency,
        'payload': payload,
        'prices': prices,
        'need_email': True,
        'send_email_to_provider': True,
        'provider_data': {
            'receipt': {
                'items': [{
                    'description': description,
                    'amount': {
                        'value': f'{SUBSCRIPTION_PRICE}.00',
                        'currency': currency,
                    },
                    'vat_code': 1,
                    'quantity': '1.00'
                }]
            }
        }
    }

    if message:
        await message.reply_invoice(**kwargs)
    elif bot:
        await bot.send_invoice(chat_id=chat_id, **kwargs)
    return True
