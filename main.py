"""SKAI - Sentient Kernel Adaptive Intelligence.

Main entry point for the SKAI system.
"""

import argparse
import os
import sys
import time
import threading
import speech_recognition as sr

# Import our LLM modules directly
from skai.llm.agent import Agent

from skai.agents.communicator import communicator
from skai.agents.research import researcher
from skai.agents.voice import voice  # Import the voice agent
from skai.agents.self_improving import self_improver  # Import the self-improving agent
from skai.config.settings import config
from skai.kernel.agent import kernel
from skai.tools.weather_time import get_weather, get_current_time
from skai.tools.workflow import create_information_workflow, create_weather_info_workflow
from skai.tools.wake_word import initialize_wake_word_detector, get_wake_word_detector
from skai.utils.logging import get_skai_logger

# Set up logger
logger = get_skai_logger("main")

# Global variables for state
wake_word_detected = False
conversation_mode_enabled = False


def setup_agents():
    """Set up and register agents."""
    # Register tools with the kernel
    kernel.register_tool("get_weather", get_weather)
    kernel.register_tool("get_current_time", get_current_time)
    kernel.register_tool("create_information_workflow", create_information_workflow)
    kernel.register_tool("create_weather_info_workflow", create_weather_info_workflow)
    
    # Create and register the weather_time_agent using OpenRouter models
    weather_time_agent = Agent(
        name="weather_time_agent",
        model="meta-llama/llama-3.3-8b-instruct:free",  # Smaller FREE model for simple tasks
        description=(
            "Agent to answer questions about the time and weather in a city."
        ),
        instruction=(
            "You are a helpful agent who can answer user questions about the time and weather in a city."
        ),
        tools=[get_weather, get_current_time],
    )
    
    # Register agents with the kernel
    kernel.register_agent("weather_time_agent", weather_time_agent)
    kernel.register_agent("communicator_agent", communicator)
    kernel.register_agent("research_agent", researcher)
    kernel.register_agent("voice_agent", voice)  # Register the voice agent
    kernel.register_agent("self_improving_agent", self_improver)  # Register the self-improving agent
    
    logger.info("Agents set up successfully")


def check_voice_capability():
    """Check if voice input/output capabilities are available.
    
    Returns:
        tuple: (input_available, output_available, error_message)
    """
    try:
        print("\nChecking voice capabilities...")
        
        # Check speech recognition availability
        if not hasattr(voice, 'recognizer') or voice.recognizer is None:
            print("  Voice input NOT available (speech recognition issue)")
            logger.warning("Voice input not available - speech recognition issue")
            input_available = False
        else:
            print("  Voice input available (speech recognition OK)")
            logger.info("Voice input available (speech recognition OK)")
            input_available = True
            
        # Check TTS availability    
        if not hasattr(voice, 'tts') or voice.tts is None:
            print("  Voice output NOT available (text-to-speech issue)")
            logger.warning("Voice output not available - TTS issue")
            output_available = False
        else:
            print("  Voice output available (text-to-speech OK)")
            logger.info("Voice output available (text-to-speech OK)")
            output_available = True
        
        # Determine error message
        error_message = None
        if not input_available and not output_available:
            error_message = (
                "Voice capabilities are not available. "
                "Please install the required packages:\n"
                "- SpeechRecognition and PyAudio for voice input\n"
                "- pyttsx3 for basic voice output\n"
                "- TTS (Coqui) or Piper for advanced voice output"
            )
        elif not input_available:
            error_message = (
                "Voice input is not available. "
                "Please install SpeechRecognition and PyAudio."
            )
        elif not output_available:
            error_message = (
                "Voice output is not available. "
                "Please install at least one of: pyttsx3, TTS, or Piper."
            )
            
        # Log results
        if error_message:
            print(f"  ERROR: {error_message}")
            logger.warning(f"Voice capability error: {error_message}")
        else:
            print("  All voice capabilities are OK")
            logger.info("All voice capabilities are available")
            
        return input_available, output_available, error_message
        
    except Exception as e:
        logger.error(f"Error checking voice capabilities: {e}", exc_info=True)
        print(f"\nError checking voice capabilities: {e}")
        return False, False, f"Error checking voice capabilities: {e}"


