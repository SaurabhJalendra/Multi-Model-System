"""Weather and time tools for SKAI."""

import datetime
from zoneinfo import ZoneInfo
from typing import Dict

from skai.utils.logging import get_skai_logger

logger = get_skai_logger("tools.weather_time")


def get_weather(city: str) -> Dict[str, str]:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city for which to retrieve the weather report.

    Returns:
        dict: status and result or error msg.
    """
    logger.info(f"Getting weather for city: {city}")
    
    if city.lower() == "new york":
        return {
            "status": "success",
            "report": (
                "The weather in New York is sunny with a temperature of 25 degrees"
                " Celsius (77 degrees Fahrenheit)."
            ),
        }
    else:
        logger.warning(f"Weather information not available for city: {city}")
        return {
            "status": "error",
            "error_message": f"Weather information for '{city}' is not available.",
        }


def get_current_time(city: str) -> Dict[str, str]:
    """Returns the current time in a specified city.

    Args:
        city (str): The name of the city for which to retrieve the current time.

    Returns:
        dict: status and result or error msg.
    """
    logger.info(f"Getting current time for city: {city}")

    # Map of city names to timezone identifiers
    timezone_map = {
        "new york": "America/New_York",
        "london": "Europe/London",
        "tokyo": "Asia/Tokyo",
        "paris": "Europe/Paris",
        "sydney": "Australia/Sydney",
        "los angeles": "America/Los_Angeles",
        "chicago": "America/Chicago",
        "mumbai": "Asia/Kolkata",
        "beijing": "Asia/Shanghai",
        "berlin": "Europe/Berlin",
    }

    city_lower = city.lower()
    if city_lower in timezone_map:
        tz_identifier = timezone_map[city_lower]
    else:
        logger.warning(f"Timezone information not available for city: {city}")
        return {
            "status": "error",
            "error_message": (
                f"Sorry, I don't have timezone information for {city}."
            ),
        }

    try:
        tz = ZoneInfo(tz_identifier)
        now = datetime.datetime.now(tz)
        report = (
            f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
        )
        
        return {"status": "success", "report": report}
    except Exception as e:
        logger.error(f"Error getting time for {city}: {e}")
        return {
            "status": "error",
            "error_message": f"An error occurred while getting the time for {city}."
        } 