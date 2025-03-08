"""
Telegram Bot for Course Sales and Management
Created by RainZerg on 2025-03-08 12:51:28 UTC
"""

import logging
import re
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
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
    BACK_BUTTON, CANCEL_BUTTON,
    WELCOME_NEW, WELCOME_BACK,
    PAYMENT_EMAIL_REQUEST, PAYMENT_EMAIL_INVALID, PAYMENT_EMAIL_THANKS, PAYMENT_INFO_REQUEST, 
    PAYMENT_PHONE_REQUEST, PAYMENT_INFO_THANKS, PAYMENT_ERROR, PAYMENT_CANCELLED,
    ALREADY_PURCHASED, ACCESS_SUCCESS, ACCESS_SUCCESS_NO_LINK,
    ACCESS_NOT_PURCHASED, HELP_TEXT, GENERAL_ERROR,
    COURSE_DESCRIPTION, LECTURER_INFO, MENU_UPDATED,
    ACCESS_PAYMENT_SUCCESS, ACCESS_PAYMENT_SUCCESS_NO_LINK,
    escape_markdown
)
from payment_handler import PaymentHandler, CustomerInfo

# States for conversation handler
AWAITING_EMAIL = 1
AWAITING_NAME = 2
AWAITING_PHONE = 3

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def handle_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle successful payment"""
    user_id = update.effective_user.id
    transaction_id = update.message.successful_payment.provider_payment_charge_id

    try:
        # Generate invite link - pass both user_id and context
        invite_link = await payment_handler.create_invite_link(user_id, context)
        
        if invite_link:
            escaped_link = escape_markdown(invite_link)
            await update.message.reply_text(
                text_constants.ACCESS_PAYMENT_SUCCESS.format(
                    transaction_id=transaction_id,
                    invite_link=escaped_link
                ),
                parse_mode='MarkdownV2'
            )
        else:
            await update.message.reply_text(
                text_constants.ACCESS_PAYMENT_SUCCESS_NO_LINK.format(
                    transaction_id=transaction_id
                ),
                parse_mode='MarkdownV2'
            )

        # Update keyboard immediately after successful payment
        keyboard = await get_start_keyboard(user_id)
        await update.message.reply_text(
            text_constants.MENU_UPDATED,
            parse_mode='MarkdownV2',
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error in successful payment handler: {e}")
        await update.message.reply_text(text_constants.GENERAL_ERROR)

# Initialize payment handler with custom successful payment handler
payment_handler = PaymentHandler(
    provider_token=config.PROVIDER_TOKEN,
    currency=config.CURRENCY,
    students_chat_id=config.STUDENTS_CHAT_ID,
    handle_successful_payment=handle_successful_payment
)

async def get_start_keyboard(user_id: int):
    """Creates the main menu keyboard based on user's access status"""
    has_paid, _ = await payment_handler.get_access_status(user_id)

    keyboard = [
        [KeyboardButton(MENU_ABOUT_COURSE)],
        [KeyboardButton(MENU_ABOUT_LECTURER)],
        [KeyboardButton(MENU_ACCESS if has_paid else MENU_PURCHASE)]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_button():
    """Creates an inline keyboard with just a back button"""
    keyboard = [[InlineKeyboardButton(BACK_BUTTON, callback_data="start")]]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command"""
    try:
        # Get user-specific keyboard
        keyboard = await get_start_keyboard(update.effective_user.id)

        if not config.COVER_IMAGE_PATH.exists():
            logger.warning("Cover image not found. Sending text-only message.")
            await update.message.reply_text(
                WELCOME_NEW,
                parse_mode='MarkdownV2',
                reply_markup=keyboard
            )
            return

        await update.message.reply_photo(
            photo=open(config.COVER_IMAGE_PATH, 'rb'),
            caption=WELCOME_NEW,
            parse_mode='MarkdownV2',
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text(GENERAL_ERROR)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for text messages"""
    try:
        message_text = update.message.text
        user_id = update.effective_user.id

        if message_text == MENU_ABOUT_COURSE:
            await update.message.reply_text(
                COURSE_DESCRIPTION,
                parse_mode='MarkdownV2',
                reply_markup=get_back_button()
            )

        elif message_text == MENU_ABOUT_LECTURER:
            await update.message.reply_text(
                LECTURER_INFO,
                parse_mode='MarkdownV2',
                reply_markup=get_back_button()
            )

        elif message_text in [MENU_PURCHASE, MENU_ACCESS]:
            has_paid, invite_link = await payment_handler.get_access_status(user_id)

            if has_paid and message_text == MENU_ACCESS:
                # If no invite link exists, try to create one
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
                # Handle purchase button
                await start_payment(update, context)

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text(
            GENERAL_ERROR,
            reply_markup=await get_start_keyboard(user_id)
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for button callbacks"""
    query = update.callback_query
    await query.answer()

    if query.data == "start":
        try:
            keyboard = await get_start_keyboard(query.from_user.id)

            if not config.COVER_IMAGE_PATH.exists():
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=WELCOME_BACK,
                    parse_mode='MarkdownV2',
                    reply_markup=keyboard
                )
            else:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=open(config.COVER_IMAGE_PATH, 'rb'),
                    caption=WELCOME_BACK,
                    parse_mode='MarkdownV2',
                    reply_markup=keyboard
                )

            await query.message.delete()

        except Exception as e:
            logger.error(f"Error in button callback: {e}")
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=GENERAL_ERROR,
                reply_markup=await get_start_keyboard(query.from_user.id)
            )

async def start_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the payment process by requesting user email"""
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

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the email input and requests name if needed"""
    if update.message.text == CANCEL_BUTTON:
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
        # If we have the name, go straight to phone
        keyboard = [[
            KeyboardButton("📱 Отправить номер телефона", request_contact=True),
            KeyboardButton(CANCEL_BUTTON)
        ]]
        
        await update.message.reply_text(
            PAYMENT_PHONE_REQUEST,
            parse_mode='MarkdownV2',
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return AWAITING_PHONE
    else:
        # If no name, ask for it
        await update.message.reply_text(
            PAYMENT_EMAIL_THANKS,
            parse_mode='MarkdownV2'
        )
        return AWAITING_NAME

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the name input and requests phone"""
    if update.message.text == CANCEL_BUTTON:
        await start(update, context)
        return ConversationHandler.END

    full_name = update.message.text
    context.user_data['full_name'] = full_name

    # Create keyboard with phone number request button
    keyboard = [[
        KeyboardButton("📱 Отправить номер телефона", request_contact=True),
        KeyboardButton(CANCEL_BUTTON)
    ]]

    await update.message.reply_text(
        PAYMENT_PHONE_REQUEST,
        parse_mode='MarkdownV2',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return AWAITING_PHONE

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the phone input and initiates payment"""
    if update.message.text == CANCEL_BUTTON:
        await start(update, context)
        return ConversationHandler.END

    # Get phone number either from contact or text message
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text

    context.user_data['phone'] = phone
    user_id = update.effective_user.id

    # Create CustomerInfo with all required fields
    customer_info = CustomerInfo(
        full_name=context.user_data['full_name'],
        email=context.user_data['email'],
        phone=phone
    )

    await update.message.reply_text(
        PAYMENT_INFO_THANKS,
        parse_mode='MarkdownV2',
        reply_markup=await get_start_keyboard(user_id)
    )

    try:
        await payment_handler.send_invoice(
            update=update,
            context=context,
            customer_info=customer_info
        )
    except Exception as e:
        logger.error(f"Error sending invoice: {e}")
        await update.message.reply_text(
            PAYMENT_ERROR,
            parse_mode='MarkdownV2',
            reply_markup=await get_start_keyboard(user_id)
        )

    return ConversationHandler.END

async def cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the payment process"""
    user_id = update.effective_user.id
    await update.message.reply_text(
        PAYMENT_CANCELLED,
        parse_mode='MarkdownV2',
        reply_markup=await get_start_keyboard(user_id)
    )
    return ConversationHandler.END

async def check_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /access command - checks user's access status"""
    user_id = update.effective_user.id
    has_paid, invite_link = await payment_handler.get_access_status(user_id)

    try:
        if has_paid:
            # If no invite link exists, try to create one
            if not invite_link:
                invite_link = await payment_handler.create_invite_link(user_id, context)
                
            if invite_link:
                escaped_link = escape_markdown(invite_link)
                await update.message.reply_text(
                    ACCESS_SUCCESS.format(
                        invite_link=escaped_link
                    ),
                    parse_mode='MarkdownV2',
                    reply_markup=await get_start_keyboard(user_id)
                )
            else:
                await update.message.reply_text(
                    ACCESS_SUCCESS_NO_LINK,
                    parse_mode='MarkdownV2',
                    reply_markup=await get_start_keyboard(user_id)
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
                reply_markup=await get_start_keyboard(user_id)
            )
    except Exception as e:
        logger.error(f"Error sending access status message: {e}")
        await update.message.reply_text(
            "Произошла ошибка при проверке статуса. Пожалуйста, попробуйте позже.",
            reply_markup=await get_start_keyboard(user_id)
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /help command"""
    user_id = update.effective_user.id
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode='MarkdownV2',
        reply_markup=await get_start_keyboard(user_id)
    )

def main():
    """Start the bot"""
    if not config.TOKEN or not config.PROVIDER_TOKEN or not config.STUDENTS_CHAT_ID:
        logger.error("Missing required configuration!")
        return

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
                    MessageHandler(filters.CONTACT, handle_phone),  # Handle contact sharing
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)  # Handle manual input
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
        application.add_handler(MessageHandler(
            filters.SUCCESSFUL_PAYMENT, 
            handle_successful_payment  # Use our custom handler instead of payment_handler's
        ))

        # Add general message handler for menu options LAST
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & 
            ~filters.Regex(f'^({MENU_PURCHASE}|{MENU_ACCESS})$'),
            handle_message
        ))

        logger.info("Bot is starting up...")
        application.run_polling()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == '__main__':
    main()
