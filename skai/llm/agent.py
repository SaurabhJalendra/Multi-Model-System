"""Agent implementation for SKAI using OpenRouter.

This module provides an Agent class that replaces the Google ADK Agent.
"""

import inspect
import json
from typing import Any, Callable, Dict, List, Optional, Union

from skai.llm.openrouter import OpenRouterClient
from skai.utils.logging import get_skai_logger

logger = get_skai_logger("llm.agent")

class Agent:
    """Agent implementation using OpenRouter LLMs.
    
    This class provides an interface similar to Google ADK Agent but uses
    OpenRouter for LLM access.
    """
    
    def __init__(
        self,
        name: str,
        model: str,
        description: str,
        instruction: str,
        tools: Optional[List[Callable]] = None,
    ):
        """Initialize the Agent.
        
        Args:
            name: Agent name
            model: LLM model to use
            description: Agent description 
            instruction: System instructions for the agent
            tools: List of tool functions available to the agent
        """
        self.name = name
        self.model = model
        self.description = description
        self.instruction = instruction
        self.tools = tools or []
        self.callbacks = {}
        
        # Create OpenRouter client
        self.client = OpenRouterClient(model=model)
        
        logger.info(f"Initialized Agent: {name} with model {model}")
    
    def process_message(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Process a user message.
        
        Args:
            message: User message
            history: Conversation history
            tool_calls: List of tool calls to make
            
        Returns:
            Response dictionary
        """
        # Convert tools to the format expected by OpenRouter
        tools_for_api = []
        tool_executors = {}
        
        if self.tools:
            for tool in self.tools:
                if callable(tool):
                    # Get the function name, signature, and docstring
                    func_name = tool.__name__
                    func_desc = tool.__doc__ or ""
                    sig = inspect.signature(tool)
                    
                    # Extract parameter information from signature
                    parameters = {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    }
                    
                    for param_name, param in sig.parameters.items():
                        # Skip self, cls, and kwargs parameters
                        if param_name in ['self', 'cls', '**kwargs']:
                            continue
                            
                        # Get parameter type annotation if available
                        param_type = "string"  # Default type
                        if param.annotation != inspect.Parameter.empty:
                            if param.annotation == int:
                                param_type = "integer"
                            elif param.annotation == float:
                                param_type = "number"
                            elif param.annotation == bool:
                                param_type = "boolean"
                            elif param.annotation == list or param.annotation == List:
                                param_type = "array"
                            elif param.annotation == dict or param.annotation == Dict:
                                param_type = "object"
                        
                        # Add parameter to properties
                        parameters["properties"][param_name] = {
                            "type": param_type,
                            "description": f"Parameter: {param_name}"
                        }
                        
                        # Add to required list if doesn't have default value
                        if param.default == inspect.Parameter.empty:
                            parameters["required"].append(param_name)
                    
                    # Create tool definition
                    tool_definition = {
                        "type": "function",
                        "function": {
                            "name": func_name,
                            "description": func_desc,
                            "parameters": parameters,
                        },
                    }
                    
                    tools_for_api.append(tool_definition)
                    tool_executors[func_name] = tool
        
        # Call the OpenRouter client
        response = self.client.process_message(
            message=message,
            system_message=self.instruction,
            history=history,
            tools=tools_for_api if tools_for_api else None,
            tool_executors=tool_executors if tool_executors else None,
            model=self.model,
        )
        
        # Process tool calls if needed (this is now handled in OpenRouterClient)
        
        return response
    
    def add_tool(self, tool: Callable) -> None:
        """Add a tool to the agent.
        
        Args:
            tool: Tool function to add
        """
        if tool not in self.tools:
            self.tools.append(tool)
            logger.info(f"Added tool {tool.__name__} to agent {self.name}")
    
    def set_callback(self, event: str, callback: Callable) -> None:
        """Set a callback for an event.
        
        Args:
            event: Event name
            callback: Callback function
        """
        self.callbacks[event] = callback
        logger.info(f"Set callback for event {event} on agent {self.name}")
    
    def update_model(self, model: str) -> None:
        """Update the model used by the agent.
        
        Args:
            model: New model name
        """
        self.model = model
        self.client.model = model
        logger.info(f"Updated model for agent {self.name} to {model}") 