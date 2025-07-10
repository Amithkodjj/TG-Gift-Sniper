import logging
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

logger = logging.getLogger(__name__)

class CommissionMiddleware(BaseMiddleware):
    """
    Middleware for handling commission on successful payments.
    Automatically deducts commission from deposits and notifies owner.
    """
    
    def __init__(self, owner_id: int):
        self.owner_id = owner_id
        super().__init__()
    
    async def __call__(self, handler, event: TelegramObject, data: dict):
        """
        Process commission for successful payments.
        """
        # Only process successful payment messages
        if (isinstance(event, Message) and 
            hasattr(event, 'successful_payment') and 
            event.successful_payment):
            
            # Add commission processing data
            data["process_commission"] = True
            data["owner_id"] = self.owner_id
        
        return await handler(event, data) 