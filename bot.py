"""
Telegram Bot for Course Sales and Management
Updated by RainZerg on 2025-03-24 12:55:43 UTC
"""

import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    InputMediaPhoto,
    KeyboardButton, 
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Contact
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler,
    PreCheckoutQueryHandler,
    ContextTypes, 
    filters,
    ConversationHandler
)
import config
import text_constants
from text_constants import *
from payment_handler import PaymentHandler, CustomerInfo

# States for conversation handler
AWAITING_EMAIL = 1
AWAITING_NAME = 2
AWAITING_PHONE = 3

# Constants
PHONE_BUTTON_TEXT = "📱 Отправить номер телефона"

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class BotHandlers:
    """Centralized class for bot handlers and utilities"""
    
    def __init__(self, payment_handler: PaymentHandler):
        self.payment_handler = payment_handler

    async def handle_access_check(self, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> Tuple[bool, Optional[str]]:
        """Centralized access checking logic"""
        has_paid, invite_link = await self.payment_handler.get_access_status(user_id)
        if not invite_link and has_paid:
            invite_link = await self.payment_handler.create_invite_link(user_id, context)
        return has_paid, invite_link

    async def generate_access_response(self, has_paid: bool, invite_link: Optional[str] = None) -> Tuple[str, InlineKeyboardMarkup]:
        """Centralized response generation for access checks"""
        if has_paid:
            escaped_link = escape_markdown(invite_link) if invite_link else None
            text = (ACCESS_SUCCESS.format(invite_link=escaped_link) 
                   if escaped_link else ACCESS_SUCCESS_NO_LINK)
        else:
            price_str = escape_markdown(f"{config.COURSE_PRICE / 100:,.0f}".replace(',', ' '))
            text = ACCESS_NOT_PURCHASED.format(
                course_title=text_constants.COURSE_TITLE_ESCAPED,
                course_price=price_str
            )
        keyboard = await self.get_start_keyboard(has_paid)
        return text, keyboard

    @staticmethod
    def cleanup_user_data(context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clean up user data from context"""
        keys_to_clear = ['state', 'email', 'full_name', 'phone', 'awaiting_custom_name', 'awaiting_manual_phone']
        for key in keys_to_clear:
            context.user_data.pop(key, None)

    @staticmethod
    def get_phone_keyboard() -> ReplyKeyboardMarkup:
        """Creates a reply keyboard with phone number request button"""
        return ReplyKeyboardMarkup([
            [KeyboardButton(PHONE_BUTTON_TEXT, request_contact=True)],
            [KeyboardButton("📝 Ввести номер вручную")],
            [KeyboardButton(CANCEL_BUTTON)]
        ], resize_keyboard=True)

    @staticmethod
    def get_cancel_keyboard() -> InlineKeyboardMarkup:
        """Creates an inline keyboard with cancel button"""
        return InlineKeyboardMarkup([[
            InlineKeyboardButton(CANCEL_BUTTON, callback_data="cancel_payment")
        ]])

    @staticmethod
    def get_back_button() -> InlineKeyboardMarkup:
        """Creates an inline keyboard with back button"""
        return InlineKeyboardMarkup([[
            InlineKeyboardButton(BACK_BUTTON, callback_data="start")
        ]])

    @staticmethod
    def get_contact_buttons() -> InlineKeyboardMarkup:
        """Creates contact buttons"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(WRITE_BUTTON, url="https://t.me/Kalypina")],
            [InlineKeyboardButton(BACK_BUTTON, callback_data="start")]
        ])

    async def get_start_keyboard(self, has_paid: bool) -> InlineKeyboardMarkup:
        """Creates the main menu keyboard based on user's access status"""
        keyboard = [
            [InlineKeyboardButton(MENU_ABOUT_COURSE, callback_data="about_course")],
            [InlineKeyboardButton(MENU_ABOUT_LECTURER, callback_data="about_lecturer")],
            [InlineKeyboardButton(
                MENU_ACCESS if has_paid else MENU_PURCHASE, 
                callback_data="access" if has_paid else "purchase"
            )],
            [InlineKeyboardButton(MENU_REVIEWS, callback_data="reviews")],
            [InlineKeyboardButton(MENU_CONTACT, callback_data="contact")]
        ]
        return InlineKeyboardMarkup(keyboard)

    async def send_photo_message(
        self,
        chat_id: int, 
        photo_path: Path, 
        caption: str, 
        keyboard: InlineKeyboardMarkup,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Helper function to send photo messages"""
        try:
            with open(photo_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=caption,
                    parse_mode='MarkdownV2',
                    reply_markup=keyboard
                )
        except FileNotFoundError:
            logger.error(f"Photo not found: {photo_path}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=caption,
                parse_mode='MarkdownV2',
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error sending photo message: {e}")
            raise

    async def handle_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handler for processing email input"""
        email = update.message.text.strip()
        
        # Basic email validation using regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            await update.message.reply_text(
                text=PAYMENT_EMAIL_INVALID,
                parse_mode='MarkdownV2',
                reply_markup=self.get_cancel_keyboard()
            )
            return AWAITING_EMAIL
        
        # Store email in user data
        context.user_data['email'] = email
        
        # Get user's full name from Telegram
        user = update.effective_user
        full_name = f"{user.first_name} {user.last_name if user.last_name else ''}"
        
        # Create keyboard with options
        keyboard = [
            [KeyboardButton(f"✅ Использовать имя из профиля: {full_name}")],
            [KeyboardButton("📝 Ввести другое имя")],
            [KeyboardButton(CANCEL_BUTTON)]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            text=USE_PROFILE_NAME_REQUEST.format(full_name=full_name),
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
        
        return AWAITING_NAME

    async def handle_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handler for processing full name input"""
        message_text = update.message.text.strip()
        
        # If user chose to use profile name
        if message_text.startswith("✅ Использовать имя из профиля:"):
            user = update.effective_user
            full_name = f"{user.first_name} {user.last_name if user.last_name else ''}"
            context.user_data['full_name'] = full_name
            return await self.request_phone(update, context)
        
        # If user wants to enter different name
        if message_text == "📝 Ввести другое имя":
            await update.message.reply_text(
                text=PAYMENT_NAME_REQUEST,
                parse_mode='MarkdownV2',
                reply_markup=self.get_cancel_keyboard()
            )
            context.user_data['awaiting_custom_name'] = True
            return AWAITING_NAME
        
        # If user is entering custom name
        if context.user_data.get('awaiting_custom_name'):
            context.user_data['full_name'] = message_text
            context.user_data.pop('awaiting_custom_name', None)
            return await self.request_phone(update, context)
        
        return AWAITING_NAME

    async def request_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Request phone number with options"""
        keyboard = [
            [KeyboardButton(PHONE_BUTTON_TEXT, request_contact=True)],
            [KeyboardButton("📝 Ввести номер вручную")],
            [KeyboardButton(CANCEL_BUTTON)]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            text=PAYMENT_PHONE_REQUEST,
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
        
        return AWAITING_PHONE

    async def handle_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handler for processing phone number input"""
        message_text = update.message.text.strip() if update.message.text else None
        
        if message_text == "📝 Ввести номер вручную":
            await update.message.reply_text(
                text=PAYMENT_PHONE_MANUAL_REQUEST,
                parse_mode='MarkdownV2',
                reply_markup=self.get_cancel_keyboard()
            )
            context.user_data['awaiting_manual_phone'] = True
            return AWAITING_PHONE
        
        if update.message.contact:
            phone = update.message.contact.phone_number
        elif context.user_data.get('awaiting_manual_phone'):
            phone = message_text
        else:
            return AWAITING_PHONE
        
        # Basic phone validation
        phone_pattern = r'^\+?[1-9]\d{1,14}$'
        if not re.match(phone_pattern, phone):
            await update.message.reply_text(
                text=PAYMENT_PHONE_INVALID,
                parse_mode='MarkdownV2',
                reply_markup=self.get_phone_keyboard()
            )
            return AWAITING_PHONE
        
        context.user_data['phone'] = phone
        context.user_data.pop('awaiting_manual_phone', None)
        
        # Thank the user and prepare invoice
        await update.message.reply_text(
            text=PAYMENT_INFO_THANKS,
            parse_mode='MarkdownV2',
            reply_markup=ReplyKeyboardRemove()
        )
        
        # Create customer info object
        customer_info = CustomerInfo(
            full_name=context.user_data['full_name'],
            email=context.user_data['email'],
            phone=context.user_data['phone']
        )
        
        # Send invoice
        try:
            await self.payment_handler.send_invoice(update, context, customer_info)
        except Exception as e:
            logger.error(f"Error sending invoice: {e}")
            await update.message.reply_text(
                text=PAYMENT_ERROR,
                parse_mode='MarkdownV2'
            )
        
        return ConversationHandler.END

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /start command and start callback"""
        user_id = update.effective_user.id
        has_paid, _ = await self.payment_handler.get_access_status(user_id)
        keyboard = await self.get_start_keyboard(has_paid)
        
        try:
            if config.COVER_IMAGE_PATH.exists():
                await self.send_photo_message(
                    chat_id=update.effective_chat.id,
                    photo_path=config.COVER_IMAGE_PATH,
                    caption=WELCOME_BACK if context.user_data.get('seen_start') else WELCOME_NEW,
                    keyboard=keyboard,
                    context=context
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=WELCOME_BACK if context.user_data.get('seen_start') else WELCOME_NEW,
                    parse_mode='MarkdownV2',
                    reply_markup=keyboard
                )
            context.user_data['seen_start'] = True
            
        except Exception as e:
            logger.error(f"Error in start handler for user {user_id}: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=GENERAL_ERROR,
                reply_markup=keyboard
            )

    async def handle_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
        """Unified handler for button callbacks"""
        query = update.callback_query
        user_id = query.from_user.id
        try:
            await query.answer()

            match query.data:
                case "start":
                    await self.handle_start(update, context)
                case "cancel_payment":
                    self.cleanup_user_data(context)
                    await query.message.delete()
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=PAYMENT_CANCELLED,
                        parse_mode='MarkdownV2',
                        reply_markup=ReplyKeyboardRemove()
                    )
                    await self.handle_start(update, context)
                    return ConversationHandler.END
                case "about_course" | "about_lecturer" | "contact" | "reviews":
                    await self.handle_info_request(update, context, query.data)
                case "access":
                    await self.handle_access_request(update, context)
                case "purchase":
                    self.cleanup_user_data(context)
                    await query.message.reply_text(
                        PAYMENT_EMAIL_REQUEST,
                        parse_mode='MarkdownV2',
                        reply_markup=self.get_cancel_keyboard()
                    )
                    await query.message.delete()
                    return AWAITING_EMAIL
                case _:
                    pass

            await query.message.delete()
        except Exception as e:
            logger.error(f"Error in button handler for user {user_id}: {e}")
            keyboard = await self.get_start_keyboard(False)
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=GENERAL_ERROR,
                reply_markup=keyboard
            )

    async def handle_info_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, info_type: str) -> None:
        """Handler for information requests (about course, lecturer, contact)"""
        chat_id = update.effective_chat.id
        
        match info_type:
            case "about_course":
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=COURSE_DESCRIPTION,
                    parse_mode='MarkdownV2',
                    reply_markup=self.get_back_button()
                )
            
            case "about_lecturer":
                await self.send_photo_message(
                    chat_id=chat_id,
                    photo_path=config.LECTURER_IMAGE_PATH,
                    caption=LECTURER_INFO,
                    keyboard=self.get_back_button(),
                    context=context
                )
            
            case "contact":
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=CONTACT_MESSAGE,
                    reply_markup=self.get_contact_buttons()
                )
            case "reviews":
                media_group = []
                try:
                    reviews_path = config.REVIEWS_PATH
                    for review_file in reviews_path.glob('*.jpg'):
                            with open(review_file, 'rb') as photo:
                                media_group.append(InputMediaPhoto(media=photo))
                    if media_group:
                            await context.bot.send_media_group(
                                chat_id=chat_id,
                                media=media_group
                            )
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=REVIEWS_MESSAGE,
                                parse_mode='MarkdownV2',
                                reply_markup=self.get_back_button()
                            )
                    else:
                        await context.bot.send_message(
                                chat_id=chat_id,
                                text=NO_REVIEWS_MESSAGE,
                                parse_mode='MarkdownV2',
                                reply_markup=self.get_back_button()
                            )
                except Exception as e:
                        logger.error(f"Error sending reviews: {e}")
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=GENERAL_ERROR,
                            reply_markup=self.get_back_button()
                        )
            case _:
                await self.handle_start(update, context)

    async def handle_access_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Only handles access checks, payment is handled by conversation"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        has_paid, invite_link = await self.handle_access_check(user_id, context)
        text, keyboard = await self.generate_access_response(has_paid, invite_link)
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode='MarkdownV2',
            reply_markup=keyboard
        )

    async def handle_successful_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for successful payments"""
        user = update.effective_user
        payment_info = update.message.successful_payment

        try:
            self.payment_handler.db.record_payment(
                user_id=user.id,
                username=user.username,
                customer_info=context.user_data,
                transaction_id=payment_info.provider_payment_charge_id,
                amount=payment_info.total_amount / 100,
                currency=payment_info.currency
            )
            
            invite_link = await self.payment_handler.create_invite_link(user.id, context)
            text, keyboard = await self.generate_access_response(True, invite_link)
            
            await update.message.reply_text(
                text=text,
                parse_mode='MarkdownV2',
                reply_markup=keyboard
            )
            
            self.cleanup_user_data(context)
            
        except Exception as e:
            logger.error(f"Error in payment handler for user {user.id}: {e}")
            await update.message.reply_text(GENERAL_ERROR)

def main():
    """Main function to start the bot"""
    try:
        # Initialize bot handlers
        payment_handler = PaymentHandler(
            provider_token=config.PROVIDER_TOKEN,
            currency=config.CURRENCY,
            students_chat_id=config.STUDENTS_CHAT_ID
        )
        handlers = BotHandlers(payment_handler)
        
        # Build application
        application = Application.builder().token(config.TOKEN).build()

        # Add handlers

        application.add_handler(CommandHandler("start", handlers.handle_start))
        application.add_handler(CommandHandler("help", lambda u, c: u.message.reply_text(
            HELP_TEXT, parse_mode='MarkdownV2'
        )))
        
        # Add payment conversation handler
        payment_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(handlers.handle_button, pattern="^purchase$")
            ],
            states={
                AWAITING_EMAIL: [
                    CallbackQueryHandler(handlers.handle_button, pattern="^cancel_payment$"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_email)
                ],
                AWAITING_NAME: [
                    CallbackQueryHandler(handlers.handle_button, pattern="^cancel_payment$"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_name)
                ],
                AWAITING_PHONE: [
                    CallbackQueryHandler(handlers.handle_button, pattern="^cancel_payment$"),
                    MessageHandler(
                        filters.CONTACT | (filters.TEXT & ~filters.COMMAND),
                        handlers.handle_phone
                    )
                ],
            },
            fallbacks=[CommandHandler('cancel', lambda u, c: handlers.cleanup_user_data(c))]
        )

        # Add payment handlers
        application.add_handler(payment_conv_handler)
        application.add_handler(CallbackQueryHandler(handlers.handle_button))
        application.add_handler(PreCheckoutQueryHandler(payment_handler.handle_pre_checkout_query))
        application.add_handler(MessageHandler(
            filters.SUCCESSFUL_PAYMENT,
            handlers.handle_successful_payment
        ))

        logger.info("Bot is starting up...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == '__main__':
    main()
