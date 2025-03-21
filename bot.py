"""
Telegram Bot for Course Sales and Management
Updated by RainZerg on 2025-03-21 17:19:30 UTC
"""

import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardMarkup,
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
from text_constants import (
    MENU_ABOUT_COURSE, MENU_ABOUT_LECTURER, MENU_PURCHASE, MENU_ACCESS,
    BACK_BUTTON, CANCEL_BUTTON, WRITE_BUTTON,
    WELCOME_NEW, WELCOME_BACK,
    PAYMENT_EMAIL_REQUEST, PAYMENT_EMAIL_INVALID, PAYMENT_EMAIL_THANKS, 
    PAYMENT_INFO_REQUEST, PAYMENT_PHONE_REQUEST, PAYMENT_INFO_THANKS, 
    PAYMENT_ERROR, PAYMENT_CANCELLED,
    ALREADY_PURCHASED, ACCESS_SUCCESS, ACCESS_SUCCESS_NO_LINK,
    ACCESS_NOT_PURCHASED, HELP_TEXT, GENERAL_ERROR,
    COURSE_DESCRIPTION, LECTURER_INFO, MENU_UPDATED,
    ACCESS_PAYMENT_SUCCESS, ACCESS_PAYMENT_SUCCESS_NO_LINK, 
    MENU_CONTACT, CONTACT_MESSAGE,
    escape_markdown
)
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

