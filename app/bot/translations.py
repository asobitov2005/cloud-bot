# Multi-language translations for the bot
# Supported languages: uz (Uzbek), en (English), ru (Russian)

TRANSLATIONS = {
    # Start and language selection
    "welcome": {
        "uz": "Assalomu alaykum! PrimeLingoBot'ga xush kelibsiz! 🎓\n\nIltimos, tilni tanlang:",
        "en": "Hello! Welcome to PrimeLingoBot! 🎓\n\nPlease select your language:",
        "ru": "Здравствуйте! Добро пожаловать в PrimeLingoBot! 🎓\n\nПожалуйста, выберите язык:"
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
        "uz": "⭐️ Mening ro'yxatim",
        "en": "⭐️ My List",
        "ru": "⭐️ Мой список"
    },
    "btn_mock_tests": {
        "uz": "📝 Mock testlar",
        "en": "📝 Mock tests",
        "ru": "📝 Пробные тесты"
    },
    "btn_help": {
        "uz": "❓ Yordam",
        "en": "❓ Help",
        "ru": "❓ Помощь"
    },
    
    # Search flow
    "enter_search_query": {
        "uz": "📚 Kitob nomini kiriting:",
        "en": "📚 Enter book name:",
        "ru": "📚 Введите название книги:"
    },
    "search_results": {
        "uz": "🔍 Qidiruv natijalari:",
        "en": "🔍 Search results:",
        "ru": "🔍 Результаты поиска:"
    },
    "no_results": {
        "uz": "❌ Hech narsa topilmadi. Boshqa so'z bilan qidiring.",
        "en": "❌ No results found. Try searching with different keywords.",
        "ru": "❌ Ничего не найдено. Попробуйте другие ключевые слова."
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
        "uz": "⭐️ Saqlash",
        "en": "⭐️ Save to My List",
        "ru": "⭐️ Сохранить"
    },
    "btn_remove": {
        "uz": "🗑 O'chirish",
        "en": "🗑 Remove",
        "ru": "🗑 Удалить"
    },
    "downloading": {
        "uz": "📥 Yuklab olinmoqda...",
        "en": "📥 Downloading...",
        "ru": "📥 Загрузка..."
    },
    "file_saved": {
        "uz": "✅ Fayl ro'yxatga saqlandi!",
        "en": "✅ File saved to your list!",
        "ru": "✅ Файл сохранен в ваш список!"
    },
    "already_saved": {
        "uz": "ℹ️ Bu fayl allaqachon ro'yxatda.",
        "en": "ℹ️ This file is already in your list.",
        "ru": "ℹ️ Этот файл уже в вашем списке."
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
        "uz": "❌ Siz hali hech narsa yuklab olmadingiz.",
        "en": "❌ You haven't downloaded anything yet.",
        "ru": "❌ Вы еще ничего не загрузили."
    },
    
    # My List
    "my_list_title": {
        "uz": "⭐️ Saqlangan fayllar:",
        "en": "⭐️ Saved files:",
        "ru": "⭐️ Сохраненные файлы:"
    },
    "no_saved_files": {
        "uz": "❌ Saqlangan fayllar yo'q.",
        "en": "❌ No saved files.",
        "ru": "❌ Нет сохраненных файлов."
    },
    
    # Mock tests
    "mock_tests_title": {
        "uz": "📝 Mock testlar:",
        "en": "📝 Mock tests:",
        "ru": "📝 Пробные тесты:"
    },
    "no_mock_tests": {
        "uz": "❌ Hozircha mock testlar mavjud emas.",
        "en": "❌ No mock tests available yet.",
        "ru": "❌ Пробные тесты пока недоступны."
    },
    
    # Help
    "help_message": {
        "uz": """❓ <b>Yordam</b>

🤖 <b>Bot haqida:</b>
PrimeLingoBot - til o'rganish uchun kitoblar va materiallarni topish va yuklab olish uchun bot.

📖 <b>Qanday foydalanish:</b>
• 🔍 Qidiruv - kitob nomini kiriting va qidiring
• ⬇️ Yuklab olish - faylni Telegram orqali yuklab oling
• ⭐️ Saqlash - kerakli fayllarni ro'yxatga saqlang
• 📥 Yuklab olinganlar - yuklab olgan fayllaringiz tarixi
• 📝 Mock testlar - amaliy testlar

👨‍💼 <b>Admin bilan bog'lanish:</b>
@{admin_username}

💡 Savollar yoki takliflar bo'lsa, adminga murojaat qiling!""",
        "en": """❓ <b>Help</b>

🤖 <b>About the bot:</b>
PrimeLingoBot - a bot for finding and downloading books and materials for language learning.

📖 <b>How to use:</b>
• 🔍 Search - enter book name and search
• ⬇️ Download - download files via Telegram
• ⭐️ Save - save useful files to your list
• 📥 My Downloads - your download history
• 📝 Mock tests - practice tests

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
• 📝 Пробные тесты - практические тесты

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
        "uz": "❌ Bu buyruq faqat admin uchun.",
        "en": "❌ This command is for admin only.",
        "ru": "❌ Эта команда только для админа."
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
        "uz": "❌ Yuklash bekor qilindi.",
        "en": "❌ Upload cancelled.",
        "ru": "❌ Загрузка отменена."
    },
    "delete_success": {
        "uz": "✅ Fayl o'chirildi.",
        "en": "✅ File deleted.",
        "ru": "✅ Файл удален."
    },
    "delete_not_found": {
        "uz": "❌ Fayl topilmadi.",
        "en": "❌ File not found.",
        "ru": "❌ Файл не найден."
    },
    "stats_message": {
        "uz": """📊 <b>Statistika</b>

👥 Jami foydalanuvchilar: {users}
📁 Jami fayllar: {files}
📥 Jami yuklab olishlar: {downloads}

🔥 <b>Top 10 yuklab olingan fayllar:</b>
{top_files}""",
        "en": """📊 <b>Statistics</b>

👥 Total users: {users}
📁 Total files: {files}
📥 Total downloads: {downloads}

🔥 <b>Top 10 downloaded files:</b>
{top_files}""",
        "ru": """📊 <b>Статистика</b>

👥 Всего пользователей: {users}
📁 Всего файлов: {files}
📥 Всего загрузок: {downloads}

🔥 <b>Топ 10 загруженных файлов:</b>
{top_files}"""
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
        "uz": "❌ Siz bloklangansiz. Admin bilan bog'laning.",
        "en": "❌ You are blocked. Contact the admin.",
        "ru": "❌ Вы заблокированы. Свяжитесь с админом."
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
