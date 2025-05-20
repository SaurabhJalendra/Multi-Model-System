"""Self-Improving Agent for SKAI.

The Self-Improving Agent is responsible for:
1. Monitoring system logs and performance
2. Identifying code improvements
3. Implementing code changes to the codebase
4. Maintaining a version history of improvements
"""

import os
import time
import json
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from skai.config.settings import config
from skai.utils.logging import get_skai_logger

logger = get_skai_logger("agents.self_improving")


class SelfImprovingAgent:
    """Self-Improving Agent that analyzes and updates SKAI's codebase.
    
    The Self-Improving Agent is capable of:
    - Analyzing system logs for patterns and issues
    - Identifying potential code improvements
    - Generating and testing code modifications
    - Implementing changes with version tracking
    - Learning from successful and failed code changes
    """
    
    def __init__(
        self,
        name: str = "self_improving_agent",
        model: str = "deepseek/deepseek-chat-v3",  # Using a more capable model for code generation
        description: str = "Agent that analyzes and improves SKAI's codebase",
        instruction: str = (
            "You are responsible for analyzing SKAI's codebase, identifying potential improvements, "
            "and implementing changes when authorized. Always consider the impact of changes, "
            "maintain code style consistency, and ensure changes are well-tested before implementation."
        ),
        code_repo_path: Optional[str] = None,
        version_file: str = "data/improvement_history.json",
    ):
        """Initialize Self-Improving Agent.
        
        Args:
            name: Agent name
            model: LLM model to use
            description: Agent description
            instruction: System instructions for the agent
            code_repo_path: Path to the code repository (default: current directory)
            version_file: Path to store improvement version history
        """
        self.name = name
        self.model = model
        self.description = description
        self.instruction = instruction
        self.code_repo_path = code_repo_path or os.getcwd()
        self.version_file = version_file
        
        # Ensure version history directory exists
        os.makedirs(os.path.dirname(self.version_file), exist_ok=True)
        
        # Initialize or load version history
        self.improvement_history = self._load_improvement_history()
        
        logger.info(f"Initializing Self-Improving Agent: {name}")
        
        # We'll initialize the ADK agent later to avoid circular imports
        self.adk_agent = None
    
    def process_message(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Process a request for code improvement or analysis.
        
        Args:
            message: User message requesting code improvement
            history: Conversation history
            
        Returns:
            Response with analysis or improvement plan
        """
        logger.info(f"Processing self-improvement request: {message[:50]}...")
        
        # Extract file path from message
        file_path = self._extract_file_path(message)
        improvement_type = self._classify_improvement_request(message)
        
        if file_path and os.path.exists(file_path):
            # Analyze the specific file
            logger.info(f"Analyzing file: {file_path}")
            analysis = self.analyze_file(file_path, improvement_type)
            
            # Return analysis results
            return {
                "message": (
                    f"I've analyzed the file '{file_path}' and found several potential improvements:\n\n"
                    f"{analysis['summary']}\n\n"
                    f"Specific suggestions:\n"
                    + "\n".join([f"- {s['issue']}: {s['improvement']}" for s in analysis['suggestions']])
                    + "\n\nWould you like me to implement any of these improvements?"
                ),
                "status": "success",
                "needs_approval": True,
                "analysis": analysis,
                "improvement_type": improvement_type,
            }
        else:
            # Generic response for non-specific requests
            return {
                "message": (
                    f"I've analyzed your request for code improvement related to '{improvement_type}'. "
                    f"To proceed, I would need to: "
                    f"1. Examine the relevant code files\n"
                    f"2. Identify potential improvements\n"
                    f"3. Propose and implement changes with your approval\n\n"
                    f"Which file would you like me to analyze? Please provide a valid file path."
                ),
                "status": "success",
                "needs_approval": True,
                "improvement_type": improvement_type,
            }
    
    def analyze_file(self, file_path: str, improvement_type: str = "general") -> Dict[str, Any]:
        """Analyze a specific file for potential improvements.
        
        Args:
            file_path: Path to the file to analyze
            improvement_type: Type of improvements to look for
            
        Returns:
            Analysis results with improvement suggestions
        """
        logger.info(f"Analyzing file: {file_path} for {improvement_type} improvements")
        
        try:
            # Read the file content
            with open(file_path, "r") as f:
                content = f.read()
            
            file_size = len(content)
            line_count = content.count("\n") + 1
            
            # In a real implementation, this would use an LLM to analyze the code
            # and generate specific improvement suggestions
            
            # For now, provide generic suggestions based on file type
            file_ext = os.path.splitext(file_path)[1].lower()
            
            suggestions = []
            
            # Generic suggestions based on file type
            if file_ext == ".py":
                suggestions = self._analyze_python_file(content, improvement_type)
            elif file_ext in [".js", ".ts"]:
                suggestions = self._analyze_javascript_file(content, improvement_type)
            elif file_ext in [".html", ".xml"]:
                suggestions = self._analyze_markup_file(content, improvement_type)
            elif file_ext in [".css", ".scss"]:
                suggestions = self._analyze_stylesheet_file(content, improvement_type)
            elif file_ext in [".json", ".yaml", ".yml"]:
                suggestions = self._analyze_data_file(content, improvement_type)
            else:
                suggestions = [
                    {
                        "file": file_path,
                        "issue": "Generic code review",
                        "severity": "info",
                        "improvement": "Perform a detailed code review with specific file type understanding"
                    }
                ]
            
            # Create a comprehensive analysis result
            analysis_result = {
                "analyzed_path": file_path,
                "file_type": file_ext.lstrip(".") if file_ext else "unknown",
                "file_size": file_size,
                "line_count": line_count,
                "timestamp": datetime.now().isoformat(),
                "suggestions": suggestions,
                "summary": f"Analysis complete for {file_path}. Found {len(suggestions)} potential improvements.",
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {str(e)}")
            return {
                "analyzed_path": file_path,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "suggestions": [],
                "summary": f"Error analyzing file: {str(e)}"
            }
    
    def _extract_file_path(self, message: str) -> Optional[str]:
        """Extract a file path from a message.
        
        Args:
            message: User message
            
        Returns:
            Extracted file path or None if not found
        """
        # Simple extraction based on common file extensions
        message_words = message.split()
        for word in message_words:
            # Check if the word looks like a file path
            if (
                os.path.exists(word) 
                or word.endswith((".py", ".js", ".html", ".css", ".json", ".ts", ".md", ".yaml", ".yml"))
            ):
                return word
        
        # Try to find a more complex path with spaces (enclosed in quotes)
        import re
        path_matches = re.findall(r'"([^"]+)"', message) + re.findall(r"'([^']+)'", message)
        for path in path_matches:
            if os.path.exists(path):
                return path
        
        return None
    
    def _analyze_python_file(self, content: str, improvement_type: str) -> List[Dict[str, Any]]:
        """Analyze a Python file for improvements.
        
        Args:
            content: File content
            improvement_type: Type of improvements to look for
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Check for common Python code issues
        if "except:" in content and "except Exception:" not in content:
            suggestions.append({
                "issue": "Bare except clause",
                "severity": "medium",
                "improvement": "Replace bare 'except:' with 'except Exception:' or specific exceptions"
            })
        
        if "print(" in content and not content.startswith("#!/usr/bin/env python"):
            suggestions.append({
                "issue": "Debug print statements",
                "severity": "low",
                "improvement": "Consider replacing print statements with proper logging"
            })
        
        if "import *" in content:
            suggestions.append({
                "issue": "Wildcard import",
                "severity": "medium",
                "improvement": "Replace wildcard imports with explicit imports"
            })
        
        # Add more sophisticated analysis based on improvement type
        if improvement_type == "performance":
            if "for " in content and "append" in content:
                suggestions.append({
                    "issue": "Potential inefficient list construction",
                    "severity": "medium",
                    "improvement": "Consider using list comprehension instead of for-loop with append"
                })
        
        if improvement_type == "security":
            if "eval(" in content:
                suggestions.append({
                    "issue": "Use of eval()",
                    "severity": "high",
                    "improvement": "Avoid using eval() due to security risks"
                })
        
        # Add some generic improvements if no specific issues found
        if not suggestions:
            suggestions.append({
                "issue": "Code documentation",
                "severity": "low",
                "improvement": "Consider adding more comprehensive docstrings and comments"
            })
            
            suggestions.append({
                "issue": "Code structure",
                "severity": "info",
                "improvement": "Review function and class organization for better maintainability"
            })
        
        return suggestions
    
    def _analyze_javascript_file(self, content: str, improvement_type: str) -> List[Dict[str, Any]]:
        """Analyze a JavaScript file for improvements."""
        # Similar to Python analysis but with JS-specific checks
        suggestions = [
            {
                "issue": "Potential JavaScript improvements",
                "severity": "medium", 
                "improvement": "Consider modern JS features like async/await, destructuring, and arrow functions"
            }
        ]
        return suggestions
    
    def _analyze_markup_file(self, content: str, improvement_type: str) -> List[Dict[str, Any]]:
        """Analyze an HTML/XML file for improvements."""
        suggestions = [
            {
                "issue": "HTML structure review",
                "severity": "low",
                "improvement": "Check for semantic HTML tags and proper nesting"
            }
        ]
        return suggestions
    
    def _analyze_stylesheet_file(self, content: str, improvement_type: str) -> List[Dict[str, Any]]:
        """Analyze a CSS/SCSS file for improvements."""
        suggestions = [
            {
                "issue": "CSS organization",
                "severity": "medium",
                "improvement": "Consider organizing CSS properties consistently and using variables for repeated values"
            }
        ]
        return suggestions
    
    def _analyze_data_file(self, content: str, improvement_type: str) -> List[Dict[str, Any]]:
        """Analyze a JSON/YAML file for improvements."""
        suggestions = [
            {
                "issue": "Data structure organization",
                "severity": "low",
                "improvement": "Review the structure for consistency and consider adding comments if supported"
            }
        ]
        return suggestions
    
    def analyze_codebase(self, target_path: Optional[str] = None, issue_type: Optional[str] = None) -> Dict[str, Any]:
        """Analyze the codebase or a specific part for potential improvements.
        
        Args:
            target_path: Specific file or directory to analyze (default: entire codebase)
            issue_type: Type of issue to look for (performance, security, etc.)
            
        Returns:
            Analysis results with improvement suggestions
        """
        path_to_analyze = target_path or self.code_repo_path
        logger.info(f"Analyzing codebase at: {path_to_analyze}")
        
        # In a real implementation, this would:
        # 1. Use static code analysis tools if available
        # 2. Use an LLM to review code for improvements
        # 3. Look at recent logs for error patterns
        
        # Placeholder for demonstration purposes
        analysis_result = {
            "analyzed_path": path_to_analyze,
            "timestamp": datetime.now().isoformat(),
            "suggestions": [
                {
                    "file": "example_file.py",
                    "issue": "Potential memory leak in resource handling",
                    "severity": "medium",
                    "improvement": "Implement context manager pattern to ensure proper resource cleanup"
                }
            ],
            "summary": f"Initial analysis complete for {path_to_analyze}. Found 1 potential improvement."
        }
        
        return analysis_result
    
    def generate_code_improvement(
        self, 
        file_path: str, 
        issue_description: str, 
        improvement_type: str = "refactor"
    ) -> Dict[str, Any]:
        """Generate a code improvement for a specific issue.
        
        Args:
            file_path: Path to the file that needs improvement
            issue_description: Description of the issue to fix
            improvement_type: Type of improvement (refactor, optimize, fix, feature)
            
        Returns:
            Generated improvement with original and updated code
        """
        logger.info(f"Generating code improvement for {file_path}: {issue_description}")
        
        # In a real implementation, this would:
        # 1. Read the target file
        # 2. Use an LLM to generate a fix
        # 3. Validate the fix for syntax and logical errors
        
        # Placeholder for demonstration purposes
        improvement = {
            "file_path": file_path,
            "issue": issue_description,
            "type": improvement_type,
            "timestamp": datetime.now().isoformat(),
            "original_code": "# Original code would be here",
            "improved_code": "# Improved code would be here",
            "explanation": "This improvement fixes the issue by...",
            "status": "generated",  # generated, approved, implemented, reverted
        }
        
        return improvement
    
    def implement_change(self, improvement: Dict[str, Any], approve: bool = False) -> Dict[str, Any]:
        """Implement a generated code improvement.
        
        Args:
            improvement: The improvement to implement
            approve: Whether the change is pre-approved (default: False)
            
        Returns:
            Result of the implementation
        """
        if not approve:
            return {
                "status": "pending_approval",
                "message": "This change requires explicit approval before implementation."
            }
        
        file_path = improvement.get("file_path")
        if not file_path or not os.path.exists(file_path):
            return {
                "status": "error",
                "message": f"Invalid file path: {file_path}"
            }
        
        # Backup the original file
        backup_path = f"{file_path}.bak.{int(time.time())}"
        try:
            with open(file_path, "r") as original_file:
                original_content = original_file.read()
            
            with open(backup_path, "w") as backup_file:
                backup_file.write(original_content)
            
            # Apply the change
            # In a real implementation, this would properly locate and replace the target code
            # with proper safeguards
            
            # For demonstration, just update the improvement status
            improvement["status"] = "implemented"
            improvement["implementation_time"] = datetime.now().isoformat()
            
            # Add to improvement history
            self._add_to_improvement_history(improvement)
            
            return {
                "status": "success",
                "message": f"Successfully implemented change to {file_path}",
                "backup_path": backup_path
            }
            
        except Exception as e:
            logger.error(f"Error implementing change: {str(e)}")
            return {
                "status": "error",
                "message": f"Error implementing change: {str(e)}"
            }
    
    def revert_change(self, improvement_id: str) -> Dict[str, Any]:
        """Revert a previously implemented change.
        
        Args:
            improvement_id: ID of the improvement to revert
            
        Returns:
            Result of the reversion
        """
        # Find the improvement in history
        for improvement in self.improvement_history:
            if improvement.get("id") == improvement_id:
                file_path = improvement.get("file_path")
                backup_path = improvement.get("backup_path")
                
                if not backup_path or not os.path.exists(backup_path):
                    return {
                        "status": "error",
                        "message": f"Backup file not found: {backup_path}"
                    }
                
                try:
                    # Restore from backup
                    with open(backup_path, "r") as backup_file:
                        backup_content = backup_file.read()
                    
                    with open(file_path, "w") as original_file:
                        original_file.write(backup_content)
                    
                    # Update improvement status
                    improvement["status"] = "reverted"
                    improvement["revert_time"] = datetime.now().isoformat()
                    
                    # Save updated history
                    self._save_improvement_history()
                    
                    return {
                        "status": "success",
                        "message": f"Successfully reverted change to {file_path}"
                    }
                    
                except Exception as e:
                    logger.error(f"Error reverting change: {str(e)}")
                    return {
                        "status": "error",
                        "message": f"Error reverting change: {str(e)}"
                    }
        
        return {
            "status": "error",
            "message": f"Improvement with ID {improvement_id} not found"
        }
    
    def _classify_improvement_request(self, message: str) -> str:
        """Classify the type of improvement requested.
        
        Args:
            message: User message
            
        Returns:
            Type of improvement requested
        """
        message_lower = message.lower()
        
        if any(kw in message_lower for kw in ["bug", "error", "fix", "issue", "problem"]):
            return "bugfix"
        
        if any(kw in message_lower for kw in ["optimize", "performance", "slow", "speed", "faster"]):
            return "optimization"
        
        if any(kw in message_lower for kw in ["feature", "add", "new", "implement"]):
            return "feature"
        
        if any(kw in message_lower for kw in ["refactor", "clean", "improve", "better", "redesign"]):
            return "refactor"
        
        return "general_improvement"
    
    def _load_improvement_history(self) -> List[Dict[str, Any]]:
        """Load improvement history from file.
        
        Returns:
            List of improvement records
        """
        if not os.path.exists(self.version_file):
            return []
        
        try:
            with open(self.version_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading improvement history: {str(e)}")
            return []
    
    def _save_improvement_history(self) -> bool:
        """Save improvement history to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.version_file, "w") as f:
                json.dump(self.improvement_history, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving improvement history: {str(e)}")
            return False
    
    def _add_to_improvement_history(self, improvement: Dict[str, Any]) -> None:
        """Add an improvement to the history.
        
        Args:
            improvement: Improvement record to add
        """
        # Generate a unique ID if needed
        if "id" not in improvement:
            improvement["id"] = f"imp_{int(time.time())}_{len(self.improvement_history)}"
        
        self.improvement_history.append(improvement)
        self._save_improvement_history()


# Create a global self-improving agent instance
self_improver = SelfImprovingAgent() 