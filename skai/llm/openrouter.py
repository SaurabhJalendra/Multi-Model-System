"""OpenRouter API Client for SKAI.

This module provides a client for the OpenRouter API to access various LLMs.
"""

import json
import requests
import time
from typing import Any, Dict, List, Optional, Union, Callable

from skai.config.settings import config
from skai.utils.logging import get_skai_logger

logger = get_skai_logger("llm.openrouter")

class OpenRouterClient:
    """Client for the OpenRouter API.
    
    OpenRouter is a unified API that provides access to various LLMs including
    those from Anthropic, OpenAI, and others.
    """
    
    # OpenRouter API endpoint
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "meta-llama/llama-3.2-8b-instruct",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.95,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        timeout: int = 60,
    ):
        """Initialize the OpenRouter client.
        
        Args:
            api_key: OpenRouter API key (defaults to config value)
            model: LLM model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            frequency_penalty: Frequency penalty
            presence_penalty: Presence penalty
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or config.openrouter_api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.timeout = timeout
        
        if not self.api_key:
            logger.warning("No OpenRouter API key provided. Set OPENROUTER_API_KEY in .env file.")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_executors: Optional[Dict[str, Callable]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Call the OpenRouter chat completion API.
        
        Args:
            messages: List of messages in the conversation
            tools: List of tools available to the LLM
            tool_executors: Map of tool names to their executor functions
            model: Override the default model
            temperature: Override the default temperature
            max_tokens: Override the default max tokens
            
        Returns:
            API response dictionary
        """
        # Use provided params or defaults
        model = model or self.model
        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/sky-ai-repo/SKAI",  # Optional: helps with attribution
            "X-Title": "SKAI",  # Optional: helps with attribution
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
        }
        
        # Add tools if provided
        if tools:
            payload["tools"] = tools
        
        start_time = time.time()
        
        try:
            logger.debug(f"Sending request to OpenRouter API: {model}")
            response = requests.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            
            # Log response time
            elapsed = time.time() - start_time
            logger.debug(f"OpenRouter API response time: {elapsed:.2f}s")
            
            # Check for errors
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            # Process tool calls if they exist and executors are provided
            if tool_executors and "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                if "message" in choice and "tool_calls" in choice["message"]:
                    tool_calls = choice["message"]["tool_calls"]
                    
                    # Execute tools and update messages
                    for tool_call in tool_calls:
                        function_name = tool_call["function"]["name"]
                        try:
                            arguments = json.loads(tool_call["function"]["arguments"])
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse arguments for tool call: {tool_call}")
                            continue
                            
                        if function_name in tool_executors:
                            logger.info(f"Executing tool: {function_name}")
                            try:
                                # Execute the tool
                                tool_result = tool_executors[function_name](**arguments)
                                
                                # Add tool result to messages
                                messages.append({
                                    "role": "assistant",
                                    "content": None,
                                    "tool_calls": [{
                                        "id": tool_call["id"],
                                        "type": "function",
                                        "function": {
                                            "name": function_name,
                                            "arguments": tool_call["function"]["arguments"]
                                        }
                                    }]
                                })
                                
                                # Add tool result as a message
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call["id"],
                                    "content": json.dumps(tool_result)
                                })
                                
                                # Make a follow-up request to process the tool results
                                logger.debug(f"Making follow-up request with tool results for: {function_name}")
                                follow_up_payload = {
                                    "model": model,
                                    "messages": messages,
                                    "temperature": temperature,
                                    "max_tokens": max_tokens,
                                    "top_p": self.top_p,
                                    "frequency_penalty": self.frequency_penalty,
                                    "presence_penalty": self.presence_penalty,
                                }
                                
                                # Send follow-up request
                                follow_up_response = requests.post(
                                    self.API_URL,
                                    headers=headers,
                                    json=follow_up_payload,
                                    timeout=self.timeout,
                                )
                                
                                follow_up_response.raise_for_status()
                                result = follow_up_response.json()
                                
                            except Exception as e:
                                logger.error(f"Error executing tool {function_name}: {str(e)}")
                                # Add error message as tool result
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call["id"],
                                    "content": json.dumps({"error": str(e)})
                                })
                        else:
                            logger.warning(f"Tool {function_name} not found in tool_executors")
            
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"OpenRouter API request failed: {str(e)}"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "status": "error",
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "error": error_msg,
                "status": "error",
            }
    
    def process_message(
        self,
        message: str,
        system_message: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_executors: Optional[Dict[str, Callable]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process a user message with the LLM.
        
        This method provides an interface compatible with the Google ADK Agent.process_message.
        
        Args:
            message: User message
            system_message: System message for the LLM
            history: Conversation history
            tools: List of tools available to the LLM
            tool_executors: Map of tool names to their actual implementations
            model: Override the default model
            
        Returns:
            Response dictionary with message and tool_outputs
        """
        # Prepare messages
        messages = []
        
        # Add system message if provided
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        # Add history if provided
        if history:
            messages.extend(history)
        
        # Add user message
        messages.append({"role": "user", "content": message})
        
        # Call OpenRouter API
        response = self.chat_completion(
            messages=messages,
            tools=tools,
            tool_executors=tool_executors,
            model=model,
        )
        
        # Check for errors
        if "error" in response:
            return {
                "message": f"Error: {response['error']}",
                "status": "error",
                "tools_used": [],
            }
        
        # Extract response content
        try:
            # Get the final response
            if "choices" in response and len(response["choices"]) > 0:
                assistant_message = response["choices"][0]["message"]["content"]
            else:
                assistant_message = "I don't have a response at this time."
            
            # Process tool calls and outputs
            tool_outputs = {}
            tools_used = []
            
            if "choices" in response and len(response["choices"]) > 0:
                message_obj = response["choices"][0]["message"]
                
                # Check for tool calls in the response
                if "tool_calls" in message_obj:
                    tool_calls = message_obj["tool_calls"]
                    
                    for tool_call in tool_calls:
                        function_name = tool_call["function"]["name"]
                        tools_used.append(function_name)
                        
                        # Store tool results if available
                        # This will be populated if tool_executors was provided
                        # and the tools were actually executed
                        if function_name not in tool_outputs:
                            tool_outputs[function_name] = {
                                "status": "called",
                                "result": "Tool call was processed"
                            }
            
            return {
                "message": assistant_message,
                "status": "success",
                "tools_used": tools_used,
                "tool_outputs": tool_outputs,
                "full_response": response  # Include the full response for debugging
            }
            
        except (KeyError, IndexError) as e:
            error_msg = f"Error parsing OpenRouter response: {str(e)}"
            logger.error(error_msg)
            logger.debug(f"Response: {response}")
            return {
                "message": "I had trouble understanding. Please try again.",
                "status": "error",
                "tools_used": [],
            } 