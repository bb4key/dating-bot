from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# Районы Осло
OSLO_DISTRICTS = [
    "Sentrum", "Grünerløkka", "Frogner", "St. Hanshaugen",
    "Sagene", "Gamle Oslo", "Bjerke", "Grorud",
    "Stovner", "Alna", "Østensjø", "Nordstrand",
    "Søndre Nordstrand", "Nordre Aker", "Ullern", "Vestre Aker",
]


# ─── REPLY KEYBOARDS ─────────────────────────────────────────────────────────

def main_menu_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.row(
        KeyboardButton(text="👀 Смотреть анкеты"),
        KeyboardButton(text="❤️ Мои совпадения"),
    )
    kb.row(
        KeyboardButton(text="👤 Моя анкета"),
        KeyboardButton(text="⚙️ Настройки"),
    )
    return kb.as_markup(resize_keyboard=True)


def gender_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="👨 Парень"), KeyboardButton(text="👩 Девушка"))
    return kb.as_markup(resize_keyboard=True)


def looking_for_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="👨 Парней"), KeyboardButton(text="👩 Девушек"))
    kb.row(KeyboardButton(text="💫 Всех"))
    return kb.as_markup(resize_keyboard=True)


def district_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    for i in range(0, len(OSLO_DISTRICTS), 2):
        row = [KeyboardButton(text=OSLO_DISTRICTS[i])]
        if i + 1 < len(OSLO_DISTRICTS):
            row.append(KeyboardButton(text=OSLO_DISTRICTS[i + 1]))
        kb.row(*row)
    kb.row(KeyboardButton(text="❌ Отмена"))
    return kb.as_markup(resize_keyboard=True)


def cancel_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="❌ Отмена"))
    return kb.as_markup(resize_keyboard=True)


def skip_cancel_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="⏭ Пропустить"), KeyboardButton(text="❌ Отмена"))
    return kb.as_markup(resize_keyboard=True)


def profile_active_kb(is_active: bool) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    status_text = "🔴 Скрыть анкету" if is_active else "🟢 Показывать анкету"
    kb.row(KeyboardButton(text="✏️ Редактировать"), KeyboardButton(text=status_text))
    kb.row(KeyboardButton(text="🏠 Главное меню"))
    return kb.as_markup(resize_keyboard=True)


def edit_profile_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="📝 Имя"), KeyboardButton(text="🎂 Возраст"))
    kb.row(KeyboardButton(text="🗺️ Район"), KeyboardButton(text="💬 О себе"))
    kb.row(KeyboardButton(text="📸 Фото"))
    kb.row(KeyboardButton(text="◀️ Назад"))
    return kb.as_markup(resize_keyboard=True)


def back_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="◀️ Назад"))
    return kb.as_markup(resize_keyboard=True)


def chat_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="🚪 Завершить чат"))
    return kb.as_markup(resize_keyboard=True)


# ─── INLINE KEYBOARDS ────────────────────────────────────────────────────────

def browse_actions_kb(profile_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="❤️", callback_data=f"like:{profile_id}"),
        InlineKeyboardButton(text="👎", callback_data=f"dislike:{profile_id}"),
        InlineKeyboardButton(text="⚡ Суперлайк", callback_data=f"superlike:{profile_id}"),
    )
    kb.row(
        InlineKeyboardButton(text="🚩 Пожаловаться", callback_data=f"report:{profile_id}"),
    )
    return kb.as_markup()


def match_actions_kb(partner_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="💬 Написать", callback_data=f"chat_start:{partner_id}"),
        InlineKeyboardButton(text="❌ Удалить", callback_data=f"unmatch:{partner_id}"),
    )
    return kb.as_markup()


def notify_match_kb(partner_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="💬 Написать первым!", callback_data=f"chat_start:{partner_id}"),
    )
    return kb.as_markup()


def complaint_reasons_kb(to_user: int) -> InlineKeyboardMarkup:
    reasons = [
        ("🔞 Непристойный контент", "obscene"),
        ("🤖 Бот / Спам", "spam"),
        ("💸 Мошенничество", "scam"),
        ("😡 Оскорбления", "insults"),
        ("📵 Другое", "other"),
    ]
    kb = InlineKeyboardBuilder()
    for label, code in reasons:
        kb.row(InlineKeyboardButton(
            text=label, callback_data=f"complaint:{to_user}:{code}"
        ))
    kb.row(InlineKeyboardButton(text="❌ Отмена", callback_data="complaint_cancel"))
    return kb.as_markup()


def confirm_delete_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✅ Да, удалить", callback_data="delete_profile_confirm"),
        InlineKeyboardButton(text="❌ Нет", callback_data="delete_profile_cancel"),
    )
    return kb.as_markup()


def settings_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🔍 Изменить: кого ищу", callback_data="settings_looking"))
    kb.row(InlineKeyboardButton(text="👤 Изменить: мой пол", callback_data="settings_gender"))
    kb.row(InlineKeyboardButton(text="🗑️ Удалить анкету", callback_data="delete_profile"))
    return kb.as_markup()


def settings_looking_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="👨 Парней", callback_data="set_looking:male"),
        InlineKeyboardButton(text="👩 Девушек", callback_data="set_looking:female"),
    )
    kb.row(InlineKeyboardButton(text="💫 Всех", callback_data="set_looking:any"))
    kb.row(InlineKeyboardButton(text="◀️ Назад", callback_data="settings_back"))
    return kb.as_markup()


def settings_gender_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="👨 Парень", callback_data="set_gender:male"),
        InlineKeyboardButton(text="👩 Девушка", callback_data="set_gender:female"),
    )
    kb.row(InlineKeyboardButton(text="◀️ Назад", callback_data="settings_back"))
    return kb.as_markup()
