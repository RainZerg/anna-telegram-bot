"""
Payment Handler for Course Sales Bot
Created by RainZerg on 2025-03-08 12:56:07 UTC
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, Callable
import logging
from telegram import LabeledPrice, Update, ChatInviteLink
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from database import Database
import config
from text_constants import (
    COURSE_DESCRIPTION,
    COURSE_TITLE,
    ACCESS_PAYMENT_SUCCESS,
    ACCESS_PAYMENT_SUCCESS_NO_LINK,
    escape_markdown
)

logger = logging.getLogger(__name__)

@dataclass
class CustomerInfo:
    full_name: str
    email: str
    phone: Optional[str] = None
    inn: Optional[str] = None

class PaymentHandler:
    def __init__(
        self, 
        provider_token: str, 
        currency: str, 
        students_chat_id: str,
        handle_successful_payment: Optional[Callable] = None
    ):
        self.provider_token = provider_token
        self.currency = currency
        self.students_chat_id = students_chat_id
        self.db = Database()
        self._custom_payment_handler = handle_successful_payment

    def create_invoice_payload(self, 
                             chat_id: int, 
                             title: str,
                             description: str,
                             amount: int,
                             customer_info: CustomerInfo) -> Dict[str, Any]:
        """Creates a complete invoice payload with fiscalization data"""

        return {
            "chat_id": chat_id,
            "title": title,
            "description": description,
            "payload": f"course_payment_{chat_id}",
            "provider_token": self.provider_token,
            "currency": self.currency,
            "need_email": True,
            "send_email_to_provider": True,
            "prices": [LabeledPrice(label="К оплате", amount=amount)],
            "start_parameter": "course_purchase",
            "provider_data": {
                "receipt": {
                    "customer": {
                        "full_name": customer_info.full_name,
                        "email": customer_info.email,
                        "phone": customer_info.phone
                    },
                    "items": [
                        {
                            "description": title,
                            "quantity": 1,
                            "amount": {
                                "value": amount / 100,  # Convert kopeks to rubles
                                "currency": self.currency
                            },
                            "vat_code": config.VAT_CODE,
                            "payment_mode": "full_payment",
                            "payment_subject": "commodity"
                        }
                    ],
                    "tax_system_code": config.TAX_SYSTEM_CODE
                }
            }
        }

    async def send_invoice(self, 
                          update: Update, 
                          context: ContextTypes.DEFAULT_TYPE,
                          customer_info: CustomerInfo):
        """Sends an invoice to the user"""
        chat_id = update.effective_chat.id

        invoice_payload = self.create_invoice_payload(
            chat_id=chat_id,
            title=COURSE_TITLE,
            description=COURSE_DESCRIPTION,
            amount=config.COURSE_PRICE,
            customer_info=customer_info
        )

        try:
            await context.bot.send_invoice(**invoice_payload)
        except Exception as e:
            logger.error(f"Error sending invoice: {e}")
            raise

    async def create_invite_link(self, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        """Get existing or create new invite link"""
        try:
            # First check if user already has an invite link
            existing_link = self.db.get_chat_invite(user_id)
            if existing_link:
                logger.info(f"Found existing invite link for user {user_id}")
                return existing_link
                
            logger.info(f"Creating new invite link for user {user_id}")
            # Create new invite link
            chat_invite = await context.bot.create_chat_invite_link(
                chat_id=self.students_chat_id,
                member_limit=1,
                expire_date=None
            )

            # Store and return the invite link
            invite_link = chat_invite.invite_link
            logger.info(f"Successfully created new invite link for user {user_id}")
            self.db.record_chat_invite(user_id, invite_link)
            return invite_link

        except Exception as e:
            logger.error(f"Failed to create invite link for user {user_id}: {e}")
            if isinstance(e, TelegramError):
                logger.error(f"Telegram error details: {e.message}")
            return None

    async def handle_pre_checkout_query(self, 
                                      update: Update, 
                                      context: ContextTypes.DEFAULT_TYPE):
        """Handles the pre-checkout query"""
        query = update.pre_checkout_query
        try:
            await query.answer(ok=True)
        except Exception as e:
            logger.error(f"Error in pre-checkout: {e}")
            await query.answer(
                ok=False, 
                error_message="Payment processing error, please try again later."
            )

    async def handle_successful_payment(self, 
                                      update: Update, 
                                      context: ContextTypes.DEFAULT_TYPE):
        """Handles successful payment"""
        user = update.effective_user
        payment_info = update.message.successful_payment

        logger.info(f"Processing successful payment for user {user.id}")

        # Record the payment
        try:
            self.db.record_payment(
                user_id=user.id,
                username=user.username,
                customer_info=context.user_data,
                transaction_id=payment_info.provider_payment_charge_id,
                amount=payment_info.total_amount / 100,
                currency=payment_info.currency
            )
            logger.info(f"Successfully recorded payment for user {user.id}")

            # If custom payment handler is provided, use it
            if self._custom_payment_handler:
                await self._custom_payment_handler(update, context)
                return

            # Otherwise use default handling...
            invite_link = await self.create_invite_link(user.id, context)
            
            if invite_link:
                escaped_link = escape_markdown(invite_link)
                await update.message.reply_text(
                    ACCESS_PAYMENT_SUCCESS.format(
                        transaction_id=payment_info.provider_payment_charge_id,
                        invite_link=escaped_link
                    ),
                    parse_mode='MarkdownV2'
                )
            else:
                await update.message.reply_text(
                    ACCESS_PAYMENT_SUCCESS_NO_LINK.format(
                        transaction_id=payment_info.provider_payment_charge_id
                    ),
                    parse_mode='MarkdownV2'
                )

        except Exception as e:
            logger.error(f"Failed to process payment for user {user.id}: {e}")
            await update.message.reply_text(
                f"Спасибо за покупку! Ваша транзакция успешно завершена.\n"
                f"ID транзакции: {payment_info.provider_payment_charge_id}"
            )

    async def get_access_status(self, user_id: int) -> tuple[bool, Optional[str]]:
        """Check user's access status and return invite link if available"""
        has_paid = self.db.get_payment_status(user_id)
        invite_link = self.db.get_chat_invite(user_id) if has_paid else None
        return has_paid, invite_link
