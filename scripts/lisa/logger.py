
import sys

def print_with_status(message, status_icon="🟢"):
    """
    Prints a message prefixed with the current context health status icon.
    """
    # If the message is a raw newline or empty, just print it
    if message == "\n":
        print(message, end="")
        return

    # If message is multiline, prefix first line? 
    # Or just prefix the whole block? 
    # For now, simplistic approach:
    # [🟢] [LISA] Message...
    
    # We assume 'message' might already have [LISA] prefix or be a raw string.
    # We just want to prepend the icon.
    
    print(f"[{status_icon}] {message}")

def get_current_icon():
    """
    Retrieves the current status icon from the cache (lazy).
    To be implemented by wiring up with context_stats.
    For now returns default.
    """
    # This will be injected or imported. 
    # To avoid circular imports, maybe commands.py passes the icon to the logger?
    # OR logger imports context_stats (if context_stats doesn't import logger).
    # context_stats -> standard lib. Safe.
    from .context_stats import get_cached_health_icon
    return get_cached_health_icon()

def log(message):
    """
    Main logging function. Auto-fetches current status.
    """
    try:
        icon = get_current_icon()
    except Exception:
         icon = "⚪" # Fallback/Unknown
         
    print_with_status(message, icon)
