"""
Bot Text Constants
Created by RainZerg on 2025-03-08 12:09:32 UTC
"""

from config import COURSE_PRICE, COURSE_TITLE

def escape_markdown(text: str) -> str:
    """Helper function to escape MarkdownV2 special characters"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

# Format price for display (e.g., "10 000")
COURSE_PRICE_RUB = COURSE_PRICE / 100  # Convert kopeks to rubles
COURSE_PRICE_STR = f"{COURSE_PRICE_RUB:,.0f}".replace(',', ' ')

# Escape course title for MarkdownV2
COURSE_TITLE_ESCAPED = escape_markdown(COURSE_TITLE)

# Course Description
COURSE_DESCRIPTION = f"""
📚 *Курс для инструкторов по дрессировке\\!*

Курс посвящен исключительно БЫТОВОЙ дрессировке\\.

🕒 *Когда?*
Живые онлайн\\-лекции по средам
Старт 2 апреля в 19\\:00 по МСК

👥 *Для кого этот курс?*
Мы ждем всех \\- и опытных инструкторов, и начинающих, и тех, кто пока не решается взять первых клиентов\\!

💫 *Начинающим инструкторам:*
• Научим находить клиентов \\(и сразу начнем это практиковать\\)
• Поможем побороть неуверенность и начать работать
• Расскажем, как формировать цены на услуги
• Научим правильно общаться с разными типами клиентов
• Подробно разберем построение занятий
• Обсудим особенности работы с разными породами собак

🌟 *Опытным инструкторам:*
• Как замотивировать клиентов делать домашку?
• Как удержать клиентов на долгий срок?
• Как сделать занятия интереснее?
• Что делать с выгоранием?
• Как перестать унывать от «бытовухи»?
И много других актуальных вопросов\\!

📋 *Что входит в курс:*
• 7 недель обучения
• 8 живых лекций с записью
• Можно задавать вопросы прямо во время лекций
• Практические задания
• Разбор ваших личных кейсов
• Чат участников в телеграме
• Записи лекций и учебные материалы
• Домашние задания
• Подробные инструкции по воспитанию собак
• Список упражнений и лайфхаков для работы

✨ *Важно\\!* Доступ к курсу остается у вас навсегда\\!"""

#Reviews
REVIEWS_MESSAGE = "Отзывы моих учеников 🌟"
NO_REVIEWS_MESSAGE = "No reviews avaliable at the moment\\."

# Lecturer Information
LECTURER_INFO = """
👨‍🏫 *О ведущей курса*

*Ведущая курса:* Анна Калыпина
*Стаж дрессировки собак:* 15 лет

*Инструктор по дрессировке РКФ \\(ОКД, ЗКС, ВН\\)\\. \\- личный лист 10190\\.
Инструктор по служебной кинологии ДОСААФ\\.*

*Спортсмен ОКД, ЗКС Мониторинг, ноузворк и бытовой поиск\\.*

