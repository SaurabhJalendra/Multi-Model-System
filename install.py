#!/usr/bin/env python3
"""
SKAI Installation Script

This script helps set up the SKAI environment, installing dependencies,
and configuring the system for optimal performance.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)


def run_command(command, description=None):
    """Run a shell command and print its output."""
    if description:
        print(f"\n>> {description}...")
    
    try:
        result = subprocess.run(
            command, shell=True, check=True, 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False


def create_env():
    """Create a virtual environment."""
    print_header("Creating Virtual Environment")
    
    if os.path.exists(".venv"):
        print(".venv directory already exists. Using existing environment.")
        return True
    
    if platform.system() == "Windows":
        return run_command("python -m venv .venv", "Creating virtual environment")
    else:
        return run_command("python3 -m venv .venv", "Creating virtual environment")


def activate_env():
    """Activate the virtual environment."""
    print_header("Activating Virtual Environment")
    
    if platform.system() == "Windows":
        activate_cmd = ".venv\\Scripts\\activate"
        print(f"Please run: {activate_cmd}")
        return True
    else:
        activate_cmd = "source .venv/bin/activate"
        print(f"Please run: {activate_cmd}")
        return True


def install_dependencies():
    """Install Python dependencies."""
    print_header("Installing Dependencies")
    
    # Basic dependencies
    success = run_command(
        "pip install -r requirements.txt",
        "Installing required Python packages"
    )
    
    if not success:
        return False
    
    # Additional package checks for voice functionality
    print_header("Voice Dependencies")
    print("SKAI supports voice input/output with optional dependencies.")
    print("\nFor basic voice support:")
    
    # PyAudio (needed for SpeechRecognition)
    print("\n1. PyAudio (required for microphone access)")
    try:
        import pyaudio
        print("   ✓ PyAudio is already installed.")
        pyaudio_installed = True
    except ImportError:
        print("   ✗ PyAudio is not installed.")
        pyaudio_installed = False
        
        print("\n   Would you like to install PyAudio? (y/n)")
        choice = input("   > ")
        if choice.lower() in ['y', 'yes']:
            try:
                if platform.system() == "Windows":
                    run_command("pip install pyaudio", "Installing PyAudio")
                elif platform.system() == "Darwin":  # macOS
                    run_command("brew install portaudio", "Installing PortAudio")
                    run_command("pip install pyaudio", "Installing PyAudio")
                else:  # Linux
                    run_command("sudo apt-get install -y python3-pyaudio", "Installing PyAudio")
                pyaudio_installed = True
            except Exception as e:
                print(f"   ✗ Could not install PyAudio: {e}")
                print("     Please install manually: pip install pyaudio")
    
    # pyttsx3 (basic TTS)
    print("\n2. pyttsx3 (basic text-to-speech)")
    try:
        import pyttsx3
        print("   ✓ pyttsx3 is already installed.")
        pyttsx3_installed = True
    except ImportError:
        print("   ✗ pyttsx3 is not installed.")
        pyttsx3_installed = False
        
        print("\n   Would you like to install pyttsx3? (y/n)")
        choice = input("   > ")
        if choice.lower() in ['y', 'yes']:
            try:
                run_command("pip install pyttsx3", "Installing pyttsx3")
                pyttsx3_installed = True
            except Exception as e:
                print(f"   ✗ Could not install pyttsx3: {e}")
                print("     Please install manually: pip install pyttsx3")
    
    # Advanced voice dependencies
    print("\nAdvanced voice capabilities (optional):")
    
    # Whisper
    print("\n3. OpenAI Whisper (advanced speech recognition)")
    try:
        import whisper
        print("   ✓ Whisper is already installed.")
        whisper_installed = True
    except ImportError:
        print("   ✗ Whisper is not installed.")
        whisper_installed = False
        
        print("\n   Would you like to install Whisper? (y/n)")
        print("   Note: This may take a few minutes and requires additional space.")
        choice = input("   > ")
        if choice.lower() in ['y', 'yes']:
            try:
                run_command("pip install openai-whisper", "Installing Whisper")
                whisper_installed = True
            except Exception as e:
                print(f"   ✗ Could not install Whisper: {e}")
                print("     Please install manually: pip install openai-whisper")
    
    # Coqui TTS
    print("\n4. Coqui TTS (high-quality text-to-speech)")
    try:
        from TTS.api import TTS
        print("   ✓ Coqui TTS is already installed.")
        tts_installed = True
    except ImportError:
        python_version = platform.python_version()
        print(f"   ✗ Coqui TTS is not installed (your Python version: {python_version}).")
        print(f"   Note: Coqui TTS requires Python >=3.9, <3.12")
        tts_installed = False
        
        if sys.version_info >= (3, 9) and sys.version_info < (3, 12):
            print("\n   Would you like to install Coqui TTS? (y/n)")
            print("   Note: This is a large package and may take a while to install.")
            choice = input("   > ")
            if choice.lower() in ['y', 'yes']:
                try:
                    run_command("pip install TTS", "Installing Coqui TTS")
                    tts_installed = True
                except Exception as e:
                    print(f"   ✗ Could not install TTS: {e}")
                    print("     Please install manually if needed: pip install TTS")
        else:
            print("   Your Python version is not compatible with Coqui TTS.")
            print("   Use Python 3.9-3.11 if you want to use this feature.")
            
    # Summary
    print("\nVoice capability summary:")
    print(f"   Voice input:  {'Available' if pyaudio_installed else 'Not available'}")
    print(f"   Basic TTS:    {'Available' if pyttsx3_installed else 'Not available'}")
    print(f"   Advanced STT: {'Available (Whisper)' if whisper_installed else 'Not available'}")
    print(f"   Advanced TTS: {'Available (Coqui TTS)' if tts_installed else 'Not available'}")
    
    if not (pyaudio_installed and pyttsx3_installed):
        print("\nTo enable voice features, install the missing packages.")
    
    return True


def create_env_file():
    """Create a .env file if it doesn't exist."""
    print_header("Setting Up Environment Variables")
    
    env_path = Path(".env")
    if env_path.exists():
        print(".env file already exists.")
        return True
    
    print("Creating .env file with template values...")
    with open(".env", "w") as f:
        f.write("""# SKAI Configuration
# ==================

# OpenRouter API Key (Required for LLM access)
# Get one at: https://openrouter.ai/
OPENROUTER_API_KEY=

# LLM Settings
LLM_PROVIDER=openrouter
LLM_MODEL=meta-llama/llama-3.3-8b-instruct:free
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1024

# Voice Settings
TTS_SYSTEM=system  # Options: coqui_tts, piper, system
STT_SYSTEM=system  # Options: whisper, system

# Debug Settings
DEBUG_MODE=False
LOG_LEVEL=info
LOG_TO_FILE=True
DETAILED_LOGS=False
""")
    
    print("Created .env file. Please edit it with your API keys and preferences.")
    return True


