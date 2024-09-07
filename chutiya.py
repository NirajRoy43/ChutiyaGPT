import random
import asyncio
import logging
import os
import signal
from telethon import TelegramClient, events
from telethon.tl.custom import Message
from telethon.tl.types import PeerChannel
import g4f

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
API_ID = os.getenv('API_ID')  # Your Telegram API ID
API_HASH = os.getenv('API_HASH')  # Your Telegram API Hash
BOT_TOKEN = os.getenv('BOT_TOKEN')
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID'))
RESPONSE_PROBABILITY = 0.5

# Initialize Telegram client
client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

async def log_message(username, user_id, chat_type, chat_id, text, timestamp):
    try:
        log_text = f"User: {username} ({user_id})\n"
        log_text += f"Chat: {chat_type} ({chat_id})\n"
        log_text += f"Message: {text}\n"
        log_text += f"Timestamp: {timestamp}"
        
        await client.send_message(LOG_CHANNEL_ID, log_text, parse_mode='md')
        logger.info(f"Message logged to channel: {text[:20]}...")
    except Exception as e:
        logger.error(f"Error logging message to channel: {e}")

async def generate_response(prompt):
    try:
        response = await g4f.ChatCompletion.create_async(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        logger.info(f"Generated response: {response[:50]}...")
        return response
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "I apologize, but I'm having trouble processing your request at the moment. Could you please try again or rephrase your question?"

async def handle_message(event):
    message = event.message
    user_id = message.sender_id
    username = message.sender.username
    text = message.text
    chat_id = message.chat_id
    chat_type = message.chat.title if message.chat.title else message.chat.__class__.__name__
    timestamp = message.date
    
    logger.info(f"Received message: {text}")
    
    await log_message(username, user_id, chat_type, chat_id, text, timestamp)
    
    if message.reply_to_msg_id and message.reply_to_msg_id:
        bot_id = (await client.get_me()).id
        if message.reply_to_msg_id == bot_id:
            logger.info("This is a reply to bot's message. Continuing conversation.")
            await continue_conversation(event, user_id, text, username)
    elif random.random() < RESPONSE_PROBABILITY:
        logger.info("Decided to respond to this message")
        await start_conversation(event, user_id, text, username)
    else:
        logger.info("Decided not to respond to this message")

async def continue_conversation(event, user_id, message, username):
    prompt = f"Continue the conversation with {username}. Their latest message is: '{message}'. Respond to the User as per mood of the message also keep in track previous conversation with them to give a befitting reply. If the message is related to coding or programming, provide a detailed and helpful response. Use Hinglish or English as appropriate based on the user's message."
    response = await generate_response(prompt)
    await send_response(event, response)

async def start_conversation(event, user_id, message, username):
    prompt = f"Start a conversation with {username} based on their message: '{message}'. Respond in an engaging manner in Hinglish or English as appropriate. If the message is related to coding or programming, provide a detailed and helpful response."
    response = await generate_response(prompt)
    await send_response(event, response)

async def send_response(event, response):
    wait_time = random.uniform(0.5, 2)
    logger.info(f"Waiting for {wait_time:.2f} seconds before responding")
    await asyncio.sleep(wait_time)
    
    logger.info(f"Sending response: {response[:50]}...")
    await event.reply(response, parse_mode='md')

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("Main active hoon! Ab maza aayega. 😎", parse_mode='md')
    logger.info("Bot started and responded to /start command")

@client.on(events.NewMessage(pattern='/ask'))
async def ask(event):
    logger.info("Received /ask command")
    question = event.message.text.split(maxsplit=1)[1:]
    if not question:
        await event.reply("Kuch to pucho yaar! /ask ke baad apna sawal likho.", parse_mode='md')
        return

    prompt = f"Answer this question from {event.sender.first_name} in a friendly and informative way: '{question}'. If the question is related to coding or programming, provide a detailed and helpful response. Respond in Hinglish or English as appropriate based on the user's question."
    response = await generate_response(prompt)
    await event.reply(response, parse_mode='md')

@client.on(events.NewMessage)
async def error_handler(event):
    try:
        await event.reply("Oops! Something went wrong. Please try again later.", parse_mode='md')
    except Exception as e:
        logger.error(f"Exception while handling an update: {e}")

def signal_handler(signum, frame):
    loop = asyncio.get_event_loop()
    loop.create_task(client.disconnect())

def main():
    # Register the signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting the bot...")
    client.run_until_disconnected()

if __name__ == '__main__':
    main()
