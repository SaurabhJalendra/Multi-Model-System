"""SKAI Conversation Mode.

A simplified script to start SKAI in conversation mode.
"""

import os
import sys
import time
import threading

# Add the parent directory to the path so we can import SKAI modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from skai.agents.voice import voice
from skai.kernel.agent import kernel
from skai.utils.logging import get_skai_logger

# Setup logger
logger = get_skai_logger("conversation")

def main():
    """Main entry point."""
    print("\n" + "=" * 50)
    print("SKAI Conversation Mode")
    print("=" * 50)
    print("Starting initialization...")
    
    # Check voice capabilities
    if not hasattr(voice, 'recognizer') or voice.recognizer is None:
        print("\nERROR: Voice input is not available. Please install SpeechRecognition and PyAudio.")
        return 1
    
    if not hasattr(voice, 'tts') or voice.tts is None:
        print("\nERROR: Voice output is not available. Please install pyttsx3.")
        return 1
    
    print("Voice capabilities OK. Testing microphone...")
    
    # Test microphone
    try:
        import speech_recognition as sr
        with sr.Microphone() as source:
            print("Calibrating for ambient noise... (please be quiet)")
            voice.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Microphone access successful")
    except Exception as e:
        print(f"\nERROR: Failed to access microphone: {e}")
        print("Please check your microphone settings and permissions.")
        return 1
    
    print("\nAll checks passed. Starting conversation...")
    print("\nSay 'exit conversation' at any time to end the conversation.")
    
    # Start conversation
    conversation_history = []
    active = True
    
    # Greeting
    greeting = "Hello! I'm SKAI. How can I help you today?"
    print(f"\nSKAI: {greeting}")
    try:
        voice.speak(greeting)
    except Exception as e:
        print(f"Error speaking: {e}")
    
    while active:
        try:
            # Listen for user input
            print("\nListening...")
            listen_result = voice.listen(timeout=5, phrase_time_limit=10)
            
            if listen_result["status"] == "success":
                user_input = listen_result["text"]
                print(f"\nYou: {user_input}")
                
                # Add to conversation history
                conversation_history.append({"role": "user", "content": user_input})
                
                # Check for exit command
                if user_input.lower() in ["exit", "quit", "stop", "exit conversation", "end conversation"]:
                    print("\nExiting conversation mode.")
                    active = False
                    break
                
                # Process the input
                print("\nProcessing...")
                
                # The kernel doesn't accept history directly, so we'll work around it
                # by including the conversation history in the session
                # Process the input without passing history directly
                response = kernel.process_message(user_input)
                
                # Add to conversation history
                response_text = response["message"]
                conversation_history.append({"role": "assistant", "content": response_text})
                
                # Output the response
                print(f"\nSKAI: {response_text}")
                try:
                    voice.speak(response_text)
                except Exception as e:
                    print(f"Error speaking: {e}")
                
            elif listen_result["status"] == "timeout":
                print("\nI didn't hear anything. Please speak again or say 'exit conversation' to end.")
                continue
            else:
                if "error" in listen_result:
                    print(f"\nError: {listen_result['error']}")
                    time.sleep(2)
                    continue
        except KeyboardInterrupt:
            print("\n\nInterrupted. Exiting conversation mode.")
            active = False
            break
        except Exception as e:
            print(f"\nError in conversation: {e}")
            time.sleep(1)
    
    print("\nConversation ended. Thank you for using SKAI!")
    return 0

if __name__ == "__main__":
    # Import here to ensure the agents are set up
    from skai.agents.communicator import communicator
    from skai.agents.research import researcher
    
    # Register agents with the kernel if not already registered
    if "communicator_agent" not in kernel.agents:
        kernel.register_agent("communicator_agent", communicator)
    if "research_agent" not in kernel.agents:
        kernel.register_agent("research_agent", researcher)
    
    sys.exit(main()) 