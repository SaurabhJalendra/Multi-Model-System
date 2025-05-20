"""Kernel Agent for SKAI.

The Kernel Agent is the central orchestrator that manages task routing, agent execution,
and result aggregation.
"""

import time
from typing import Any, Dict, List, Optional, Union

# Import our Agent implementation directly
from skai.llm.agent import Agent

from skai.config.settings import config
from skai.memory.state import Session, session_manager
from skai.utils.logging import get_skai_logger

logger = get_skai_logger("kernel.agent")


class KernelAgent:
    """Kernel Agent for orchestrating the SKAI system.
    
    The Kernel Agent is responsible for:
    1. Managing session state
    2. Routing tasks to appropriate agents
    3. Aggregating results
    4. Maintaining conversation context
    """
    
    def __init__(
        self,
        name: str = "kernel_agent",
        model: str = "meta-llama/llama-4-maverick:free",
        description: str = "Kernel Agent for orchestrating SKAI",
        instruction: str = "You are the central controller for SKAI, responsible for managing other agents and coordinating workflows.",
    ):
        """Initialize the Kernel Agent.
        
        Args:
            name: Name of the agent
            model: LLM model to use
            description: Description of the agent
            instruction: Instructions for the agent
        """
        self.name = name
        self.model = model
        self.description = description
        self.instruction = instruction
        self.agents: Dict[str, Agent] = {}
        self.tools: Dict[str, Any] = {}
        
        logger.info(f"Initialized Kernel Agent: {name}")
        
        # Create the root agent using our implementation
        self.adk_agent = Agent(
            name=name,
            model=model,
            description=description,
            instruction=instruction,
            tools=[],  # No tools yet
        )
        
        # Callbacks are handled differently in our implementation
        # so we don't need these anymore
    
    def register_agent(self, name: str, agent: Agent) -> None:
        """Register a new agent with the Kernel.
        
        Args:
            name: Name of the agent
            agent: The agent to register
        """
        self.agents[name] = agent
        logger.info(f"Registered agent: {name}")
    
    def register_tool(self, name: str, tool_func: Any) -> None:
        """Register a tool with the Kernel.
        
        Args:
            name: Name of the tool
            tool_func: The tool function
        """
        self.tools[name] = tool_func
        
        # Add tool to the ADK agent
        self.adk_agent.add_tool(tool_func)
        
        logger.info(f"Registered tool: {name}")
    
    def process_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process a user message.
        
        Args:
            message: User message
            session_id: Session ID (created if None)
            metadata: Additional metadata
            
        Returns:
            Response dictionary
        """
        start_time = time.time()
        
        # Get or create session
        session = self._get_or_create_session(session_id, metadata or {})
        
        # Add user message to session
        session.add_message(role="user", content=message)
        
        # Get conversation history
        conversation_history = session.get_conversation_history()
        
        # Step 1: Process with Communicator Agent if available
        communicator_agent = self._get_agent_by_type("communicator_agent")
        if communicator_agent:
            logger.info("Routing message to Communicator Agent")
            processed_message = communicator_agent.process_message(message, history=conversation_history)
            
            # Update session state with intent and sentiment
            session.update_state({
                "intent": processed_message["intent"],
                "sentiment": processed_message["sentiment"],
                "urgency": processed_message["urgency"],
            })
            
            # Log the processing results
            logger.info(
                f"Message processed: intent={processed_message['intent']}, "
                f"sentiment={processed_message['sentiment']}, "
                f"target_agent={processed_message['target_agent']}"
            )
            
            # Step 2: Route to appropriate specialized agent based on Communicator's analysis
            target_agent_name = processed_message["target_agent"]
            if target_agent_name != "general" and target_agent_name in self.agents:
                # Route to specialized agent
                logger.info(f"Routing to specialized agent: {target_agent_name}")
                target_agent = self.agents[target_agent_name]
                
                # Process with specialized agent
                specialized_response = self.route_to_agent(
                    target_agent_name, message, session.session_id
                )
                
                response_text = specialized_response.get("message", "")
                
                # Format the response based on sentiment and urgency
                if hasattr(communicator_agent, "format_response"):
                    response_text = communicator_agent.format_response(
                        response_text,
                        processed_message["sentiment"],
                        processed_message["urgency"]
                    )
                
                # Create the final response
                response = {
                    "message": response_text,
                    "session_id": session.session_id,
                    "intent": processed_message["intent"],
                    "sentiment": processed_message["sentiment"],
                    "urgency": processed_message["urgency"],
                    "elapsed_time": time.time() - start_time,
                    "agent_used": target_agent_name,
                }
                
                # Add any additional info from specialized agent
                for key, value in specialized_response.items():
                    if key not in response and key != "message":
                        response[key] = value
                
                # Add assistant response to session
                session.add_message(role="assistant", content=response_text)
                
                # Save session
                session_manager.save_session(session.session_id)
                
                return response
        
        # If we get here, either:
        # 1. There was no Communicator Agent
        # 2. Target agent wasn't found
        # 3. Target agent was "general"
        # So we use the default ADK agent
        
        logger.info("Using default ADK agent processing")
        
        # Process the message with the ADK agent
        adk_response = self.adk_agent.process_message(
            message, 
            history=conversation_history
        )
        
        # Add assistant message to session
        session.add_message(role="assistant", content=adk_response["message"])
        
        # Save session
        session_manager.save_session(session.session_id)
        
        # Prepare response
        result = {
            "message": adk_response["message"],
            "session_id": session.session_id,
            "tools_used": adk_response.get("tools_used", []),
            "elapsed_time": time.time() - start_time,
            "agent_used": "default_adk_agent",
        }
        
        return result
    
    def route_to_agent(
        self,
        agent_name: str,
        input_data: Union[str, Dict[str, Any]],
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Route a task to a specific agent.
        
        Args:
            agent_name: Name of the agent to route to
            input_data: Input data for the agent
            session_id: Session ID
            
        Returns:
            Agent response
        """
        if agent_name not in self.agents:
            error_msg = f"Agent not found: {agent_name}"
            logger.error(error_msg)
            return {"error": error_msg}
        
        # Get the agent
        agent = self.agents[agent_name]
        
        # Get session
        session = self._get_or_create_session(session_id)
        
        # Get conversation history
        conversation_history = session.get_conversation_history()
        
        # Process with the agent
        if isinstance(input_data, str):
            # Simple string input
            if hasattr(agent, "process_message"):
                response = agent.process_message(input_data, history=conversation_history)
            else:
                # Fallback to ADK agent interface
                response = agent.adk_agent.process_message(input_data, history=conversation_history)
            
            # Log the interaction in the session
            session.add_message(role="user", content=input_data, target_agent=agent_name)
            session.add_message(role="agent", content=response["message"], source_agent=agent_name)
        else:
            # Structured input (depends on agent implementation)
            # This would need to be implemented based on the specific agent
            logger.warning(f"Structured input not yet implemented for agent: {agent_name}")
            response = {"message": "Structured input not supported yet"}
        
        # Save session
        session_manager.save_session(session.session_id)
        
        return response
    
    def execute_workflow(
        self,
        workflow: List[Dict[str, Any]],
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a multi-step workflow.
        
        Args:
            workflow: List of workflow steps (agent name and input)
            session_id: Session ID (created if None)
            metadata: Additional metadata
            
        Returns:
            Workflow execution results
        """
        start_time = time.time()
        
        # Get or create session
        session = self._get_or_create_session(session_id, metadata or {})
        
        results = []
        final_result = None
        
        # Execute each step in the workflow
        for i, step in enumerate(workflow):
            agent_name = step.get("agent")
            input_data = step.get("input")
            
            if not agent_name or not input_data:
                logger.error(f"Invalid workflow step {i}: missing agent or input")
                continue
            
            logger.info(f"Executing workflow step {i+1}/{len(workflow)}: {agent_name}")
            
            # Route to agent
            step_result = self.route_to_agent(agent_name, input_data, session.session_id)
            
            # Store result
            results.append({
                "step": i + 1,
                "agent": agent_name,
                "input": input_data,
                "result": step_result,
            })
            
            # Update final result with the last step's result
            final_result = step_result
            
            # Check for workflow control (e.g., conditions, loops) - not implemented yet
        
        # Prepare response
        response = {
            "session_id": session.session_id,
            "workflow_results": results,
            "message": final_result.get("message", "") if final_result else "",
            "elapsed_time": time.time() - start_time,
        }
        
        return response
    
    def _get_or_create_session(
        self,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """Get or create a session.
        
        Args:
            session_id: Session ID (created if None)
            metadata: Session metadata
            
        Returns:
            Session object
        """
        if session_id is None:
            # Create new session
            return session_manager.create_session(metadata=metadata or {})
        
        # Get existing session
        session = session_manager.get_session(session_id)
        if session is None:
            # Create new session if not found
            return session_manager.create_session(session_id=session_id, metadata=metadata or {})
        
        return session
    
    def _get_agent_by_type(self, agent_type: str) -> Optional[Any]:
        """Get an agent by type.
        
        Args:
            agent_type: Type of agent to get
            
        Returns:
            Agent or None if not found
        """
        # First, try exact match
        if agent_type in self.agents:
            return self.agents[agent_type]
        
        # Try to find by prefix
        matching_agents = [
            agent for name, agent in self.agents.items()
            if name.startswith(agent_type) or agent_type in name
        ]
        
        if matching_agents:
            return matching_agents[0]
        
        return None
    
    # Callback handlers - simplified for our implementation
    def _on_agent_start(self, payload: Any) -> None:
        """Handle agent start event."""
        logger.debug(f"Agent started: {payload}")
    
    def _on_agent_end(self, payload: Any) -> None:
        """Handle agent end event."""
        logger.debug(f"Agent ended: {payload}")
    
    def _on_tool_start(self, payload: Any) -> None:
        """Handle tool start event."""
        logger.debug(f"Tool started: {payload}")
    
    def _on_tool_end(self, payload: Any) -> None:
        """Handle tool end event."""
        logger.debug(f"Tool ended: {payload}")


# Create a global kernel agent instance
kernel = KernelAgent() 