def cleanup_user_data(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clean up user data from context"""
    keys_to_clear = ['state', 'email', 'full_name', 'phone']
    for key in keys_to_clear:
        context.user_data.pop(key, None)

def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """Creates a keyboard with phone number request button"""
    return ReplyKeyboardMarkup([
        [
            KeyboardButton(PHONE_BUTTON_TEXT, request_contact=True),
            KeyboardButton(CANCEL_BUTTON)
        ]
    ], resize_keyboard=True)

async def handle_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle successful payment"""
    user = update.effective_user
    payment_info = update.message.successful_payment

    try:
        # First record the payment in the database
        payment_handler.db.record_payment(
            user_id=user.id,
            username=user.username,
            customer_info=context.user_data,
            transaction_id=payment_info.provider_payment_charge_id,
            amount=payment_info.total_amount / 100,
            currency=payment_info.currency
        )
        logger.info(f"Successfully recorded payment for user {user.id}")

        # Then generate invite link
        invite_link = await payment_handler.create_invite_link(user.id, context)
        
        if invite_link:
            escaped_link = escape_markdown(invite_link)
            await update.message.reply_text(
                text_constants.ACCESS_PAYMENT_SUCCESS.format(
                    transaction_id=payment_info.provider_payment_charge_id,
                    invite_link=escaped_link
                ),
                parse_mode='MarkdownV2'
            )
        else:
            await update.message.reply_text(
                text_constants.ACCESS_PAYMENT_SUCCESS_NO_LINK.format(
                    transaction_id=payment_info.provider_payment_charge_id
                ),
                parse_mode='MarkdownV2'
            )

        # Update keyboard immediately after successful payment
        keyboard = await get_start_keyboard(user.id)
        await update.message.reply_text(
            text_constants.MENU_UPDATED,
            parse_mode='MarkdownV2',
            reply_markup=keyboard
        )
        
        # Clean up user data after successful payment
        cleanup_user_data(context)

    except Exception as e:
        logger.error(f"Error in successful payment handler for user {user.id}: {e}")
        await update.message.reply_text(text_constants.GENERAL_ERROR)

# Initialize payment handler with custom successful payment handler
payment_handler = PaymentHandler(
    provider_token=config.PROVIDER_TOKEN,
    currency=config.CURRENCY,
    students_chat_id=config.STUDENTS_CHAT_ID,
    handle_successful_payment=handle_successful_payment
)

async def get_start_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Creates the main menu keyboard based on user's access status"""
    has_paid, _ = await payment_handler.get_access_status(user_id)

    keyboard = [
        [InlineKeyboardButton(MENU_ABOUT_COURSE, callback_data="about_course")],
        [InlineKeyboardButton(MENU_ABOUT_LECTURER, callback_data="about_lecturer")],
        [InlineKeyboardButton(
            MENU_ACCESS if has_paid else MENU_PURCHASE, 
            callback_data="access" if has_paid else "purchase"
        )],
        [InlineKeyboardButton(MENU_CONTACT, callback_data="contact")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_contact_buttons() -> InlineKeyboardMarkup:
    """Creates an inline keyboard with write and back buttons"""
    keyboard = [
        [InlineKeyboardButton(WRITE_BUTTON, url="https://t.me/Kalypina")],
        [InlineKeyboardButton(BACK_BUTTON, callback_data="start")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_button() -> InlineKeyboardMarkup:
    """Creates an inline keyboard with just a back button"""
    keyboard = [[InlineKeyboardButton(BACK_BUTTON, callback_data="start")]]
    return InlineKeyboardMarkup(keyboard)

async def send_photo_message(
    chat_id: int, 
    photo_path: Path, 
    caption: str, 
    keyboard: InlineKeyboardMarkup,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Helper function to send photo messages with proper resource management"""
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command"""
    user = update.effective_user
    try:
        logger.info(f"Processing /start command for user {user.id}")
        keyboard = await get_start_keyboard(user.id)

        if not config.COVER_IMAGE_PATH.exists():
            logger.warning("Cover image not found. Sending text-only message.")
            await update.message.reply_text(
                WELCOME_NEW,
                parse_mode='MarkdownV2',
                reply_markup=keyboard
            )
            return

        await send_photo_message(
            chat_id=update.effective_chat.id,
            photo_path=config.COVER_IMAGE_PATH,
            caption=WELCOME_NEW,
            keyboard=keyboard,
            context=context
        )
    except Exception as e:
        logger.error(f"Error in start command for user {user.id}: {e}")
        await update.message.reply_text(GENERAL_ERROR)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for button callbacks"""
    query = update.callback_query
    user_id = query.from_user.id
    
    logger.info(f"Processing callback '{query.data}' for user {user_id}")
    
    try:
        await query.answer()  # Answer callback query first
        
        match query.data:
            case "start":
                keyboard = await get_start_keyboard(user_id)
                if config.COVER_IMAGE_PATH.exists():
                    await send_photo_message(
                        chat_id=query.message.chat_id,
                        photo_path=config.COVER_IMAGE_PATH,
                        caption=WELCOME_BACK,
                        keyboard=keyboard,
                        context=context
                    )
                else:
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=WELCOME_BACK,
                        parse_mode='MarkdownV2',
                        reply_markup=keyboard
                    )

            case "about_course":
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=COURSE_DESCRIPTION,
                    parse_mode='MarkdownV2',
                    reply_markup=get_back_button()
                )

            case "about_lecturer":
                await send_photo_message(
                    chat_id=query.message.chat_id,
                    photo_path=config.LECTURER_IMAGE_PATH,
                    caption=LECTURER_INFO,
                    keyboard=get_back_button(),
                    context=context
                )

            case "contact":
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=CONTACT_MESSAGE,
                    reply_markup=get_contact_buttons()
                )

            case "purchase" | "access":
                has_paid, invite_link = await payment_handler.get_access_status(user_id)
                
                if has_paid and query.data == "access":
                    if not invite_link:
                        invite_link = await payment_handler.create_invite_link(user_id, context)
                    
                    escaped_link = escape_markdown(invite_link) if invite_link else None
                    text = (ALREADY_PURCHASED.format(invite_link=escaped_link) 
                           if escaped_link else ACCESS_SUCCESS_NO_LINK)
                    
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=text,
                        parse_mode='MarkdownV2',
                        reply_markup=await get_start_keyboard(user_id)
                    )
                elif not has_paid and query.data == "purchase":
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=PAYMENT_EMAIL_REQUEST,
                        parse_mode='MarkdownV2',
                        reply_markup=ReplyKeyboardMarkup(
                            [[KeyboardButton(CANCEL_BUTTON)]], 
                            resize_keyboard=True
                        )
                    )
                    context.user_data['state'] = AWAITING_EMAIL

            case _:  # default case
                logger.warning(f"Unexpected callback data: {query.data}")
                return

        # Delete the original message after handling any case
        await query.message.delete()

    except Exception as e:
        logger.error(f"Error in button callback for user {user_id}: {e}")
        try:
            await query.answer()  # Ensure callback is answered even on error
        except Exception:
            pass  # Ignore if we can't answer the callback
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=GENERAL_ERROR,
            reply_markup=await get_start_keyboard(user_id)
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for text messages"""
    user = update.effective_user
    try:
        message_text = update.message.text
        user_id = user.id

        if message_text == MENU_ABOUT_COURSE:
            await update.message.reply_text(
                COURSE_DESCRIPTION,
                parse_mode='MarkdownV2',
                reply_markup=get_back_button()
            )

        elif message_text == MENU_ABOUT_LECTURER:
            await send_photo_message(
                chat_id=update.effective_chat.id,
                photo_path=config.LECTURER_IMAGE_PATH,
                caption=LECTURER_INFO,
                keyboard=get_back_button(),
                context=context
            )
        
        elif message_text == MENU_CONTACT:
            await update.message.reply_text(
                CONTACT_MESSAGE,
                reply_markup=get_contact_buttons()
            )

        elif message_text in [MENU_PURCHASE, MENU_ACCESS]:
            has_paid, invite_link = await payment_handler.get_access_status(user_id)

            if has_paid and message_text == MENU_ACCESS:
                if not invite_link:
                    invite_link = await payment_handler.create_invite_link(user_id, context)

                escaped_link = escape_markdown(invite_link) if invite_link else None
                if escaped_link:
                    await update.message.reply_text(
                        ALREADY_PURCHASED.format(invite_link=escaped_link),
                        parse_mode='MarkdownV2',
                        reply_markup=await get_start_keyboard(user_id)
                    )
                else:
                    await update.message.reply_text(
                        ACCESS_SUCCESS_NO_LINK,
                        parse_mode='MarkdownV2',
                        reply_markup=await get_start_keyboard(user_id)
                    )
            elif not has_paid and message_text == MENU_PURCHASE:
                await start_payment(update, context)

    except Exception as e:
        logger.error(f"Error handling message for user {user.id}: {e}")
        await update.message.reply_text(
            GENERAL_ERROR,
            reply_markup=await get_start_keyboard(user.id)
        )

async def start_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the payment process by requesting user email"""
    user = update.effective_user
    try:
        # Get user's full name from chat
        first_name = update.message.chat.first_name or ""
        last_name = update.message.chat.last_name or ""
        full_name = f"{first_name} {last_name}".strip()
        
        # Store the name if available
        if full_name:
            context.user_data['full_name'] = full_name
        
        # Always request email first
        await update.message.reply_text(
            PAYMENT_EMAIL_REQUEST,
            parse_mode='MarkdownV2',
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton(CANCEL_BUTTON)]], resize_keyboard=True)
        )
        return AWAITING_EMAIL
    except Exception as e:
        logger.error(f"Error starting payment for user {user.id}: {e}")
        await update.message.reply_text(GENERAL_ERROR)
        return ConversationHandler.END

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the email input and requests name if needed"""
    user = update.effective_user
    
    if update.message.text == CANCEL_BUTTON:
        cleanup_user_data(context)
        await start(update, context)
        return ConversationHandler.END
        
    email = update.message.text.strip()
    
    # Email validation using regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        await update.message.reply_text(
            PAYMENT_EMAIL_INVALID,
            parse_mode='MarkdownV2'
        )
        return AWAITING_EMAIL
    
    context.user_data['email'] = email

    # Check if we already have the name from Telegram profile
    if 'full_name' in context.user_data:
        await update.message.reply_text(
            PAYMENT_PHONE_REQUEST,
            parse_mode='MarkdownV2',
            reply_markup=get_phone_keyboard()
        )
        return AWAITING_PHONE
    else:
        await update.message.reply_text(
            PAYMENT_EMAIL_THANKS,
            parse_mode='MarkdownV2'
        )
        return AWAITING_NAME

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the name input and requests phone"""
    if update.message.text == CANCEL_BUTTON:
        cleanup_user_data(context)
        await start(update, context)
        return ConversationHandler.END

    context.user_data['full_name'] = update.message.text

    await update.message.reply_text(
        PAYMENT_PHONE_REQUEST,
        parse_mode='MarkdownV2',
        reply_markup=get_phone_keyboard()
    )
    return AWAITING_PHONE

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the phone input and initiates payment"""
    user = update.effective_user
    
    try:
        if update.message.text == CANCEL_BUTTON:
            cleanup_user_data(context)
            await start(update, context)
            return ConversationHandler.END

        # Get phone number either from contact or text message
        phone = update.message.contact.phone_number if update.message.contact else update.message.text

        # Verify all required data is present
        required_fields = ['full_name', 'email']
        missing_fields = [field for field in required_fields if field not in context.user_data]
        
        if missing_fields:
            logger.error(f"Missing required fields for user {user.id}: {missing_fields}")
            raise ValueError(f"Missing required customer info: {', '.join(missing_fields)}")

        context.user_data['phone'] = phone

        # Create CustomerInfo with all required fields
        customer_info = CustomerInfo(
            full_name=context.user_data['full_name'],
            email=context.user_data['email'],
            phone=phone
        )

        await update.message.reply_text(
            PAYMENT_INFO_THANKS,
            parse_mode='MarkdownV2',
            reply_markup=await get_start_keyboard(user.id)
        )

        await payment_handler.send_invoice(
            update=update,
            context=context,
            customer_info=customer_info
        )
        
        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error handling phone input for user {user.id}: {e}")
        cleanup_user_data(context)
        await update.message.reply_text(
            PAYMENT_ERROR,
            parse_mode='MarkdownV2',
            reply_markup=await get_start_keyboard(user.id)
        )
        return ConversationHandler.END

async def cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the payment process"""
    user = update.effective_user
    cleanup_user_data(context)
    await update.message.reply_text(
        PAYMENT_CANCELLED,
        parse_mode='MarkdownV2',
        reply_markup=await get_start_keyboard(user.id)
    )
    return ConversationHandler.END

async def check_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /access command - checks user's access status"""
    user = update.effective_user
    
    try:
        has_paid, invite_link = await payment_handler.get_access_status(user.id)

        if has_paid:
            if not invite_link:
                invite_link = await payment_handler.create_invite_link(user.id, context)
                
            if invite_link:
                escaped_link = escape_markdown(invite_link)
                await update.message.reply_text(
                    ACCESS_SUCCESS.format(invite_link=escaped_link),
                    parse_mode='MarkdownV2',
                    reply_markup=await get_start_keyboard(user.id)
                )
            else:
                await update.message.reply_text(
                    ACCESS_SUCCESS_NO_LINK,
                    parse_mode='MarkdownV2',
                    reply_markup=await get_start_keyboard(user.id)
                )
        else:
            price_str = escape_markdown(
                f"{config.COURSE_PRICE / 100:,.0f}".replace(',', ' ')
            )

            await update.message.reply_text(
                ACCESS_NOT_PURCHASED.format(
                    course_title=text_constants.COURSE_TITLE_ESCAPED,
                    course_price=price_str
                ),
                parse_mode='MarkdownV2',
                reply_markup=await get_start_keyboard(user.id)
            )
    except Exception as e:
        logger.error(f"Error checking access for user {user.id}: {e}")
        await update.message.reply_text(
            GENERAL_ERROR,
            reply_markup=await get_start_keyboard(user.id)
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /help command"""
    user = update.effective_user
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode='MarkdownV2',
        reply_markup=await get_start_keyboard(user.id)
    )

def main():
    """Main function to start the bot"""
    try:
        application = Application.builder().token(config.TOKEN).build()

        # Add callback query handler for inline buttons FIRST
        application.add_handler(CallbackQueryHandler(button_callback))

        # Add command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("access", check_access))

        # Add payment conversation handler
        payment_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex(f'^{MENU_PURCHASE}$'), start_payment)],
            states={
                AWAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)],
                AWAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
                AWAITING_PHONE: [
                    MessageHandler(filters.CONTACT, handle_phone),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)
                ],
            },
            fallbacks=[
                CommandHandler('cancel', cancel_payment),
                MessageHandler(filters.Regex(f'^{CANCEL_BUTTON}$'), cancel_payment)
            ]
        )

        # Add payment handlers
        application.add_handler(payment_conv_handler)
        application.add_handler(PreCheckoutQueryHandler(payment_handler.handle_pre_checkout_query))
        application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, handle_successful_payment))
        
        # Add handler for menu buttons BEFORE the general message handler
        application.add_handler(MessageHandler(
            filters.Regex(f'^({MENU_PURCHASE}|{MENU_ACCESS}|{MENU_ABOUT_COURSE}|{MENU_ABOUT_LECTURER})$'),
            handle_message
        ))

        # Add general message handler for all other text messages LAST
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        ))

        logger.info("Bot is starting up...")
        application.run_polling()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == '__main__':
    main()
