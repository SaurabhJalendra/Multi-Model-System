"""Voice Agent for SKAI.

The Voice Agent is responsible for handling all voice-related functionality, including:
1. Speech-to-text conversion (STT)
2. Text-to-speech conversion (TTS)
3. Voice activity detection
4. Voice sentiment analysis
"""

import time
from typing import Any, Dict, List, Optional, Union, Tuple
import os
import sys
import queue
import threading
import select

# Try to import voice dependencies, but gracefully handle missing ones
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    sr = None
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    from pydub import AudioSegment
    from pydub.playback import play
    PYDUB_AVAILABLE = True
except ImportError:
    AudioSegment = None
    play = None
    PYDUB_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    pyttsx3 = None
    PYTTSX3_AVAILABLE = False

# Check for advanced optional dependencies
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    whisper = None
    WHISPER_AVAILABLE = False

try:
    from TTS.api import TTS
    TTS_AVAILABLE = True
except ImportError:
    TTS = None
    TTS_AVAILABLE = False

from skai.config.settings import config
from skai.utils.logging import get_skai_logger

logger = get_skai_logger("agents.voice")


class VoiceAgent:
    """Voice Agent for SKAI.
    
    Handles speech-to-text (STT) and text-to-speech (TTS).
    """
    
    def __init__(self):
        """Initialize Voice Agent."""
        self.name = "voice_agent"
        
        # Set up STT
        stt_system = os.getenv("STT_SYSTEM", "system").lower()
        self.recognizer = sr.Recognizer()
        if stt_system == "whisper" and WHISPER_AVAILABLE:
            logger.info("Initializing Whisper STT")
            self.stt_system = "whisper"
        else:
            logger.info("Initializing system STT")
            self.stt_system = "system"
        
        # Set up TTS
        tts_system = os.getenv("TTS_SYSTEM", "system").lower()
        if tts_system == "coqui_tts" and TTS_AVAILABLE:
            logger.info("Initializing Coqui TTS")
            from TTS.api import TTS as CoquiTTS
            self.tts = CoquiTTS("tts_models/en/vctk/vits", gpu=False)
            self.tts_system = "coqui_tts"
        elif tts_system == "piper" and PIPER_AVAILABLE:
            logger.info("Initializing Piper TTS")
            from piper import PiperVoice
            self.tts = PiperVoice("en_US-vctk-medium.onnx", "en_US-vctk-medium.onnx.json")
            self.tts_system = "piper"
        else:
            logger.info("Initializing system TTS")
            self.tts = pyttsx3.init()
            self.tts_system = "system"
        
        # Voice streaming and conversation state
        self.streaming_enabled = PYDUB_AVAILABLE
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.speech_thread = None
        self.conversation_active = False
        self.last_user_speech_time = 0
        self.voice_activity_timeout = 10  # seconds
        
    def process_message(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Process a message for voice output.
        
        Args:
            message: Text message to process
            history: Conversation history (optional)
            
        Returns:
            Response dictionary with status
        """
        logger.info(f"Processing voice output: {message[:50]}...")
        
        # Speak the message
        result = self.speak(message, stream=True)
        
        return {
            "status": result["status"],
            "message": f"Voice output: {message[:50]}...",
            "error": result.get("error", None)
        }
    
    def speak(self, text: str, stream: bool = False) -> Dict[str, Any]:
        """Convert text to speech.
        
        Args:
            text: Text to convert to speech
            stream: Whether to stream the audio (for conversation mode)
            
        Returns:
            Status dictionary
        """
        if not self.tts:
            return {"status": "error", "error": "No TTS engine available"}
        
        try:
            # For streaming, we need to break the text into sentences
            if stream and self.streaming_enabled:
                return self._stream_speak(text)
            
            # Regular non-streaming speech
            if self.tts_system == "coqui_tts":
                # Coqui TTS
                output_file = "temp_speech.wav"
                self.tts.tts_to_file(text=text, file_path=output_file)
                self._play_audio_file(output_file)
                try:
                    os.remove(output_file)
                except:
                    pass
            elif self.tts_system == "piper":
                # Piper
                output_file = "temp_speech.wav"
                with open(output_file, "wb") as f:
                    self.tts.synthesize(text, f)
                self._play_audio_file(output_file)
                try:
                    os.remove(output_file)
                except:
                    pass
            else:
                # System TTS
                self.tts.say(text)
                self.tts.runAndWait()
                
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"Error in TTS: {e}")
            return {"status": "error", "error": str(e)}
    
    def _stream_speak(self, text: str) -> Dict[str, Any]:
        """Stream speech output for more natural conversations.
        
        Args:
            text: Text to speak
            
        Returns:
            Status dictionary
        """
        try:
            # Split text into sentences for streaming
            sentences = self._split_into_sentences(text)
            
            # Queue up sentences for streaming
            for sentence in sentences:
                if sentence.strip():
                    self.speech_queue.put(sentence.strip())
            
            # Start the streaming thread if not already running
            if not self.is_speaking:
                self.is_speaking = True
                self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
                self.speech_thread.start()
                
            return {"status": "success", "streaming": True}
            
        except Exception as e:
            logger.error(f"Error in streaming TTS: {e}")
            return {"status": "error", "error": str(e)}
    
    def _speech_worker(self):
        """Background worker that processes speech queue."""
        try:
            while True:
                try:
                    # Get the next sentence from the queue with a timeout
                    sentence = self.speech_queue.get(timeout=0.5)
                    
                    # Speak the sentence
                    if self.tts_system == "coqui_tts":
                        # Coqui TTS
                        output_file = "temp_speech.wav"
                        self.tts.tts_to_file(text=sentence, file_path=output_file)
                        self._play_audio_file(output_file)
                        try:
                            os.remove(output_file)
                        except:
                            pass
                    elif self.tts_system == "piper":
                        # Piper
                        output_file = "temp_speech.wav"
                        with open(output_file, "wb") as f:
                            self.tts.synthesize(sentence, f)
                        self._play_audio_file(output_file)
                        try:
                            os.remove(output_file)
                        except:
                            pass
                    else:
                        # System TTS
                        self.tts.say(sentence)
                        self.tts.runAndWait()
                    
                    # Mark task as done
                    self.speech_queue.task_done()
                    
                except queue.Empty:
                    # If the queue is empty and no new items for a while, exit
                    if self.speech_queue.empty():
                        self.is_speaking = False
                        break
        except Exception as e:
            logger.error(f"Error in speech worker: {e}")
            self.is_speaking = False
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for better streaming.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Basic sentence splitting on punctuation
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return sentences
    
    def _play_audio_file(self, file_path: str):
        """Play an audio file.
        
        Args:
            file_path: Path to audio file
        """
        if PYDUB_AVAILABLE:
            # Use PyDub for better audio control
            try:
                from pydub import AudioSegment
                from pydub.playback import play
                
                sound = AudioSegment.from_wav(file_path)
                play(sound)
                return
            except Exception as e:
                logger.error(f"Error playing audio with PyDub: {e}")
        
        # Fallback to simpler playback
        if sys.platform == "win32":
            try:
                import winsound
                winsound.PlaySound(file_path, winsound.SND_FILENAME)
                return
            except:
                pass
                
        # Last resort using system commands
        try:
            if sys.platform == "darwin":  # macOS
                os.system(f"afplay {file_path}")
            else:  # Linux or other platforms
                os.system(f"aplay {file_path}")
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
    
    def listen(self, timeout: int = 5, phrase_time_limit: int = 10) -> Dict[str, Any]:
        """Listen for voice input.
        
        Args:
            timeout: Timeout in seconds for listening
            phrase_time_limit: Maximum phrase duration in seconds
            
        Returns:
            Dictionary with transcription or error
        """
        if not self.recognizer:
            return {"status": "error", "error": "No speech recognition engine available"}
        
        result = {"status": "error", "error": "Failed to initialize microphone"}
        
        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise
                print("\nCalibrating for ambient noise... (please be quiet)")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("Listening...")
                
                # Listen for input with timeout
                try:
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                    
                    # Update conversation state
                    self.last_user_speech_time = time.time()
                    self.conversation_active = True
                    
                except sr.WaitTimeoutError:
                    return {"status": "timeout", "error": "Listening timed out"}
                
                # Transcribe audio
                try:
                    if self.stt_system == "whisper":
                        # Whisper STT
                        import whisper
                        
                        # Save audio to temporary file
                        temp_file = "temp_audio.wav"
                        with open(temp_file, "wb") as f:
                            f.write(audio.get_wav_data())
                        
                        # Transcribe with Whisper
                        model = whisper.load_model("base")
                        result = model.transcribe(temp_file)
                        
                        # Clean up
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                        
                        return {"status": "success", "text": result["text"]}
                    else:
                        # System STT
                        text = self.recognizer.recognize_google(audio)
                        return {"status": "success", "text": text}
                except sr.UnknownValueError:
                    return {"status": "error", "error": "Could not understand audio"}
                except sr.RequestError as e:
                    return {"status": "error", "error": f"Recognition service error: {e}"}
                except Exception as e:
                    return {"status": "error", "error": f"Transcription error: {e}"}
                
        except Exception as e:
            logger.error(f"Error in speech recognition: {e}")
            result = {"status": "error", "error": str(e)}
            
        return result
    
    def start_conversation_mode(self) -> Dict[str, Any]:
        """Start a continuous conversation mode.
        
        Returns:
            Status dictionary
        """
        try:
            logger.info("Starting conversation mode")
            # First, check if we can access the microphone and speech recognition
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    logger.info("Microphone and speech recognition tested successfully")
            except Exception as e:
                logger.error(f"Failed to initialize microphone: {e}")
                return {"status": "error", "error": f"Failed to initialize microphone: {e}"}
            
            # Now check if TTS is working
            try:
                if self.tts_system == "system":
                    # Just check if initialized
                    if not self.tts:
                        logger.error("TTS not initialized")
                        return {"status": "error", "error": "Text-to-speech not initialized"}
                else:
                    # For other TTS systems, try to speak a short text
                    self.speak("Testing speech synthesis.", stream=False)
                logger.info("Text-to-speech tested successfully")
            except Exception as e:
                logger.error(f"Failed to initialize text-to-speech: {e}")
                return {"status": "error", "error": f"Failed to initialize text-to-speech: {e}"}
            
            # All checks passed, start the conversation
            self.conversation_active = True
            self.last_user_speech_time = time.time()
            
            # Start the conversation loop in a background thread
            threading.Thread(target=self._conversation_loop, daemon=True).start()
            
            return {"status": "success", "message": "Conversation mode started"}
        except Exception as e:
            logger.error(f"Failed to start conversation mode: {e}")
            return {"status": "error", "error": f"Failed to start conversation mode: {e}"}
    
    def stop_conversation_mode(self) -> Dict[str, Any]:
        """Stop the continuous conversation mode.
        
        Returns:
            Status dictionary
        """
        self.conversation_active = False
        return {"status": "success", "message": "Conversation mode stopped"}
    
    def _conversation_loop(self):
        """Background loop for continuous conversation mode."""
        try:
            conversation_history = []
            wait_for_wake_word = False
            
            # Print initial message
            print("\n" + "=" * 50)
            print("SKAI ChatGPT-like Conversation Mode")
            print("=" * 50)
            print("Speak naturally to have a conversation with SKAI")
            print("Say 'exit conversation' to end the session")
            print("=" * 50 + "\n")
            
            # Initial greeting
            greeting = "Hello! I'm SKAI. How can I help you today?"
            print(f"\nSKAI: {greeting}")
            
            # Try to speak the greeting, but don't fail if it doesn't work
            try:
                self.speak(greeting, stream=True)
            except Exception as e:
                logger.error(f"Error speaking greeting: {e}")
                print(f"Error speaking: {e}")
            
            while self.conversation_active:
                try:
                    # Check if the conversation has timed out due to inactivity
                    if time.time() - self.last_user_speech_time > self.voice_activity_timeout:
                        if not wait_for_wake_word:
                            timeout_message = "I haven't heard from you in a while. Say 'Hey Sky' if you'd like to continue our conversation."
                            print(f"\nSKAI: {timeout_message}")
                            try:
                                self.speak(timeout_message, stream=True)
                            except Exception as e:
                                logger.error(f"Error speaking timeout message: {e}")
                            wait_for_wake_word = True
                            # Reset timeout to allow a longer wait period
                            self.last_user_speech_time = time.time()
                        elif time.time() - self.last_user_speech_time > self.voice_activity_timeout * 2:
                            # If still no interaction after double the timeout, end the conversation
                            print("\nEnding conversation due to inactivity.")
                            self.conversation_active = False
                            break
                    
                    # Wait for the user to finish speaking before listening again
                    if self.is_speaking:
                        time.sleep(0.5)
                        continue
                    
                    # In wait_for_wake_word mode, check for wake word and don't listen otherwise
                    if wait_for_wake_word:
                        # Just sleep a bit and continue the loop
                        # The wake word should be handled externally in main.py
                        time.sleep(0.5)
                        
                        # Simple workaround - check if the user typed something
                        # This allows for keyboard input to continue the conversation
                        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                            user_text = input("You (text): ")
                            if user_text.strip():
                                wait_for_wake_word = False
                                self.last_user_speech_time = time.time()
                                
                                # Process the text input as if it were spoken
                                print(f"\nUser (text): {user_text}")
                                
                                # Add to conversation history
                                conversation_history.append({"role": "user", "content": user_text})
                                
                                # Check for exit command
                                if user_text.lower() in ["exit", "quit", "stop", "exit conversation", "end conversation"]:
                                    print("\nExiting conversation mode.")
                                    self.conversation_active = False
                                    break
                                
                                # Process the input through the kernel with conversation history
                                from skai.kernel.agent import kernel
                                
                                print("\nProcessing...")
                                response = kernel.process_message(user_text, history=conversation_history)
                                
                                # Add to conversation history
                                conversation_history.append({"role": "assistant", "content": response["message"]})
                                
                                # Speak the response
                                print(f"\nSKAI: {response['message']}")
                                try:
                                    self.speak(response["message"], stream=True)
                                except Exception as e:
                                    logger.error(f"Error speaking response: {e}")
                        
                        continue
                    
                    # Listen for user input
                    print("\nListening...")
                    listen_result = self.listen(timeout=5, phrase_time_limit=15)
                    
                    if listen_result["status"] == "success":
                        user_input = listen_result["text"]
                        print(f"\nUser: {user_input}")
                        
                        # Add to conversation history
                        conversation_history.append({"role": "user", "content": user_input})
                        
                        # Check for exit command
                        if user_input.lower() in ["exit", "quit", "stop", "exit conversation", "end conversation"]:
                            print("\nExiting conversation mode.")
                            self.conversation_active = False
                            break
                        
                        # Process the input through the kernel with conversation history
                        from skai.kernel.agent import kernel
                        
                        print("\nProcessing...")
                        response = kernel.process_message(user_input, history=conversation_history)
                        
                        # Add to conversation history
                        conversation_history.append({"role": "assistant", "content": response["message"]})
                        
                        # Speak the response
                        print(f"\nSKAI: {response['message']}")
                        try:
                            self.speak(response["message"], stream=True)
                        except Exception as e:
                            logger.error(f"Error speaking response: {e}")
                        
                        # Update the last speech time
                        self.last_user_speech_time = time.time()
                        
                    elif listen_result["status"] == "timeout":
                        # Just a timeout, continue listening
                        continue
                    else:
                        # Error in listening
                        if "error" in listen_result:
                            print(f"\nError: {listen_result['error']}")
                        
                        # Brief pause before trying again
                        time.sleep(1)
                except Exception as e:
                    logger.error(f"Error in conversation loop: {e}")
                    print(f"\nError: {e}")
                    time.sleep(1)  # Add a small delay to prevent high CPU usage if errors repeat
                
            print("\nConversation mode ended.")
        except Exception as e:
            logger.error(f"Fatal error in conversation loop: {e}")
            print(f"\nFatal error in conversation loop: {e}")
            self.conversation_active = False
    
    def is_in_conversation_mode(self) -> bool:
        """Check if the agent is currently in conversation mode.
        
        Returns:
            True if in conversation mode, False otherwise
        """
        return self.conversation_active


# Create a global voice agent instance
voice = VoiceAgent() 