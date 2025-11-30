# Multi-language translations for the bot
# Supported languages: uz (Uzbek), en (English), ru (Russian)

TRANSLATIONS = {
    # Start and language selection
    "welcome": {
        "uz": "<b>Assalamu alaykum!</b> <b>PrimeLingoBot</b>'ga xush kelibsiz! 🎓\n\nQuyidagi bo'limlardan birini tanlang:",
        "en": "Hello! Welcome to PrimeLingoBot! 🎓\n\nPlease select an option:",
        "ru": "Здравствуйте! Добро пожаловать в PrimeLingoBot! 🎓\n\nПожалуйста, выберите опцию:"
    },
    "select_language": {
        "uz": "Iltimos, tilni tanlang:",
        "en": "Please select your language:",
        "ru": "Пожалуйста, выберите язык:"
    },
    "language_selected": {
        "uz": "Til tanlandi: O'zbekcha ✅",
        "en": "Language selected: English ✅",
        "ru": "Язык выбран: Русский ✅"
    },
    
    # Main menu buttons
    "btn_search": {
        "uz": "🔍 Qidiruv",
        "en": "🔍 Search",
        "ru": "🔍 Поиск"
    },
    "btn_my_downloads": {
        "uz": "📥 Yuklab olinganlar",
        "en": "📥 My Downloads",
        "ru": "📥 Мои загрузки"
    },
    "btn_my_list": {
        "uz": "📁 Mening ro'yxatim",
        "en": "📁 My List",
        "ru": "📁 Мой список"
    },
    "btn_help": {
        "uz": "❓ Yordam",
        "en": "❓ Help",
        "ru": "❓ Помощь"
    },
    "btn_change_language": {
        "uz": "🌐 Tilni o'zgartirish",
        "en": "🌐 Change Language",
        "ru": "🌐 Изменить язык"
    },
    
    # Search flow
    "enter_search_query": {
        "uz": "<b>Qidiruv uchun kitob nomini kiriting:</b>",
        "en": "<b>Enter book name:</b>",
        "ru": "<b>Введите название книги:</b>"
    },
    "search_results": {
        "uz": "🔍 Qidiruv natijalari:",
        "en": "🔍 Search results:",
        "ru": "🔍 Результаты поиска:"
    },
    "searching": {
        "uz": "<i>🔍 Qidirilmoqda.....</i>",
        "en": "<i>🔍 Searching.....</i>",
        "ru": "<i>🔍 Поиск.....</i>"
    },
    "search_result_for": {
        "uz": "Qidiruv so'rovi: ☞ {query}",
        "en": "Search result for: ☞ {query}",
        "ru": "Результат поиска для: ☞ {query}"
    },
    "result_shown_in": {
        "uz": "Natija ko'rsatildi: ☞ {time} sekund",
        "en": "Result shown in: ☞ {time} seconds",
        "ru": "Результат показан за: ☞ {time} секунд"
    },
    "no_results": {
        "uz": "🚫 Hech narsa topilmadi. Boshqa so'z bilan qidiring.",
        "en": "🚫 No results found. Try searching with different keywords.",
        "ru": "🚫 Ничего не найдено. Попробуйте другие ключевые слова."
    },
    "select_menu_option": {
        "uz": "Quyidagi menular birini tanlang:",
        "en": "Please select one of the following menu options:",
        "ru": "Пожалуйста, выберите один из следующих пунктов меню:"
    },
    "level": {
        "uz": "Daraja",
        "en": "Level",
        "ru": "Уровень"
    },
    
    # File actions
    "btn_download": {
        "uz": "⬇️ Yuklab olish",
        "en": "⬇️ Download",
        "ru": "⬇️ Скачать"
    },
    "btn_save": {
        "uz": " Saqlash",
        "en": "📁 Save to My List",
        "ru": "📁 Сохранить"
    },
    "btn_remove": {
        "uz": "🗑 O'chirish",
        "en": "🗑 Remove",
        "ru": "🗑 Удалить"
    },
    "downloading": {
        "uz": "⏳ Yuklanmoqda.....",
        "en": "⏳ Downloading.....",
        "ru": "⏳ Загрузка....."
    },
    "file_saved": {
        "uz": "✅ Fayl ro'yxatga saqlandi!",
        "en": "✅ File saved to your list!",
        "ru": "✅ Файл сохранен в ваш список!"
    },
    "already_saved": {
        "uz": "❗️ Bu fayl allaqachon ro'yxatda.",
        "en": "❗️ This file is already in your list.",
        "ru": "❗️ Этот файл уже в вашем списке."
    },
    "file_removed": {
        "uz": "✅ Fayl ro'yxatdan o'chirildi.",
        "en": "✅ File removed from your list.",
        "ru": "✅ Файл удален из вашего списка."
    },
    
    # My Downloads
    "my_downloads_title": {
        "uz": "📥 Yuklab olingan fayllar:",
        "en": "📥 Downloaded files:",
        "ru": "📥 Загруженные файлы:"
    },
    "no_downloads": {
        "uz": "🚫 Siz hali hech narsa yuklab olmadingiz.",
        "en": "🚫 You haven't downloaded anything yet.",
        "ru": "🚫 Вы еще ничего не загрузили."
    },
    
    # My List
    "my_list_title": {
        "uz": "<b>📁 Saqlangan fayllar:</b>",
        "en": "📁 Saved files:",
        "ru": "📁 Сохраненные файлы:"
    },
    "no_saved_files": {
        "uz": "🚫 Saqlangan fayllar yo'q.",
        "en": "🚫 No saved files.",
        "ru": "🚫 Нет сохраненных файлов."
    },
    
    # Help
    "help_message": {
        "uz": """❓ <b>Yordam</b>

🤖 <b>Bot haqida:</b>
<b>PrimeLingoBot</b> - til o'rganish uchun kitoblar va materiallarni topish va yuklab olish uchun bot.

📖 <b>Qanday foydalanish:</b>

• 🔍 <b>Qidiruv</b> - kitob nomini kiriting va qidiring

• ⬇️ <b>Yuklab olish</b> - faylni Telegram orqali yuklab oling

• 📁 <b>Saqlash</b> - kerakli fayllarni ro'yxatga saqlang


👨‍💻 <b>Admin bilan bog'lanish: {admin_username}</b>

💡 <i>Savollar yoki takliflar bo'lsa, adminga murojaat qiling!</i>""",
        "en": """❓ <b>Help</b>

🤖 <b>About the bot:</b>
PrimeLingoBot - a bot for finding and downloading books and materials for language learning.

📖 <b>How to use:</b>
• 🔍 Search - enter book name and search
• ⬇️ Download - download files via Telegram
• ⭐️ Save - save useful files to your list
• 📥 My Downloads - your download history

👨‍💼 <b>Contact admin:</b>
@{admin_username}

💡 If you have questions or suggestions, contact the admin!""",
        "ru": """❓ <b>Помощь</b>

🤖 <b>О боте:</b>
PrimeLingoBot - бот для поиска и загрузки книг и материалов для изучения языков.

📖 <b>Как использовать:</b>
• 🔍 Поиск - введите название книги и ищите
• ⬇️ Скачать - загрузите файлы через Telegram
• ⭐️ Сохранить - сохраните нужные файлы в список
• 📥 Мои загрузки - история загрузок


👨‍💼 <b>Связаться с админом:</b>
@{admin_username}

💡 Если у вас есть вопросы или предложения, свяжитесь с админом!"""
    },
    
    # Pagination
    "btn_next": {
        "uz": "Keyingisi ➡️",
        "en": "Next ➡️",
        "ru": "Далее ➡️"
    },
    "btn_prev": {
        "uz": "⬅️ Oldingi",
        "en": "⬅️ Previous",
        "ru": "⬅️ Назад"
    },
    "page_info": {
        "uz": "Sahifa {current}/{total}",
        "en": "Page {current}/{total}",
        "ru": "Страница {current}/{total}"
    },
    
    # Admin messages
    "admin_only": {
        "uz": "🚫 Bu buyruq faqat admin uchun.",
        "en": "🚫 This command is for admin only.",
        "ru": "🚫 Эта команда только для админа."
    },
    "upload_send_file": {
        "uz": "📤 Faylni yuboring (PDF, MP3, va h.k.):",
        "en": "📤 Send the file (PDF, MP3, etc.):",
        "ru": "📤 Отправьте файл (PDF, MP3 и т.д.):"
    },
    "upload_enter_title": {
        "uz": "📝 Fayl nomini kiriting:",
        "en": "📝 Enter file title:",
        "ru": "📝 Введите название файла:"
    },
    "upload_send_thumbnail": {
        "uz": "🖼 Thumbnail rasmini yuboring (yoki /skip):",
        "en": "🖼 Send thumbnail image (or /skip):",
        "ru": "🖼 Отправьте изображение миниатюры (или /skip):"
    },
    "upload_enter_level": {
        "uz": "📊 Darajani kiriting (A1, A2, B1, B2, C1, C2 yoki /skip):",
        "en": "📊 Enter level (A1, A2, B1, B2, C1, C2 or /skip):",
        "ru": "📊 Введите уровень (A1, A2, B1, B2, C1, C2 или /skip):"
    },
    "upload_enter_tags": {
        "uz": "🏷 Teglarni kiriting (vergul bilan ajratilgan, yoki /skip):",
        "en": "🏷 Enter tags (comma-separated, or /skip):",
        "ru": "🏷 Введите теги (через запятую, или /skip):"
    },
    "upload_enter_description": {
        "uz": "📄 Tavsifni kiriting (yoki /skip):",
        "en": "📄 Enter description (or /skip):",
        "ru": "📄 Введите описание (или /skip):"
    },
    "upload_file_type": {
        "uz": "📁 Fayl turi: regular yoki mock_test?",
        "en": "📁 File type: regular or mock_test?",
        "ru": "📁 Тип файла: regular или mock_test?"
    },
    "upload_success": {
        "uz": "✅ Fayl muvaffaqiyatli yuklandi!\n\n📝 Nom: {title}\n🏷 Teglar: {tags}",
        "en": "✅ File uploaded successfully!\n\n📝 Title: {title}\n🏷 Tags: {tags}",
        "ru": "✅ Файл успешно загружен!\n\n📝 Название: {title}\n🏷 Теги: {tags}"
    },
    "upload_cancelled": {
        "uz": "🚫 Yuklash bekor qilindi.",
        "en": "🚫 Upload cancelled.",
        "ru": "🚫 Загрузка отменена."
    },
    "delete_success": {
        "uz": "✅ Fayl o'chirildi.",
        "en": "✅ File deleted.",
        "ru": "✅ Файл удален."
    },
    "delete_not_found": {
        "uz": "🚫 Fayl topilmadi.",
        "en": "🚫 File not found.",
        "ru": "🚫 Файл не найден."
    },
    "stats_message": {
        "uz": """📊 <b>Bot Statistikalari</b>

★ Jami foydalanuvchilar: <b>{users}</b>
★ Jami fayllar: <b>{files}</b>
★ Ishlatilgan xotira: <b>{storage}</b>
★ Jami yuklab olishlar: <b>{downloads}</b>""",
        "en": """📊 <b>Bot Statistics</b>

★ Total users: <b>{users}</b>
★ Total files: <b>{files}</b>
★ Storage used: <b>{storage}</b>
★ Total downloads: <b>{downloads}</b>""",
        "ru": """📊 <b>Статистика бота</b>

★ Всего пользователей: <b>{users}</b>
★ Всего файлов: <b>{files}</b>
★ Использовано памяти: <b>{storage}</b>
★ Всего загрузок: <b>{downloads}</b>"""
    },
    "user_blocked": {
        "uz": "✅ Foydalanuvchi bloklandi.",
        "en": "✅ User blocked.",
        "ru": "✅ Пользователь заблокирован."
    },
    "user_unblocked": {
        "uz": "✅ Foydalanuvchi blokdan chiqarildi.",
        "en": "✅ User unblocked.",
        "ru": "✅ Пользователь разблокирован."
    },
    "broadcast_sent": {
        "uz": "✅ Xabar {count} foydalanuvchiga yuborildi.",
        "en": "✅ Message sent to {count} users.",
        "ru": "✅ Сообщение отправлено {count} пользователям."
    },
    "you_are_blocked": {
        "uz": "🚫 Siz bloklangansiz. Admin bilan bog'laning: {admin_username}",
        "en": "🚫 You are blocked. Contact the admin: @{admin_username}",
        "ru": "🚫 Вы заблокированы. Свяжитесь с админом: @{admin_username}"
    },
    
    # Settings
    "send_default_thumbnail": {
        "uz": "🖼 Standart thumbnail rasmini yuboring:",
        "en": "🖼 Send default thumbnail image:",
        "ru": "🖼 Отправьте стандартное изображение миниатюры:"
    },
    "default_thumbnail_set": {
        "uz": "✅ Standart thumbnail o'rnatildi!",
        "en": "✅ Default thumbnail set!",
        "ru": "✅ Стандартная миниатюра установлена!"
    },
    "default_thumbnail_deleted": {
        "uz": "✅ Standart thumbnail o'chirildi.",
        "en": "✅ Default thumbnail deleted.",
        "ru": "✅ Стандартная миниатюра удалена."
    },
    
    # Force Subscribe (FSub)
    "no_fsub_channels": {
        "uz": "🚫 Force Join kanallar yo'q.",
        "en": "🚫 No Force Join Channels.",
        "ru": "🚫 Нет каналов для обязательной подписки."
    },
    "fsub_channels_list": {
        "uz": "📢 Force Join kanallar ro'yxati:",
        "en": "📢 Force Join Channels List:",
        "ru": "📢 Список каналов для обязательной подписки:"
    },
    "add_fsub_instruction": {
        "uz": "📢 Force Join kanal qo'shish:\n\nKanalni forward qiling yoki kanal username yoki ID ni yuboring.\n\nMisol: @channel yoki -1001234567890",
        "en": "📢 Add Force Join Channel:\n\nForward a channel message or send channel username or ID.\n\nExample: @channel or -1001234567890",
        "ru": "📢 Добавить канал для обязательной подписки:\n\nПерешлите сообщение из канала или отправьте username или ID канала.\n\nПример: @channel или -1001234567890"
    },
    "fsub_channel_added": {
        "uz": "✅ Force Join kanal qo'shildi: {channel}",
        "en": "✅ Force Join channel added: {channel}",
        "ru": "✅ Канал для обязательной подписки добавлен: {channel}"
    },
    "fsub_channel_exists": {
        "uz": "ℹ️ Bu kanal allaqachon ro'yxatda.",
        "en": "ℹ️ This channel is already in the list.",
        "ru": "ℹ️ Этот канал уже в списке."
    },
    "fsub_channel_removed": {
        "uz": "✅ Force Join kanal o'chirildi.",
        "en": "✅ Force Join channel removed.",
        "ru": "✅ Канал для обязательной подписки удален."
    },
    "fsub_channel_not_found": {
        "uz": "🚫 Kanal topilmadi. Kanal username yoki ID ni to'g'ri kiriting.",
        "en": "🚫 Channel not found. Please enter correct channel username or ID.",
        "ru": "🚫 Канал не найден. Пожалуйста, введите правильный username или ID канала."
    },
    "fsub_invalid_format": {
        "uz": "🚫 Noto'g'ri format. Kanalni forward qiling yoki @username yoki ID kiriting.",
        "en": "🚫 Invalid format. Forward a channel message or enter @username or ID.",
        "ru": "🚫 Неверный формат. Перешлите сообщение из канала или введите @username или ID."
    },
    "fsub_join_required": {
        "uz": "<b>⚠️ Botdan foydalanish uchun quyidagi kanal(lar)ga a'zo bo'lishingiz kerak! </b>\n\n<i>Quyidagi tugmalarni bosib kanallarga a'zo bo'ling, so'ng tasdiqlash tugmasini bosing.</i>",
        "en": "<b>⚠️ You must join the following channel(s) to use the bot: </b>\n\n<i>Click the buttons below to join the channels, then click the confirmation button.</i>",
        "ru": "<b>⚠️ Вы должны подписаться на следующие каналы, чтобы использовать бота:</b>\n\n<i>Нажмите кнопки ниже, чтобы подписаться на каналы, затем нажмите кнопку подтверждения.</i>"
    },
    "btn_confirm_joined": {
        "uz": "✅ Tasdiqlash - A'zo bo'ldim",
        "en": "✅ Confirm - I Joined",
        "ru": "✅ Подтвердить - Я подписался"
    },
    "fsub_joined_success": { 
        "uz": "✅ Tabriklaymiz! Barcha kanallarga a'zo bo'ldingiz. Endi botdan foydalanishingiz mumkin!",
        "en": "✅ Congratulations! You have joined all channels. You can now use the bot!",
        "ru": "✅ Поздравляем! Вы подписались на все каналы. Теперь вы можете использовать бота!"
    },
    "fsub_not_joined": {
        "uz": "<b>❗️ Siz hali kanal(lar)ga a'zo bo'lmadingiz:</b>\n\n<b><i>Iltimos, barcha kanallarga a'zo bo'ling va qayta urinib ko'ring.</i></b>",
        "en": "<b>🚫 You haven't joined the channel(s) yet:</b>\n\nPlease join all channels and try again.",
        "ru": "<b>🚫 Вы еще не подписались на следующие каналы:</b>\n\nПожалуйста, подпишитесь на все каналы и попробуйте снова."
    },
    "fsub_no_channels": {
        "uz": "ℹ️ Hozircha force join kanallar yo'q.",
        "en": "ℹ️ No force join channels at the moment.",
        "ru": "ℹ️ Нет каналов для обязательной подписки в данный момент."
    }
}


def get_text(key: str, lang: str = "uz", **kwargs) -> str:
    """
    Get translated text by key and language
    
    Args:
        key: Translation key
        lang: Language code (uz, en, ru)
        **kwargs: Format arguments for the text
    
    Returns:
        Translated and formatted text
    """
    text = TRANSLATIONS.get(key, {}).get(lang, TRANSLATIONS.get(key, {}).get("uz", key))
    if kwargs:
        return text.format(**kwargs)
    return text
