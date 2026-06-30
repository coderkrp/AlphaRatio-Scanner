import httpx
import logging
from src.config_loader import load_config

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        config = load_config()
        self.token = config['telegram']['token']
        chat_id_raw = config['telegram']['chat_id']
        
        # Normalize chat_id into a list of strings
        if isinstance(chat_id_raw, list):
            self.chat_ids = [str(cid) for cid in chat_id_raw]
        else:
            self.chat_ids = [str(chat_id_raw)]
            
        self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    async def send_message(self, text: str):
        if self.token == "YOUR_TELEGRAM_BOT_TOKEN":
            logger.warning("Telegram token not configured. Skipping send.")
            return True # Pretend success for development if not configured
            
        # Message splitting for Telegram's 4096 character limit
        # alert_engine should handle this, but adding safety here
        if len(text) > 4096:
            logger.warning("Message too long, trimming in TelegramBot.")
            text = text[:4093] + "..."

        at_least_one_success = False
        async with httpx.AsyncClient() as client:
            for chat_id in self.chat_ids:
                payload = {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                }
                try:
                    response = await client.post(self.base_url, json=payload)
                    response.raise_for_status()
                    at_least_one_success = True
                except Exception as e:
                    logger.error(f"Failed to send Telegram message to {chat_id}: {e}")
                    
        return at_least_one_success
