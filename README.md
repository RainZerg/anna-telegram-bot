# Telegram Course Bot

A Telegram bot for selling online courses with YooMoney integration.

## Features

- Course information display
- Lecturer information
- YooMoney payment processing
- Automatic chat access management
- Payment status persistence

## Setup

1. Create a Telegram bot via @BotFather and get the token
2. Set up YooMoney integration and get the provider token
3. Create a Telegram group for students and get its ID
4. Copy `.env.example` to `.env` and fill in the tokens
5. Place your course cover image in `media/cover_image.jpg`

## Running the Bot

### Using Docker (Recommended)

```bash
# Start the bot
./start.sh

# Stop the bot
./stop.sh