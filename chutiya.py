import random
import asyncio
import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from anthropic import AsyncAnthropic

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('BOT_TOKEN')
LOG_CHANNEL_ID = os.getenv('LOG_CHANNEL_ID')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
RESPONSE_PROBABILITY = 0.5

anthropic = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

async def log_message(context: ContextTypes.DEFAULT_TYPE, message_data: dict):
    try:
        log_text = f"User: {message_data['username']} ({message_data['user_id']})\n"
        log_text += f"Chat: {message_data['chat_type']} ({message_data['chat_id']})\n"
        log_text += f"Message: {message_data['text']}\n"
        log_text += f"Timestamp: {message_data['timestamp']}"
        
        await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=log_text)
        logger.info(f"Message logged to channel: {message_data['text'][:20]}...")
    except Exception as e:
        logger.error(f"Error logging message to channel: {e}")

async def generate_response(prompt):
    try:
        response = await anthropic.completions.create(
            model="claude-3-haiku",
            max_tokens_to_sample=2000,
            prompt=f"Human: {prompt}\n\nAssistant:"
        )
        logger.info(f"Generated response: {response.completion[:50]}...")
        return response.completion
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "I apologize, but I'm having trouble processing your request at the moment. Could you please try again or rephrase your question?"

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
    await log_message(context, message_data)
    
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
    prompt = f"Continue the conversation with {user_name}. Their latest message is: '{message}'. Respond to the User as per mood of the message also keep in track previous conversation with them to give a befitting reply. If the message is related to coding or programming, provide a detailed and helpful response. Use Hinglish or English as appropriate based on the user's message."
    response = await generate_response(prompt)
    await send_response(update, context, response)

async def start_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, message: str, user_name: str):
    prompt = f"Start a conversation with {user_name} based on their message: '{message}'. Respond in an engaging manner in Hinglish or English as appropriate. If the message is related to coding or programming, provide a detailed and helpful response."
    response = await generate_response(prompt)
    await send_response(update, context, response)

async def send_response(update: Update, context: ContextTypes.DEFAULT_TYPE, response: str):
    wait_time = random.uniform(0.5, 2)
    logger.info(f"Waiting for {wait_time:.2f} seconds before responding")
    await asyncio.sleep(wait_time)
    
    logger.info(f"Sending response: {response[:50]}...")
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

    prompt = f"Answer this question from {update.effective_user.first_name} in a friendly and informative way: '{question}'. If the question is related to coding or programming, provide a detailed and helpful response. Respond in Hinglish or English as appropriate based on the user's question."
    response = await generate_response(prompt)
    await update.message.reply_text(response)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Exception while handling an update: {context.error}")
    if update and isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("Oops! Something went wrong. Please try again later.")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ask", ask))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    logger.info("Starting the bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()
