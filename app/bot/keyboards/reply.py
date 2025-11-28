from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.bot.translations import get_text


def get_language_keyboard() -> ReplyKeyboardMarkup:
    """Get language selection keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🇺🇿 O'zbekcha"),
                KeyboardButton(text="🇬🇧 English"),
                KeyboardButton(text="🇷🇺 Русский")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard


def get_main_menu_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Get main menu keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text("btn_search", lang)),
                KeyboardButton(text=get_text("btn_my_downloads", lang))
            ],
            [
                KeyboardButton(text=get_text("btn_my_list", lang))
            ],
            [
                KeyboardButton(text=get_text("btn_help", lang)),
                KeyboardButton(text=get_text("btn_change_language", lang))
            ]
        ],
        resize_keyboard=True
    )
    return keyboard



