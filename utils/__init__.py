"""
Utility functions for Area 51 Bot
Database operations, formatting, validation, and more
"""
from .formatters import UIFormatter, DashboardFormatter

# We'll import database functions from the existing database.py file
try:
    from .database import get_owner_data, save_owner_data, get_analytics
except ImportError:
    # Fallback to existing services.database if utils.database doesn't exist yet
    from services.database import get_owner_data, save_owner_data, get_analytics

__all__ = [
    'UIFormatter', 
    'DashboardFormatter',
    'get_owner_data',
    'save_owner_data', 
    'get_analytics'
]

