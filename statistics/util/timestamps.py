from datetime import datetime, timedelta

def get_month_timestamps(year, month):
    # Start of the month
    start_time = datetime(year, month, 1)
    
    # End of the month
    if month == 12:
        end_time = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        end_time = datetime(year, month + 1, 1) - timedelta(seconds=1)
    
    return start_time, end_time