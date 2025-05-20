"""State management system for SKAI."""

import json
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from skai.utils.logging import get_skai_logger

logger = get_skai_logger("memory.state")


@dataclass
class Message:
    """A message in a conversation."""
    
    role: str  # "user", "assistant", "system", "agent"
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """Session represents a conversation session with history and state."""
    
    session_id: str
    messages: List[Message] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    
    def add_message(self, role: str, content: str, **metadata) -> Message:
        """Add a message to the session.
        
        Args:
            role: Role of the message sender
            content: Message content
            metadata: Additional metadata for the message
            
        Returns:
            The created message
        """
        message = Message(role=role, content=content, metadata=metadata)
        self.messages.append(message)
        self.last_updated = time.time()
        return message
    
    def update_state(self, updates: Dict[str, Any]) -> None:
        """Update session state.
        
        Args:
            updates: Dictionary of state updates
        """
        self.state.update(updates)
        self.last_updated = time.time()
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a value from session state.
        
        Args:
            key: State key
            default: Default value if key doesn't exist
            
        Returns:
            Value from state or default
        """
        return self.state.get(key, default)
    
    def get_conversation_history(self, max_messages: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get conversation history as a list of messages.
        
        Args:
            max_messages: Maximum number of messages to return (most recent)
            
        Returns:
            List of messages
        """
        messages = self.messages
        if max_messages is not None:
            messages = messages[-max_messages:]
        
        return [{"role": msg.role, "content": msg.content} for msg in messages]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to a dictionary.
        
        Returns:
            Dictionary representation of session
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """Create a session from a dictionary.
        
        Args:
            data: Dictionary representation of session
            
        Returns:
            Session object
        """
        # Convert message dictionaries to Message objects
        messages = [
            Message(**msg) for msg in data.get("messages", [])
        ]
        
        # Create a new session
        session = cls(
            session_id=data["session_id"],
            state=data.get("state", {}),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", time.time()),
            last_updated=data.get("last_updated", time.time()),
        )
        
        # Add messages
        session.messages = messages
        
        return session


class SessionManager:
    """Manages multiple sessions."""
    
    def __init__(self, save_dir: str = "data/sessions"):
        """Initialize SessionManager.
        
        Args:
            save_dir: Directory to save sessions
        """
        self.save_dir = save_dir
        self.sessions: Dict[str, Session] = {}
        
        # Create save directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        logger.info(f"SessionManager initialized with save directory: {save_dir}")
    
    def create_session(self, session_id: Optional[str] = None, **metadata) -> Session:
        """Create a new session.
        
        Args:
            session_id: Optional session ID (generated if not provided)
            metadata: Additional metadata for the session
            
        Returns:
            New session
        """
        if session_id is None:
            session_id = f"session_{int(time.time())}"
        
        session = Session(session_id=session_id, metadata=metadata)
        self.sessions[session_id] = session
        
        logger.info(f"Created session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session or None if not found
        """
        # Check if session is in memory
        if session_id in self.sessions:
            return self.sessions[session_id]
        
        # Try to load from disk
        session_path = os.path.join(self.save_dir, f"{session_id}.json")
        if os.path.exists(session_path):
            try:
                with open(session_path, "r") as f:
                    session_data = json.load(f)
                
                session = Session.from_dict(session_data)
                self.sessions[session_id] = session
                logger.info(f"Loaded session from disk: {session_id}")
                return session
            except Exception as e:
                logger.error(f"Error loading session {session_id}: {e}")
        
        logger.warning(f"Session not found: {session_id}")
        return None
    
    def save_session(self, session_id: str) -> bool:
        """Save a session to disk.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if saved successfully, False otherwise
        """
        if session_id not in self.sessions:
            logger.warning(f"Cannot save non-existent session: {session_id}")
            return False
        
        session = self.sessions[session_id]
        session_path = os.path.join(self.save_dir, f"{session_id}.json")
        
        try:
            with open(session_path, "w") as f:
                json.dump(session.to_dict(), f, indent=2)
            
            logger.info(f"Saved session to disk: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving session {session_id}: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if deleted successfully, False otherwise
        """
        # Remove from memory
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        # Remove from disk
        session_path = os.path.join(self.save_dir, f"{session_id}.json")
        if os.path.exists(session_path):
            try:
                os.remove(session_path)
                logger.info(f"Deleted session: {session_id}")
                return True
            except Exception as e:
                logger.error(f"Error deleting session {session_id}: {e}")
                return False
        
        return True


# Create a global session manager
session_manager = SessionManager() 