"""Coding Agent for SKAI.

The Coding Agent is responsible for generating, explaining, and debugging code
across multiple programming languages.
"""

import time
from typing import Any, Dict, List, Optional, Union

from skai.config.settings import config
from skai.utils.logging import get_skai_logger

logger = get_skai_logger("agents.coding")


class CodingAgent:
    """Agent for handling code-related tasks.
    
    The Coding Agent can:
    - Generate code based on requirements
    - Explain existing code
    - Debug issues in code
    - Suggest code improvements
    """
    
    def __init__(
        self,
        name: str = "coding_agent",
        model: str = "tngtech/deepseek-r1t-chimera:free",  # Strong code model
        description: str = "Agent that handles code-related tasks",
        instruction: str = (
            "You are a coding expert responsible for generating, explaining, "
            "and debugging code in multiple programming languages. "
            "Prioritize clean, maintainable, and well-documented code."
        ),
    ):
        """Initialize Coding Agent.
        
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
        
        logger.info(f"Initializing Coding Agent: {name}")
        
        # Define coding tools
        def generate_code(
            language: str,
            task_description: str,
            include_comments: bool = True,
            use_libraries: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """Generate code based on task description.
            
            Args:
                language: Programming language to generate code in
                task_description: Description of what the code should do
                include_comments: Whether to include comments in the code
                use_libraries: Specific libraries to use
                
            Returns:
                Generated code and explanation
            """
            logger.info(f"Generating {language} code for: {task_description[:50]}...")
            
            # This is a placeholder. In a real implementation, this would call an LLM
            # to generate code. For now, we'll return mock results.
            
            # Simulate generation delay
            time.sleep(2)
            
            # Very simple mock examples
            examples = {
                "python": {
                    "code": f"""# Function to {task_description}
def process_data(data):
    \"\"\"
    Process the given data as required.
    
    Args:
        data: The data to process
        
    Returns:
        Processed data
    \"\"\"
    result = []
    
    # Process each item in the data
    for item in data:
        # Transform the item
        processed_item = item * 2
        result.append(processed_item)
        
    return result

# Example usage
if __name__ == "__main__":
    sample_data = [1, 2, 3, 4, 5]
    print(process_data(sample_data))
""",
                    "explanation": f"This Python code defines a function to process data by doubling each value. It includes proper documentation and an example usage.",
                },
                "javascript": {
                    "code": f"""/**
 * Function to {task_description}
 * @param {{Array}} data - The data to process
 * @returns {{Array}} - The processed data
 */
function processData(data) {{
    const result = [];
    
    // Process each item in the data
    for (const item of data) {{
        // Transform the item
        const processedItem = item * 2;
        result.push(processedItem);
    }}
    
    return result;
}}

// Example usage
const sampleData = [1, 2, 3, 4, 5];
console.log(processData(sampleData));
""",
                    "explanation": f"This JavaScript code defines a function to process data by doubling each value. It includes JSDoc documentation and an example usage.",
                },
                "java": {
                    "code": f"""import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Class to {task_description}
 */
public class DataProcessor {{
    /**
     * Process the given data as required.
     *
     * @param data The data to process
     * @return Processed data
     */
    public List<Integer> processData(List<Integer> data) {{
        List<Integer> result = new ArrayList<>();
        
        // Process each item in the data
        for (Integer item : data) {{
            // Transform the item
            Integer processedItem = item * 2;
            result.add(processedItem);
        }}
        
        return result;
    }}
    