📱 *Социальные сети:*
• [VK](https://vk.com/annakalypina)
• [Telegram канал](https://t.me/prosto_pro_sobak)
• [Профиль на Профи\\.ру](https://spb.profi.ru/profile/KalypinaAV2/)

Подпишитесь, чтобы быть в курсе последних новостей и советов по дрессировке\\!"""

# Contact messages

CONTACT_MESSAGE = "✨ С радостью отвечу на все ваши вопросы: @Kalypina"

# Menu Buttons
MENU_ABOUT_COURSE = "📚 Подробнее о курсе"
MENU_ABOUT_LECTURER = "👨‍🏫 О ведущей курса"
MENU_PURCHASE = "💳 Купить"
MENU_ACCESS = "🎓 Доступ к курсу"
MENU_REVIEWS = "💬 Отзывы"
MENU_CONTACT = "👩‍💼 Задать вопрос"
BACK_BUTTON = "🔙 Назад"
CANCEL_BUTTON = "🔙 Отмена"
WRITE_BUTTON = "✍️ Написать"

# Welcome Messages
WELCOME_NEW = f"""
Добро пожаловать в меню покупки курса\\! 🎓

📋 Краткая информация о курсе:
• Онлайн\\-курс для инструкторов по бытовой дрессировке
• Старт 2 апреля в 19:00 МСК
• 7 недель обучения \\(8 живых лекций\\)

*Цена: {escape_markdown(COURSE_PRICE_STR)} рублей*

Выберите опцию из меню ниже:"""

WELCOME_BACK = f"""
С возвращением в меню покупки курса\\! 🎓

📋 Напоминаем о курсе:
• Онлайн\\-курс для инструкторов по бытовой дрессировке
• Старт 2 апреля в 19:00 МСК
• 7 недель обучения с записью лекций

*Цена: {escape_markdown(COURSE_PRICE_STR)} рублей*

Выберите опцию из меню ниже:"""

# Payment Flow Messages
PAYMENT_EMAIL_REQUEST = """
Для оформления покупки нам потребуется некоторая информация\\.
Пожалуйста, введите ваш email:"""

PAYMENT_EMAIL_INVALID = """
❌ Некорректный формат email\\.
Пожалуйста, введите email в правильном формате \\(например: example@domain\\.com\\):"""

PAYMENT_EMAIL_THANKS = """
Спасибо\\! А теперь, пожалуйста, введите ваше полное имя:"""

PAYMENT_INFO_REQUEST = """
Для продолжения, пожалуйста, введите ваше полное имя:"""

PAYMENT_PHONE_REQUEST = """
Отлично\\! Теперь, пожалуйста, предоставьте ваш номер телефона\\.
Вы можете нажать кнопку «📱 Отправить номер телефона» или ввести его вручную в формате \\+79211234567:"""

PAYMENT_INFO_THANKS = """
Спасибо за предоставленную информацию\\! Подготавливаем счет\\.\\.\\."""

PAYMENT_ERROR = f"""
Извините, произошла ошибка при оформлении покупки курса «{COURSE_TITLE_ESCAPED}»\\. 
Пожалуйста, попробуйте позже\\."""

PAYMENT_CANCELLED = f"""
Процесс оплаты курса «{COURSE_TITLE_ESCAPED}» отменен\\."""

# Access Messages
ALREADY_PURCHASED = f"""
Вы уже приобрели курс «{COURSE_TITLE_ESCAPED}»\\!

🎓 Доступ к чату для студентов

Вот ваша пригласительная ссылка: {{invite_link}}

Вы можете использовать эту ссылку, чтобы снова присоединиться к чату в любое время\\."""

ACCESS_SUCCESS = f"""
✅ Вы успешно приобрели курс «{COURSE_TITLE_ESCAPED}»\\!

🎓 *Доступ к чату для студентов*
Вот ваша пригласительная ссылка: {{invite_link}}

Вы можете использовать эту ссылку, чтобы снова присоединиться к чату в любое время\\."""

ACCESS_SUCCESS_NO_LINK = f"""
✅ Вы успешно приобрели курс «{COURSE_TITLE_ESCAPED}»\\!

❗ Однако возникла проблема с вашей пригласительной ссылкой\\.
Пожалуйста, обратитесь в службу поддержки\\."""

ACCESS_NOT_PURCHASED = f"""
Вы еще не приобрели курс «{COURSE_TITLE_ESCAPED}»\\.
*Стоимость курса: {{course_price}} рублей\\.*
Используйте опцию 💳 Купить в главном меню, чтобы получить доступ\\."""

MENU_UPDATED = """
Меню обновлено с учетом вашей покупки\\!
Используйте кнопку «🎓 Доступ к курсу» для получения ссылки на чат\\."""

# Help Message
HELP_TEXT = f"""
*Доступные команды:*
/start \\- Запустить бота и показать главное меню
/help \\- Показать это справочное сообщение
/access \\- Проверить статус доступа к курсу

*Опции меню:*
• 📚 Подробнее о курсе \\- Просмотр подробной информации о курсе
• 👨‍🏫 О ведущей курса \\- Узнать о преподавателе
• 💳 Купить \\- Приобрести курс \\(*{escape_markdown(COURSE_PRICE_STR)} руб\\.*\\)

Нужна помощь? Свяжитесь с нами: \\[контактная информация\\]"""

# Payment Success Messages
ACCESS_PAYMENT_SUCCESS = """
🎉 Спасибо за покупку\\!

Ваша транзакция успешно завершена\\.
ID транзакции: `{transaction_id}`

🎓 *Доступ к материалам курса*
Вот ваша постоянная ссылка для входа в чат студентов:
{invite_link}

Сохраните эту ссылку \\- вы можете использовать её, чтобы повторно присоединиться к чату при необходимости\\.

Если у вас возникли проблемы с доступом к чату, пожалуйста, обратитесь в службу поддержки\\."""

ACCESS_PAYMENT_SUCCESS_NO_LINK = """
🎉 Спасибо за покупку\\!

Ваша транзакция успешно завершена\\.
ID транзакции: `{transaction_id}`

❗ Возникла проблема с генерацией пригласительной ссылки\\.
Наша служба поддержки свяжется с вами в ближайшее время для предоставления доступа\\.
Приносим извинения за доставленные неудобства\\."""

# Error Messages
GENERAL_ERROR = """Извините, что\\-то пошло не так\\. Пожалуйста, попробуйте позже\\."""
