import random
import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import g4f

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
API_TOKEN = os.getenv('BOT_TOKEN')
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID'))
RESPONSE_PROBABILITY = 0.5

async def log_message(username, user_id, chat_type, chat_id, text, timestamp):
    try:
        log_text = f"User: {username} ({user_id})\n"
        log_text += f"Chat: {chat_type} ({chat_id})\n"
        log_text += f"Message: {text}\n"
        log_text += f"Timestamp: {timestamp}"
        
        await bot.send_message(LOG_CHANNEL_ID, log_text, parse_mode='Markdown')
        logger.info(f"Message logged to channel: {text[:20]}...")
    except Exception as e:
        logger.error(f"Error logging message to channel: {e}")

async def generate_response(prompt):
    try:
        response = await g4f.ChatCompletion.create_async(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        if not response:
            logger.warning("Received empty response from the model.")
            return "I apologize, but I couldn't generate a response."
        logger.info(f"Generated response: {response[:50]}...")
        return response
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "I apologize, but I'm having trouble processing your request at the moment. Could you please try again or rephrase your question?"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Main active hoon! Ab maza aayega. 😎")
    logger.info("Bot started and responded to /start command")

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Received /ask command")
    if context.args:
        question = ' '.join(context.args)
        prompt = f"Answer this question from {update.message.from_user.first_name} in a friendly and informative way: '{question}'. If the question is related to coding or programming, provide a detailed and helpful response. Respond in Hinglish or English as appropriate based on the user's question."
        response = await generate_response(prompt)
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("Kuch to pucho yaar! /ask ke baad apna sawal likho.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    text = message.text
    chat_id = message.chat.id
    chat_type = message.chat.title if message.chat.title else message.chat.type
    timestamp = message.date

    logger.info(f'Received message: {text}')
    
    await log_message(username, user_id, chat_type, chat_id, text, timestamp)
    
    if random.random() < RESPONSE_PROBABILITY:
        logger.info('Decided to respond to this message')
        prompt = f"Start a conversation with {username} based on their message: '{text}'. Respond in an engaging manner in Hinglish or English as appropriate. If the message is related to coding or programming, provide a detailed and helpful response."
        response = await generate_response(prompt)
        await update.message.reply_text(response)
    else:
        logger.info('Decided not to respond to this message')

def main():
    # Create the Application and pass it your bot's token
    application = ApplicationBuilder().token(API_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ask", ask))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == '__main__':
    main()