def check_wake_word_capability():
    """Check if wake word detection is available.
    
    Returns:
        tuple: (available, error_message)
    """
    try:
        import pvporcupine
        import pvrecorder
        available = True
        error_message = None
    except ImportError:
        available = False
        error_message = (
            "Wake word detection is not available. "
            "Please install the required packages:\n"
            "- pip install pvporcupine pvrecorder\n"
            "- You'll also need a Picovoice AccessKey (register at console.picovoice.ai)"
        )
    
    return available, error_message


def wake_word_callback(keyword):
    """Callback function when wake word is detected."""
    logger.info(f"Wake word detected: {keyword}")
    print("\n" + "=" * 50)
    print(f"🎤 WAKE WORD DETECTED: '{keyword}'")
    print("=" * 50)
    
    # This function will be called from a different thread
    # The actual handling happens in the main loop
    
    # Set a flag that wake word was detected
    global wake_word_detected
    wake_word_detected = True
    
    # If we're already in conversation mode, the conversation 
    # loop will handle this via its own check
    

def run_cli():
    """Run the CLI interface."""
    print("\n" + "=" * 50)
    print("SKAI - Sentient Kernel Adaptive Intelligence")
    print("=" * 50)
    print("Type 'exit' or 'quit' to exit.")
    print("Type 'help' for available commands.")
    print("=" * 50 + "\n")
    
    # Check voice capabilities
    voice_input, voice_output, voice_error = check_voice_capability()
    if not voice_input or not voice_output:
        logger.warning(f"Limited voice capabilities: {voice_error}")
    
    # Check wake word capabilities
    wake_word_available, wake_word_error = check_wake_word_capability()
    if not wake_word_available:
        logger.warning(f"Wake word detection unavailable: {wake_word_error}")
    
    # Initialize wake word detector if available
    wake_word_detector = None
    if wake_word_available:
        # Try to find custom wake word model
        custom_wake_word_path = "hey-sky/hey-sky-windows.ppn"
        if not os.path.exists(custom_wake_word_path) and os.path.exists("hey-sky"):
            # Try to find any .ppn file in the hey-sky directory
            ppn_files = [os.path.join("hey-sky", f) for f in os.listdir("hey-sky") if f.endswith(".ppn")]
            if ppn_files:
                custom_wake_word_path = ppn_files[0]
                
        if os.path.exists(custom_wake_word_path):
            wake_word_detector = initialize_wake_word_detector(
                wake_word_callback, 
                keyword_path=custom_wake_word_path
            )
        else:
            wake_word_detector = initialize_wake_word_detector(wake_word_callback)
    
    session_id = None  # Will be generated on first message
    voice_mode = False  # Track if we're in voice mode
    wake_word_mode = False  # Track if wake word detection is active
    
    # Global flag to track wake word detection
    global wake_word_detected
    wake_word_detected = False
    
    while True:
        try:
            # Handle wake word detection if active
            if wake_word_mode and wake_word_detected:
                print("\n🔊 Wake word detected! Listening...")
                wake_word_detected = False  # Reset flag
                
                # Check if we are already in conversation mode
                if conversation_mode_enabled and voice.is_in_conversation_mode():
                    # The conversation loop will handle this
                    print("Continuing conversation...")
                    continue
                
                # Otherwise start a new conversation or single command
                if os.getenv("WAKE_WORD_CONVERSATION_MODE", "false").lower() == "true":
                    # Auto-start conversation mode
                    conversation_mode_enabled = True
                    print("\nStarting conversation mode...")
                    voice.start_conversation_mode()
                    continue
                else:
                    # Switch to listen for a command after wake word
                    listen_result = voice.listen(timeout=5, phrase_time_limit=10)
                    
                    if listen_result["status"] == "success":
                        user_input = listen_result["text"]
                        print(f"\nYou (voice): {user_input}")
                        
                        # Check if user wants to exit wake word mode
                        if user_input.lower() in ["exit wake word", "stop listening", "turn off wake word"]:
                            wake_word_mode = False
                            if wake_word_detector:
                                wake_word_detector.stop()
                            print("\nWake word detection disabled.")
                            continue
                        
                        # Check if user wants to start conversation mode
                        if user_input.lower() in ["start conversation", "conversation mode", "chat mode", "let's talk"]:
                            conversation_mode_enabled = True
                            print("\nStarting conversation mode...")
                            voice.start_conversation_mode()
                            continue
                    else:
                        # If there was an error with voice input, print it and continue
                        if "error" in listen_result:
                            print(f"\nVoice input error: {listen_result['error']}")
                        else:
                            print("\nNo speech detected. Please try again.")
                        continue
            else:
                # If in voice mode, listen for input instead of reading from console
                if voice_mode:
                    if not voice_input:
                        print("\nVoice input is not available. Exiting voice mode.")
                        voice_mode = False
                        continue
                        
                    print("\nListening... (say 'exit voice mode' to return to text, or press Ctrl+C)")
                    listen_result = voice.listen(timeout=5, phrase_time_limit=10)
                    
                    if listen_result["status"] == "success":
                        user_input = listen_result["text"]
                        print(f"\nYou (voice): {user_input}")
                        
                        # Check if user wants to exit voice mode
                        if user_input.lower() in ["exit voice mode", "exit voice", "stop listening"]:
                            voice_mode = False
                            print("\nExiting voice mode. Returning to text input.")
                            continue
                    else:
                        # If there was an error with voice input, print it and continue
                        if "error" in listen_result:
                            print(f"\nVoice input error: {listen_result['error']}")
                        else:
                            print("\nNo speech detected. Please try again.")
                        continue
                else:
                    # Normal text input
                    user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ["exit", "quit"]:
                # Ensure we stop wake word detection when exiting
                if wake_word_mode and wake_word_detector:
                    wake_word_detector.stop()
                print("\nExiting SKAI. Goodbye!")
                break
            
            if user_input.lower() == "help":
                print("\nAvailable commands:")
                print("  help - Show this help message")
                print("  exit/quit - Exit SKAI")
                print("  clear - Clear the screen")
                print("  session - Show current session information")
                print("  agents - List available agents")
                
                # Only show voice commands if capabilities are available
                if voice_input:
                    print("  voice mode - Enter voice interaction mode")
                    print("  listen - Listen for voice input once")
                    print("  conversation - Start ChatGPT-like voice conversation")
                if voice_output:
                    print("  say <text> - Convert text to speech")
                if not voice_input and not voice_output:
                    print("  (Voice commands unavailable - install voice dependencies)")
                
                # Only show wake word commands if capability is available
                if wake_word_available:
                    print("  wake word on - Enable 'Hey Sky' wake word detection")
                    print("  wake word off - Disable wake word detection")
                else:
                    print("  (Wake word detection unavailable - install pvporcupine and pvrecorder)")
                    
                print("  workflow <topic> - Run an information workflow")
                print("  weather-info <city> - Run weather+info workflow")
                print("  improve <file_path> - Analyze and suggest improvements for a file")
                print("\nYou can ask about:")
                print("  - Weather in a city (e.g., 'What's the weather in New York?')")
                print("  - Current time in a city (e.g., 'What time is it in London?')")
                print("  - General information (e.g., 'Tell me about climate change')")
                print("  - Code improvements (e.g., 'Can you improve the error handling in state.py?')")
                continue
            
            if user_input.lower() == "clear":
                os.system("cls" if os.name == "nt" else "clear")
                continue
            
            if user_input.lower() == "session":
                if session_id:
                    print(f"\nCurrent session ID: {session_id}")
                else:
                    print("\nNo active session yet.")
                continue
            
            if user_input.lower() == "agents":
                print("\nAvailable agents:")
                for agent_name in kernel.agents:
                    print(f"  - {agent_name}")
                continue
            
            # Wake word commands
            if user_input.lower() in ["wake word on", "enable wake word"]:
                if not wake_word_available:
                    print("\nWake word detection is not available. Please install pvporcupine and pvrecorder packages.")
                    print("Run: pip install pvporcupine pvrecorder")
                    print("You'll also need a Picovoice AccessKey (register at console.picovoice.ai)")
                    continue
                
                if wake_word_mode:
                    print("\nWake word detection is already enabled.")
                    continue
                
                # Start wake word detection
                if wake_word_detector and wake_word_detector.start():
                    wake_word_mode = True
                    wake_phrase = "Hey Sky" if hasattr(wake_word_detector, "keyword_path") and wake_word_detector.keyword_path else "the wake word"
                    print(f"\nWake word detection enabled. Say '{wake_phrase}' to activate.")
                    print("Say 'wake word off' to disable wake word detection.")
                else:
                    print("\nFailed to start wake word detection. Check your Picovoice AccessKey.")
                continue
                
            if user_input.lower() in ["wake word off", "disable wake word"]:
                if not wake_word_mode:
                    print("\nWake word detection is not currently enabled.")
                    continue
                
                # Stop wake word detection
                if wake_word_detector:
                    wake_word_detector.stop()
                wake_word_mode = False
                print("\nWake word detection disabled.")
                continue
            
            # Voice commands
            if user_input.lower() == "voice mode":
                if not voice_input:
                    print("\nVoice input is not available. Please install SpeechRecognition and PyAudio packages.")
                    print("Run: pip install SpeechRecognition pyaudio")
                    continue
                    
                voice_mode = True
                print("\nEntering voice mode. Speak to interact with SKAI.")
                print("Say 'exit voice mode' to return to text input.")
                continue
            
            if user_input.lower() == "listen":
                if not voice_input:
                    print("\nVoice input is not available. Please install SpeechRecognition and PyAudio packages.")
                    print("Run: pip install SpeechRecognition pyaudio")
                    continue
                    
                print("\nListening for voice input...")
                listen_result = voice.listen()
                
                if listen_result["status"] == "success":
                    print(f"\nTranscribed: {listen_result['text']}")
                    user_input = listen_result["text"]
                else:
                    if "error" in listen_result:
                        print(f"\nVoice input error: {listen_result['error']}")
                    else:
                        print("\nNo speech detected. Please try again.")
                    continue
            
            if user_input.lower().startswith("say "):
                if not voice_output:
                    print("\nVoice output is not available. Please install at least one of: pyttsx3, TTS, or Piper.")
                    print("For basic output: pip install pyttsx3")
                    print("For advanced output: pip install TTS")
                    continue
                    
                text_to_speak = user_input[4:].strip()
                if text_to_speak:
                    print(f"\nConverting to speech: {text_to_speak}")
                    speak_result = voice.speak(text_to_speak)
                    
                    if speak_result["status"] != "success":
                        print(f"\nError converting to speech: {speak_result.get('error', 'Unknown error')}")
                else:
                    print("\nNo text provided to speak.")
                continue
                
            if user_input.lower().startswith("workflow "):
                topic = user_input[9:].strip()
                if not topic:
                    print("Please specify a topic for the workflow.")
                    continue
                    
                print(f"\nRunning information workflow for: {topic}")
                print("SKAI is thinking...")
                
                start_time = time.time()
                results = create_information_workflow(topic)
                
                # Update session ID
                session_id = results.get("session_id")
                
                # Print results
                response_text = results['message']
                print(f"\nSKAI: {response_text}")
                
                # If in voice mode, also speak the response
                if voice_mode and voice_output:
                    voice.process_message(response_text)
                
                if "workflow_results" in results:
                    for step in results["workflow_results"]:
                        if "sources" in step["result"]:
                            print("\nSources:")
                            for source in step["result"]["sources"]:
                                print(f"  - {source}")
                
                elapsed = time.time() - start_time
                print(f"\n[Workflow completed in {elapsed:.2f} seconds]")
                continue
                
            if user_input.lower().startswith("weather-info "):
                city = user_input[13:].strip()
                if not city:
                    print("Please specify a city for the weather-info workflow.")
                    continue
                    
                print(f"\nRunning weather+info workflow for: {city}")
                print("SKAI is thinking...")
                
                start_time = time.time()
                results = create_weather_info_workflow(city)
                
                # Update session ID
                session_id = results.get("session_id")
                
                # Print results
                response_text = results['message']
                print(f"\nSKAI: {response_text}")
                
                # If in voice mode, also speak the response
                if voice_mode and voice_output:
                    voice.process_message(response_text)
                
                elapsed = time.time() - start_time
                print(f"\n[Workflow completed in {elapsed:.2f} seconds]")
                continue
                
            # Handle code improvement requests
            if user_input.lower().startswith("improve "):
                file_path = user_input[8:].strip()
                if not file_path:
                    print("Please specify a file path to improve.")
                    continue
                
                # Check if file exists
                if not os.path.exists(file_path):
                    print(f"\nFile not found: {file_path}")
                    print("Please provide a valid file path.")
                    continue
                
                print(f"\nAnalyzing file for improvements: {file_path}")
                print("SKAI is thinking...")
                
                start_time = time.time()
                
                # Route directly to self-improving agent
                improvement_request = f"Analyze and suggest improvements for the file: {file_path}"
                results = kernel.route_to_agent("self_improving_agent", improvement_request, session_id)
                
                # Update session ID
                session_id = results.get("session_id")
                
                # Print results
                response_text = results['message']
                print(f"\nSKAI: {response_text}")
                
                # If in voice mode, also speak the response
                if voice_mode and voice_output:
                    voice.process_message(response_text)
                
                elapsed = time.time() - start_time
                print(f"\n[Analysis completed in {elapsed:.2f} seconds]")
                continue
                
            # Conversation mode command
            if user_input.lower() in ["conversation", "conversation mode", "chat mode", "chatgpt mode"]:
                if not voice_input or not voice_output:
                    print("\nVoice input/output is not available. Please install required voice packages.")
                    continue
                    
                conversation_mode_enabled = True
                print("\nStarting ChatGPT-like conversation mode...")
                print("Speak naturally with SKAI. Say 'exit conversation' to end.")
                voice.start_conversation_mode()
                continue
                
            if not user_input:
                continue
            
            # Process message
            start_time = time.time()
            print("\nSKAI is thinking...")
            
            response = kernel.process_message(user_input, session_id)
            
            # Save session ID for future messages
            session_id = response["session_id"]
            
            # Print response
            elapsed = time.time() - start_time
            response_text = response['message']
            print(f"\nSKAI: {response_text}")
            
            # If in voice mode, also speak the response
            if voice_mode and voice_output:
                voice.process_message(response_text)
            
            # Print additional information if available
            if "sources" in response and response["sources"]:
                print("\nSources:")
                for source in response["sources"]:
                    print(f"  - {source}")
            
            if "agent_used" in response:
                print(f"\n[Agent: {response['agent_used']}]")
                
            print(f"[Processed in {elapsed:.2f} seconds]")
            
        except KeyboardInterrupt:
            if voice_mode:
                voice_mode = False
                print("\n\nInterrupted. Exiting voice mode.")
                continue
            else:
                print("\n\nInterrupted by user. Exiting...")
                break
        except Exception as e:
            logger.error(f"Error processing input: {e}", exc_info=True)
            print(f"\nSKAI: I encountered an error while processing your request. Please try again.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="SKAI - Sentient Kernel Adaptive Intelligence")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--voice", action="store_true", help="Start in voice mode")
    parser.add_argument("--wake-word", action="store_true", help="Start with wake word detection")
    parser.add_argument("--wake-word-model", help="Path to custom wake word model (.ppn file)")
    parser.add_argument("--wake-word-sensitivity", type=float, default=0.7, 
                       help="Wake word detection sensitivity (0.0-1.0, higher is more sensitive)")
    parser.add_argument("--conversation", action="store_true",
                       help="Start in continuous conversation mode (ChatGPT-like)")
    args = parser.parse_args()
    
    if args.debug:
        logger.info("Debug mode enabled")
    
    try:
        # Setup agents
        setup_agents()
        
        # Check voice capability - Do this early since we need it for conversation mode too
        voice_input, voice_output, voice_error = check_voice_capability()
        
        # Check if starting in voice mode
        if args.voice:
            if not voice_input:
                print(f"\nError: Cannot start in voice mode. {voice_error}")
                print("Starting in regular text mode instead.\n")
                args.voice = False
        
        # Check wake word capability if starting with wake word detection
        if args.wake_word:
            wake_word_available, wake_word_error = check_wake_word_capability()
            if not wake_word_available:
                print(f"\nError: Cannot start with wake word detection. {wake_word_error}")
                print("Starting without wake word detection.\n")
                args.wake_word = False
        
        # Get custom wake word model path
        custom_wake_word_path = args.wake_word_model or "hey-sky/hey-sky-windows.ppn"
        if not os.path.exists(custom_wake_word_path) and custom_wake_word_path == "hey-sky/hey-sky-windows.ppn":
            logger.warning(f"Custom wake word model not found at {custom_wake_word_path}")
            if os.path.exists("hey-sky"):
                # Try to find any .ppn file in the hey-sky directory
                ppn_files = [os.path.join("hey-sky", f) for f in os.listdir("hey-sky") if f.endswith(".ppn")]
                if ppn_files:
                    custom_wake_word_path = ppn_files[0]
                    logger.info(f"Found custom wake word model: {custom_wake_word_path}")
            else:
                # Try to find the model file directly in the same directory
                if os.path.exists("Hey-Sky_en_windows_v3_0_0"):
                    # Check for the .ppn file in this directory
                    model_dir = "Hey-Sky_en_windows_v3_0_0"
                    ppn_files = [os.path.join(model_dir, f) for f in os.listdir(model_dir) if f.endswith(".ppn")]
                    if ppn_files:
                        custom_wake_word_path = ppn_files[0]
                        logger.info(f"Found custom wake word model in root directory: {custom_wake_word_path}")
                
                # Alternative search method
                ppn_files = [f for f in os.listdir() if f.endswith(".ppn")]
                if ppn_files:
                    custom_wake_word_path = ppn_files[0]
                    logger.info(f"Found custom wake word model in current directory: {custom_wake_word_path}")
        
        # Initialize wake word detection if needed
        if args.wake_word:
            # Log wake word settings
            print(f"\nWake word settings:")
            print(f"- Sensitivity: {args.wake_word_sensitivity} (0.0-1.0)")
            
            # Create detector with the specified sensitivity
            if os.path.exists(custom_wake_word_path):
                print(f"- Model: {custom_wake_word_path}")
                wake_word_detector = initialize_wake_word_detector(
                    callback=wake_word_callback,
                    keyword_path=custom_wake_word_path
                )
                # Manually set sensitivity
                if wake_word_detector:
                    wake_word_detector.sensitivity = args.wake_word_sensitivity
            else:
                print("- Model: Using built-in wake words")
                wake_word_detector = initialize_wake_word_detector(callback=wake_word_callback)
                # Manually set sensitivity
                if wake_word_detector:
                    wake_word_detector.sensitivity = args.wake_word_sensitivity
                
            if wake_word_detector:
                wake_word_detector.start()
                word_phrase = "Hey Sky" if os.path.exists(custom_wake_word_path) else "one of the built-in wake words"
                print(f"\nWake word detection enabled. Say '{word_phrase}' to activate.")
                
                # Test microphone levels
                print("\nTesting microphone levels...")
                print("Please speak normally for a few seconds to calibrate...")
        
        # Start conversation mode if requested
        if args.conversation:
            if not voice_input or not voice_output:
                print(f"\nError: Cannot start in conversation mode. {voice_error}")
                print("Starting in regular text mode instead.\n")
            else:
                try:
                    print("\nInitializing conversation mode...")
                    conversation_mode_enabled = True
                    print("  Voice input and output verified")
                    print("  Testing microphone access...")
                    
                    # Test microphone access
                    with sr.Microphone() as source:
                        print("  Microphone access successful")
                        print("  Testing speech recognition...")
                        voice.recognizer.adjust_for_ambient_noise(source, duration=1)
                        print("  Speech recognition OK")
                    
                    print("  All checks passed. Starting conversation mode!")
                    print("  Speak naturally with SKAI in a ChatGPT-like voice conversation.")
                    print("  Say 'exit conversation' to end the conversation mode.")
                    
                    # Start conversation mode after CLI initializes
                    threading.Timer(1.0, lambda: start_conversation_safely()).start()
                except Exception as e:
                    logger.error(f"Error initializing conversation mode: {e}", exc_info=True)
                    print(f"\nError initializing conversation mode: {e}")
                    print("Starting in regular text mode instead.\n")
                    conversation_mode_enabled = False
        
        # Run CLI
        run_cli()
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        print(f"An error occurred: {e}")
        return 1
    
    return 0


def start_conversation_safely():
    """Start conversation mode with error handling."""
    try:
        result = voice.start_conversation_mode()
        logger.info(f"Conversation mode started: {result}")
    except Exception as e:
        logger.error(f"Error starting conversation mode: {e}", exc_info=True)
        print(f"\nError starting conversation mode: {e}")


if __name__ == "__main__":
    sys.exit(main()) 