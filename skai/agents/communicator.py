"""Communicator Agent for SKAI.

The Communicator Agent is responsible for:
1. Understanding user intent and sentiment
2. Formatting responses appropriately
3. Determining which specialized agents to route to
"""

from typing import Any, Dict, List, Optional, Tuple

# Remove import of Agent
# from skai.llm.agent import Agent

from skai.config.settings import config
from skai.utils.logging import get_skai_logger

logger = get_skai_logger("agents.communicator")


class CommunicatorAgent:
    """Communicator Agent that interprets user messages and intent.
    
    The Communicator Agent is the first to process user input and determines:
    - The intent of the message (query, command, etc.)
    - The sentiment and urgency
    - Which specialized agent(s) should handle the request
    """
    
    def __init__(
        self,
        name: str = "communicator_agent",
        model: str = "meta-llama/llama-3.3-8b-instruct:free",  # Efficient FREE model for communication tasks
        description: str = "Agent that interprets user messages and determines intent and sentiment",
        instruction: str = (
            "You are responsible for understanding user intent, sentiment, and urgency. "
            "Classify the message and identify the appropriate specialized agent to handle it."
        ),
    ):
        """Initialize Communicator Agent.
        
        Args:
            name: Agent name
            model: LLM model to use
            description: Agent description
            instruction: System instructions for the agent
        """
        self.name = name
        self.model = model
        self.description = description
        self.instruction = instruction
        
        logger.info(f"Initializing Communicator Agent: {name}")
        
        # Define the intent classification function
        def classify_message(message: str) -> Dict[str, Any]:
            """Classify a user message to determine intent, sentiment, and routing.
            
            Args:
                message: User message
                
            Returns:
                Classification results including intent, sentiment, and agent routing
            """
            # This is a placeholder that will be implemented with a proper LLM call
            # For now, we'll use simple keyword matching
            message_lower = message.lower()
            
            # Default classification
            classification = {
                "intent": "query",
                "sentiment": "neutral",
                "urgency": "normal",
                "agent": "general",
                "confidence": 0.7,
            }
            
            # Check for weather-related queries
            if any(kw in message_lower for kw in ["weather", "temperature", "forecast", "sunny", "rainy"]):
                classification["intent"] = "weather_query"
                classification["agent"] = "weather_time_agent"
                classification["confidence"] = 0.9
            
            # Check for time-related queries
            elif any(kw in message_lower for kw in ["time", "clock", "hour"]):
                classification["intent"] = "time_query"
                classification["agent"] = "weather_time_agent"
                classification["confidence"] = 0.9
                
            # Check for code improvement requests
            elif any(kw in message_lower for kw in ["code", "improve", "refactor", "bug", "fix", "optimize"]) and any(
                kw in message_lower for kw in ["file", "code", "module", "function", "class", "method"]):
                classification["intent"] = "code_improvement"
                classification["agent"] = "self_improving_agent"
                classification["confidence"] = 0.85
            
            # Sentiment analysis (very basic)
            if any(kw in message_lower for kw in ["urgent", "emergency", "asap", "immediately"]):
                classification["urgency"] = "high"
                classification["sentiment"] = "urgent"
            
            if any(kw in message_lower for kw in ["happy", "great", "excellent", "good", "thanks"]):
                classification["sentiment"] = "positive"
            
            if any(kw in message_lower for kw in ["sad", "bad", "terrible", "awful", "disappointed"]):
                classification["sentiment"] = "negative"
            
            return classification
        
        # Store the classification function
        self.classify_message = classify_message
        
        # We'll initialize the ADK agent later to avoid circular imports
        self.adk_agent = None
    
    def process_message(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Process a user message to determine intent and routing.
        
        Args:
            message: User message
            history: Conversation history (optional)
            
        Returns:
            Processed message with intent and routing information
        """
        logger.info(f"Processing message: {message[:50]}...")
        
        # For simplicity, directly call the function
        classification = self.classify_message(message)
        
        # Prepare the processed message
        processed_message = {
            "original_message": message,
            "intent": classification.get("intent", "query"),
            "sentiment": classification.get("sentiment", "neutral"),
            "urgency": classification.get("urgency", "normal"),
            "target_agent": classification.get("agent", "general"),
            "confidence": classification.get("confidence", 0.5),
            "timestamp": None,  # Will be filled by the caller
        }
        
        logger.info(
            f"Message classified as {processed_message['intent']} "
            f"with {processed_message['sentiment']} sentiment, "
            f"routing to {processed_message['target_agent']}"
        )
        
        return processed_message
    
    def format_response(self, response: str, sentiment: str = "neutral", urgency: str = "normal") -> str:
        """Format a response based on detected sentiment and urgency.
        
        Args:
            response: Original response text
            sentiment: Detected sentiment (positive, negative, neutral)
            urgency: Detected urgency (high, normal, low)
            
        Returns:
            Formatted response
        """
        # In a full implementation, this would use an LLM to reformat the response
        # For now, we'll use simple templates
        
        if urgency == "high":
            # Add urgency markers for high-urgency responses
            return f"URGENT: {response}"
        
        if sentiment == "positive":
            # Add a positive tone for positive sentiment
            positive_endings = ["I'm glad I could help!", "Happy to assist!", "Hope that helps!"]
            import random
            ending = random.choice(positive_endings)
            return f"{response} {ending}"
        
        if sentiment == "negative":
            # Add an empathetic tone for negative sentiment
            return f"I understand this might be frustrating. {response}"
        
        # Default case: return the original response
        return response


# Create a global communicator agent instance
communicator = CommunicatorAgent() 