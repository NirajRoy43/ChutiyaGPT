import random
import time
import asyncio
import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import g4f
import nest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient


if os.name == 'nt':
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


nest_asyncio.apply()


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


TOKEN = os.getenv('BOT_TOKEN')
MONGO_CONNECTION_STRING = os.getenv('MONGODB_STRING')
RESPONSE_PROBABILITY = 0.5

client = AsyncIOMotorClient(MONGO_CONNECTION_STRING)
db = client.telegram_bot_db
messages_collection = db.messages

async def store_message(message_data):
    try:
        await messages_collection.insert_one(message_data)
        logger.info(f"Message stored in database: {message_data['text'][:20]}...")
    except Exception as e:
        logger.error(f"Error storing message in database: {e}")

async def generate_response(prompt):
    try:
        response = await g4f.ChatCompletion.create_async(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        logger.info(f"Generated response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "Oops! Mera dimaag thoda hang ho gaya. 🤖💨"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received message: {update.message.text}")
    
    
    message_data = {
        "user_id": update.effective_user.id,
        "username": update.effective_user.username,
        "text": update.message.text,
        "timestamp": update.message.date,
        "chat_id": update.effective_chat.id,
        "chat_type": update.effective_chat.type
    }
    await store_message(message_data)
    
    user_id = update.effective_user.id
    message = update.message.text
    user_name = update.message.from_user.first_name

    if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
        logger.info("This is a reply to bot's message. Continuing conversation.")
        await continue_conversation(update, context, user_id, message, user_name)
    elif random.random() < RESPONSE_PROBABILITY:
        logger.info("Decided to respond to this message")
        await start_conversation(update, context, user_id, message, user_name)
    else:
        logger.info("Decided not to respond to this message")

async def continue_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, message: str, user_name: str):
    prompt = f"Continue the conversation with {user_name}. Their latest message is: '{message}'. Respond in a witty and engaging manner in Hindi (use Roman script). Keep it short (max 2 sentences)."
    response = await generate_response(prompt)
    await send_response(update, context, response)

async def start_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, message: str, user_name: str):
    prompt = f"Start a conversation with {user_name} based on their message: '{message}'. Respond in a witty and engaging manner in Hindi (use Roman script). Keep it short (max 2 sentences)."
    response = await generate_response(prompt)
    await send_response(update, context, response)
	
async def send_response(update: Update, context: ContextTypes.DEFAULT_TYPE, response: str):
    wait_time = random.uniform(1, 5)
    logger.info(f"Waiting for {wait_time:.2f} seconds before responding")
    await asyncio.sleep(wait_time)
    
    logger.info(f"Sending response: {response}")
    await update.message.reply_text(response)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Main active hoon! Ab maza aayega. 😎")
    logger.info("Bot started and responded to /start command")

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Received /ask command")
    question = ' '.join(context.args)
    if not question:
        await update.message.reply_text("Kuch to pucho yaar! /ask ke baad apna sawal likho.")
        return

    prompt = f"Answer this question from {update.effective_user.first_name} in a friendly and informative way: '{question}'. Respond in Hindi (use Roman script). Keep it concise but informative."
    response = await generate_response(prompt)
    await update.message.reply_text(response)

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ask", ask))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Starting the bot...")
    application.run_polling()

if __name__ == '__main__':
    main()	