def setup_workspace():
    """Create necessary directories."""
    print_header("Setting Up Workspace")
    
    # Create data directory
    os.makedirs("data/sessions", exist_ok=True)
    os.makedirs("data/chroma_db", exist_ok=True)
    
    print("Created workspace directories.")
    return True


def main():
    """Main installation function."""
    print_header("SKAI - Installation")
    print("\nThis script will set up your environment for SKAI.")
    
    # Check Python version
    python_version = platform.python_version_tuple()
    if int(python_version[0]) < 3 or (int(python_version[0]) == 3 and int(python_version[1]) < 9):
        print("Warning: SKAI works best with Python 3.9 or newer.")
        print(f"You have Python {platform.python_version()}")
        print("Some features (like Coqui TTS) may not be available with your Python version.")
        
        print("\nDo you want to continue with installation? (y/n)")
        choice = input("> ")
        if choice.lower() not in ['y', 'yes']:
            print("Installation aborted.")
            return 1
    
    # Create virtual environment
    if not create_env():
        print("Error: Failed to create virtual environment.")
        return 1
    
    # Activate virtual environment (instructions only)
    activate_env()
    
    # Prompt for activation confirmation
    print("\nPlease activate the virtual environment before continuing.")
    print("Have you activated the virtual environment? (y/n)")
    choice = input("> ")
    if choice.lower() not in ['y', 'yes']:
        print("Please activate the virtual environment first.")
        if platform.system() == "Windows":
            print("Run: .venv\\Scripts\\activate")
        else:
            print("Run: source .venv/bin/activate")
        return 0
    
    # Create workspace directories
    if not setup_workspace():
        print("Error: Failed to set up workspace.")
        return 1
    
    # Create .env file if it doesn't exist
    if not create_env_file():
        print("Error: Failed to create .env file.")
        return 1
    
    # Install dependencies
    if not install_dependencies():
        print("Error: Failed to install dependencies.")
        return 1
    
    print_header("Installation Complete")
    print("\nSKAI is now ready to use!")
    print("To get started, run: python main.py")
    
    print("\nFor voice functionality:")
    print("- Basic voice: python main.py --voice")
    print("- Check voice capabilities in the app using 'voice mode', 'listen', or 'say' commands")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 