import datetime
from dateutil import parser
import pytz

def calculate_time_difference(timestamp_str):
    """
    Calculate the difference between current time and a provided timestamp.
    
    Args:
        timestamp_str (str): A timestamp string in ISO 8601 format (e.g., '2025-04-07T02:26:11Z')
        
    Returns:
        tuple: Hours, minutes, and seconds difference
    """
    # Parse the input timestamp
    target_time = parser.parse(timestamp_str)
    
    # Get current time in UTC
    current_time = datetime.datetime.now(pytz.UTC)
    
    # Calculate the time difference
    time_difference = abs(current_time - target_time)
    
    # Extract hours, minutes, and seconds
    total_seconds = time_difference.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    
    return hours, minutes, seconds
