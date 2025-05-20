"""Wake Word Detection for SKAI.

This module handles wake word detection using Porcupine.
It allows for hands-free activation of SKAI using the phrase "Hey SKAI".
"""

import os
import time
import threading
from typing import Any, Callable, Dict, Optional

# Try to import wake word dependencies, gracefully handle if not installed
try:
    import pvporcupine
    PORCUPINE_AVAILABLE = True
except ImportError:
    pvporcupine = None
    PORCUPINE_AVAILABLE = False

try:
    from pvrecorder import PvRecorder
    PVRECORDER_AVAILABLE = True
except ImportError:
    PvRecorder = None
    PVRECORDER_AVAILABLE = False

from skai.config.settings import config
from skai.utils.logging import get_skai_logger

logger = get_skai_logger("tools.wake_word")


class WakeWordDetector:
    """Wake Word Detector that listens for "Hey SKAI".
    
    Uses Porcupine wake word engine to detect the wake phrase.
    """
    
    def __init__(
        self,
        callback: Optional[Callable[[str], None]] = None,
        sensitivity: float = 0.7,
        access_key: Optional[str] = None,
        wake_word: str = "Hey Sky",
        keyword_path: Optional[str] = None,
        enabled: bool = True
    ):
        """Initialize Wake Word Detector.
        
        Args:
            callback: Function to call when wake word is detected
            sensitivity: Detection sensitivity (0-1)
            access_key: Picovoice access key (from env or config if None)
            wake_word: Wake word/phrase to detect
            keyword_path: Path to custom keyword file (.ppn)
            enabled: Whether wake word detection is enabled
        """
        self.callback = callback
        self.sensitivity = sensitivity
        self.wake_word = wake_word
        self.keyword_path = keyword_path
        self.enabled = enabled and PORCUPINE_AVAILABLE and PVRECORDER_AVAILABLE
        self.access_key = access_key or os.getenv("PICOVOICE_ACCESS_KEY") or config.get("picovoice_access_key")
        
        self.porcupine = None
        self.recorder = None
        self.detection_thread = None
        self._running = False
        
        # Log availability
        if not PORCUPINE_AVAILABLE:
            logger.warning("Porcupine is not available. Wake word detection disabled.")
            logger.info("Install with: pip install pvporcupine")
        if not PVRECORDER_AVAILABLE:
            logger.warning("PvRecorder is not available. Wake word detection disabled.")
            logger.info("Install with: pip install pvrecorder")
        if not self.access_key:
            logger.warning("No Picovoice access key found. Wake word detection disabled.")
            logger.info("Get a free key at https://console.picovoice.ai/")
            self.enabled = False
        
        if self.enabled:
            logger.info(f"Wake word detection initialized with phrase: '{wake_word}'")
    
    def start(self):
        """Start wake word detection in a background thread."""
        if not self.enabled:
            logger.warning("Wake word detection is disabled, can't start")
            return False
        
        if self._running:
            logger.warning("Wake word detection is already running")
            return True
        
        try:
            # Check microphone access first
            try:
                temp_recorder = PvRecorder(device_index=-1, frame_length=512)
                temp_recorder.start()
                logger.info("Successfully accessed microphone")
                temp_recorder.stop()
                temp_recorder.delete()
            except Exception as e:
                logger.error(f"Failed to access microphone: {e}")
                print(f"\nError: Failed to access microphone: {e}")
                print("Please check your microphone settings and permissions.")
                return False
            
            # Initialize Porcupine with custom keyword if available
            if self.keyword_path and os.path.exists(self.keyword_path):
                logger.info(f"Using custom wake word model: {self.keyword_path}")
                self.porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keyword_paths=[self.keyword_path],
                    sensitivities=[self.sensitivity]
                )
                # Only one wake word when using custom model
                self.keyword_names = [self.wake_word]
                print(f"\nWake word detection using custom model: {self.keyword_path}")
                print(f"Sensitivity set to: {self.sensitivity}")
            else:
                # Fall back to built-in keywords
                logger.info("Using built-in wake words (no custom model found)")
                keywords = ["picovoice", "hey siri", "ok google", "computer"]
                self.porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keywords=keywords,
                    sensitivities=[self.sensitivity] * len(keywords)
                )
                self.keyword_names = keywords
            
            # Initialize recorder
            self.recorder = PvRecorder(
                device_index=-1,  # Default microphone
                frame_length=self.porcupine.frame_length
            )
            
            # Start listening in a separate thread
            self._running = True
            self.detection_thread = threading.Thread(
                target=self._detection_loop,
                daemon=True
            )
            self.detection_thread.start()
            logger.info(f"Wake word detection started with '{self.keyword_names}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start wake word detection: {e}")
            self.stop()
            return False
    
    def stop(self):
        """Stop wake word detection."""
        self._running = False
        
        if self.recorder and self.recorder.is_recording:
            self.recorder.stop()
        
        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=2.0)
        
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None
            
        if self.recorder:
            self.recorder.delete()
            self.recorder = None
        
        logger.info("Wake word detection stopped")
    
    def _detection_loop(self):
        """Main detection loop that runs in a separate thread."""
        try:
            self.recorder.start()
            logger.info("Listening for wake word...")
            print("\nWake word detector activated and listening...")
            print(f"Listening for: {', '.join(self.keyword_names)}")
            
            # For debugging - log audio level periodically
            debug_counter = 0
            
            while self._running:
                pcm = self.recorder.read()
                
                # Log audio levels every ~5 seconds for debugging
                debug_counter += 1
                if debug_counter % 100 == 0:  # Approximately every 5 seconds depending on frame rate
                    # Calculate audio level (simple RMS)
                    if len(pcm) > 0:
                        audio_level = sum(abs(x) for x in pcm) / len(pcm)
                        logger.info(f"Audio level: {audio_level:.2f}")
                
                keyword_index = self.porcupine.process(pcm)
                
                if keyword_index >= 0:
                    # Use the name from our stored names list
                    detected_keyword = self.keyword_names[keyword_index]
                    
                    logger.info(f"Wake word detected: {detected_keyword}")
                    print(f"\n🎤 Wake word detected: {detected_keyword}")
                    
                    if self.callback:
                        self.callback(detected_keyword)
                    
                    # Optional pause to prevent multiple rapid detections
                    time.sleep(1.0)
                    
        except Exception as e:
            logger.error(f"Error in wake word detection: {e}")
        finally:
            if self.recorder and self.recorder.is_recording:
                self.recorder.stop()
            logger.info("Wake word detection thread stopped")


# Create a global detector instance
wake_word_detector = None

def initialize_wake_word_detector(callback: Optional[Callable] = None, 
                                 keyword_path: Optional[str] = None) -> WakeWordDetector:
    """Initialize the global wake word detector.
    
    Args:
        callback: Function to call when wake word is detected
        keyword_path: Path to custom keyword file (.ppn)
        
    Returns:
        Initialized WakeWordDetector instance
    """
    global wake_word_detector
    
    if wake_word_detector is None:
        wake_word_detector = WakeWordDetector(
            callback=callback,
            keyword_path=keyword_path
        )
    
    return wake_word_detector

def get_wake_word_detector() -> Optional[WakeWordDetector]:
    """Get the global wake word detector.
    
    Returns:
        Global WakeWordDetector instance or None if not initialized
    """
    return wake_word_detector 