from datetime import date
from src.models import Timeframe

def get_active_timeframes(current_date: date):
    """
    Returns a list of Timeframe enums that should be processed today.
    - Monthly: 1st of the month
    - Weekly: Saturday
    - Daily: Weekdays (Mon-Fri)
    """
    active = []
    
    # 1. Monthly (1st of month)
    if current_date.day == 1:
        active.append(Timeframe.MONTHLY)
    
    # 2. Weekdays vs Saturday
    weekday = current_date.weekday()
    if weekday < 5:  # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri
        active.append(Timeframe.DAILY)
    elif weekday == 5:  # 5=Sat
        active.append(Timeframe.WEEKLY)
    
    return active