    /**
     * Main method for example usage.
     */
    public static void main(String[] args) {{
        DataProcessor processor = new DataProcessor();
        List<Integer> sampleData = Arrays.asList(1, 2, 3, 4, 5);
        System.out.println(processor.processData(sampleData));
    }}
}}
""",
                    "explanation": f"This Java code defines a class with a method to process data by doubling each value. It includes Javadoc documentation and an example usage in the main method.",
                },
            }
            
            # Default to Python if language not found
            language = language.lower()
            if language not in examples:
                language = "python"
                
            code_example = examples[language]
            
            # If comments are not requested, strip them out
            if not include_comments:
                # Very simple comment removal (not comprehensive)
                if language == "python":
                    # Remove Python comments and docstrings
                    lines = code_example["code"].split("\n")
                    code_no_comments = []
                    in_docstring = False
                    for line in lines:
                        if '"""' in line:
                            in_docstring = not in_docstring
                            continue
                        if in_docstring:
                            continue
                        if not line.strip().startswith("#"):
                            code_no_comments.append(line)
                    code_example["code"] = "\n".join(code_no_comments)
                
                elif language in ["javascript", "java"]:
                    # Remove JS/Java comments
                    import re
                    code_example["code"] = re.sub(r'\/\*[\s\S]*?\*\/|\/\/.*', '', code_example["code"])
            
            # Add libraries if specified
            if use_libraries and len(use_libraries) > 0:
                if language == "python":
                    imports = "\n".join([f"import {lib}" for lib in use_libraries])
                    code_example["code"] = imports + "\n\n" + code_example["code"]
                    
                elif language == "javascript":
                    imports = "\n".join([f"const {lib.lower()} = require('{lib}');" for lib in use_libraries])
                    code_example["code"] = imports + "\n\n" + code_example["code"]
                    
                elif language == "java":
                    imports = "\n".join([f"import {lib};" for lib in use_libraries])
                    code_example["code"] = imports + "\n\n" + code_example["code"]
            
            return {
                "language": language,
                "code": code_example["code"],
                "explanation": code_example["explanation"],
                "task": task_description,
                "libraries_used": use_libraries or [],
            }
        
        def explain_code(code: str, level_of_detail: str = "medium") -> Dict[str, Any]:
            """Explain code in human-readable terms.
            
            Args:
                code: Code to explain
                level_of_detail: How detailed the explanation should be
                
            Returns:
                Explanation and analysis of the code
            """
            logger.info(f"Explaining code (detail level: {level_of_detail})...")
            
            # This is a placeholder. In a real implementation, this would call an LLM
            # to explain the code. For now, we'll return a simple explanation.
            
            # Simulate processing delay
            time.sleep(1)
            
            # Detect language
            language = "unknown"
            if "def " in code and ":" in code:
                language = "Python"
            elif "function " in code and "{" in code:
                language = "JavaScript"
            elif "public class" in code:
                language = "Java"
            
            # Generate explanation based on level of detail
            if level_of_detail == "high":
                explanation = f"This {language} code defines a function that processes data by iterating through each item, applying a transformation (doubling the value), and returning the results. It includes proper error handling, documentation, and follows best practices for {language} programming."
            elif level_of_detail == "low":
                explanation = f"This {language} code processes data by doubling each value."
            else:  # medium
                explanation = f"This {language} code defines a function that processes a list of values by doubling each one and returning the new list. It includes basic documentation and an example of how to use it."
            
            return {
                "language": language,
                "explanation": explanation,
                "complexity": "medium",
                "best_practices": ["Proper documentation", "Clear variable names", "Simple logic"],
                "potential_issues": ["No input validation", "No error handling"],
            }
        
        def debug_code(
            code: str,
            error_message: Optional[str] = None,
            language: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Debug issues in the provided code.
            
            Args:
                code: Code to debug
                error_message: Error message if available
                language: Programming language of the code
                
            Returns:
                Debug results and fixes
            """
            logger.info("Debugging code...")
            
            # This is a placeholder. In a real implementation, this would call an LLM
            # to debug the code. For now, we'll return mock results.
            
            # Simulate debugging delay
            time.sleep(1.5)
            
            # Detect language if not provided
            if not language:
                if "def " in code and ":" in code:
                    language = "python"
                elif "function " in code and "{" in code:
                    language = "javascript"
                elif "public class" in code:
                    language = "java"
                else:
                    language = "unknown"
            
            # Mock issues and fixes
            issues = [
                {
                    "line": 5,
                    "issue": "Potential division by zero",
                    "fix": "Add a check to ensure the divisor is not zero before division"
                },
                {
                    "line": 12,
                    "issue": "Unused variable",
                    "fix": "Remove the unused variable or use it in the code"
                },
            ]
            
            # If error message is provided, add specific fix
            if error_message:
                if "division by zero" in error_message.lower():
                    issues.append({
                        "line": 8,
                        "issue": "Division by zero error",
                        "fix": "Add a check: if denominator != 0 before dividing"
                    })
                elif "index out of range" in error_message.lower() or "index out of bounds" in error_message.lower():
                    issues.append({
                        "line": 10,
                        "issue": "Index out of bounds error",
                        "fix": "Add bounds checking before accessing array elements"
                    })
                elif "null" in error_message.lower() or "none" in error_message.lower():
                    issues.append({
                        "line": 3,
                        "issue": "Null/None reference error",
                        "fix": "Add null/None check before using the variable"
                    })
            
            # Generate fixed code (placeholder)
            fixed_code = code
            for issue in issues:
                # Very simple mock fixes (not actually fixing anything)
                if "division by zero" in issue["issue"].lower():
                    if language == "python":
                        line_to_add = "    if denominator != 0:  # Prevent division by zero"
                        fixed_code = fixed_code.replace("    result = numerator / denominator", f"{line_to_add}\n        result = numerator / denominator\n    else:\n        result = 0  # Default value when denominator is zero")
                
                elif "unused variable" in issue["issue"].lower():
                    # Just comment about the unused variable
                    fixed_code = fixed_code.replace("temp_value = 0", "# temp_value = 0  # Unused variable removed")
            
            return {
                "language": language,
                "issues": issues,
                "fixed_code": fixed_code,
                "explanation": "The code had potential issues with division by zero and unused variables. These have been addressed in the fixed version.",
            }
        
        # Store the tool functions
        self.generate_code = generate_code
        self.explain_code = explain_code
        self.debug_code = debug_code
    
    def process_message(self, message: str) -> Dict[str, Any]:
        """Process a user message to perform coding tasks.
        
        Args:
            message: User message
            
        Returns:
            Coding results
        """
        logger.info(f"Processing coding request: {message[:50]}...")
        
        # Simple intent detection (in real implementation, would use LLM)
        message_lower = message.lower()
        
        if any(kw in message_lower for kw in ["generate", "create", "write", "implement"]):
            # Detect language from the message
            language = "python"  # Default
            for lang in ["python", "javascript", "java", "c++", "typescript", "go", "rust"]:
                if lang in message_lower:
                    language = lang
                    break
            
            # Extract task description (simple approach)
            task_description = message
            for prefix in ["generate", "create", "write code", "implement"]:
                if prefix in message_lower:
                    parts = message.split(prefix, 1)
                    if len(parts) > 1:
                        task_description = parts[1].strip()
                        break
            
            # Generate code
            result = self.generate_code(language=language, task_description=task_description)
            
            return {
                "message": f"Here's the {language} code I've generated:\n\n```{language}\n{result['code']}\n```\n\n{result['explanation']}",
                "code": result["code"],
                "language": language,
                "task": task_description,
            }
            
        elif any(kw in message_lower for kw in ["explain", "understand", "what does", "how does"]):
            # Extract code from the message (assumes code is after "explain" or similar)
            code = message
            for prefix in ["explain", "understand", "what does", "how does"]:
                if prefix in message_lower:
                    parts = message.split(prefix, 1)
                    if len(parts) > 1:
                        code = parts[1].strip()
                        break
            
            # Explain code
            result = self.explain_code(code=code)
            
            return {
                "message": f"{result['explanation']}\n\nThe code appears to be written in {result['language']} and has a {result['complexity']} level of complexity.",
                "explanation": result["explanation"],
                "language": result["language"],
            }
            
        elif any(kw in message_lower for kw in ["debug", "fix", "error", "issue", "problem"]):
            # Extract code and error from the message
            code = message
            error_message = None
            
            # Look for errors
            if "error:" in message_lower:
                parts = message.split("error:", 1)
                if len(parts) > 1:
                    error_message = parts[1].strip()
                    code = parts[0].strip()
            
            # Debug code
            result = self.debug_code(code=code, error_message=error_message)
            
            return {
                "message": f"I've analyzed your code and found {len(result['issues'])} issues:\n\n" +
                           "\n".join([f"- Line {issue['line']}: {issue['issue']} - {issue['fix']}" for issue in result['issues']]) +
                           f"\n\nHere's the fixed code:\n\n```{result['language']}\n{result['fixed_code']}\n```",
                "issues": result["issues"],
                "fixed_code": result["fixed_code"],
            }
            
        else:
            # Generic coding help
            return {
                "message": "I can help with code generation, explanation, and debugging. Please specify what you'd like me to do with your code.",
                "capabilities": [
                    "Code generation in multiple languages",
                    "Code explanation",
                    "Debugging and fixing issues",
                ],
            }


# Create a global coding agent instance
coding = CodingAgent() 