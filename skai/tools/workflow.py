"""Workflow tools for SKAI.

Contains tools for creating and executing workflows involving multiple agents.
"""

from typing import Any, Dict, List, Optional

from skai.kernel.agent import kernel
from skai.utils.logging import get_skai_logger

logger = get_skai_logger("tools.workflow")


def create_information_workflow(query: str) -> Dict[str, Any]:
    """Create a workflow to gather and present information on a topic.
    
    This workflow:
    1. Uses the Research Agent to gather information
    2. Formats the information into a coherent response

    Args:
        query: The topic or question to research
        
    Returns:
        Results from executing the workflow
    """
    logger.info(f"Creating information workflow for query: {query}")
    
    # Define the workflow steps
    workflow = [
        {
            "agent": "research_agent",
            "input": query,
        },
    ]
    
    # Execute the workflow
    results = kernel.execute_workflow(workflow)
    
    return results


def create_weather_info_workflow(city: str) -> Dict[str, Any]:
    """Create a workflow to provide weather information plus context.
    
    This workflow:
    1. Uses the Weather Agent to get weather data for a city
    2. Uses the Research Agent to get additional information about the city
    3. Combines the information into a comprehensive response

    Args:
        city: City to get weather and information for
        
    Returns:
        Results from executing the workflow
    """
    logger.info(f"Creating weather information workflow for city: {city}")
    
    # Define the workflow steps
    weather_query = f"What's the weather in {city}?"
    info_query = f"Tell me interesting facts about {city}"
    
    workflow = [
        {
            "agent": "weather_time_agent",
            "input": weather_query,
        },
        {
            "agent": "research_agent",
            "input": info_query,
        },
    ]
    
    # Execute the workflow
    results = kernel.execute_workflow(workflow)
    
    return results 