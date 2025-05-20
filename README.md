# SKAI - Sentient Kernel Adaptive Intelligence

## Overview

**SKAI (Sentient Kernel Adaptive Intelligence)** is a next-generation, self-evolving AI assistant designed to operate as a modular, intelligent agent system. It is more than a chatbot — SKAI acts as an orchestrated collective of AI agents that collaborates to understand tasks, break them into subtasks, execute them efficiently, and continuously improve its own abilities over time.

This project aims to build a sentient kernel capable of coordinating multiple intelligent modules, understanding user sentiment and urgency, performing research, coding, planning, document management, voice communication, and even self-refinement. SKAI is designed to be agentic, self-improving, and context-aware.

## Getting Started

### Prerequisites

- Python 3.10+ 
- Google ADK (Agent Development Kit)
- OpenRouter API key (for LLM access)
- For voice functionality: microphone and speakers

### Installation

1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/SKAI.git
cd SKAI
```

2. Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your API keys:
```
OPENROUTER_API_KEY=your_openrouter_key_here
```

## Usage

Run the CLI interface:
```bash
python main.py
```

For debug mode:
```bash
python main.py --debug
```

Start directly in voice mode:
```bash
python main.py --voice
```

Start with wake word detection enabled:
```bash
python main.py --wake-word
```

Start in ChatGPT-like conversation mode:
```bash
python main.py --conversation
```

## Voice Commands

SKAI supports these voice-related commands:

- `voice mode` - Enter voice interaction mode (speak your commands)
- `conversation` - Start ChatGPT-like continuous voice conversation
- `exit voice mode` - Return to text input mode
- `listen` - Listen for a single voice input
- `say <text>` - Convert text to speech

## ChatGPT-Like Conversations

SKAI now supports natural, flowing conversations similar to ChatGPT's voice mode:

- Start with `python main.py --conversation` or type `conversation` in the CLI
- Speak naturally and SKAI will respond conversationally
- Maintains context across multiple turns
- Say "exit conversation" to end the conversation
- Integration with wake word detection - say "Hey Sky" to resume after timeout

## Wake Word Commands

SKAI now supports wake word detection using Picovoice Porcupine:

- `wake word on` - Enable wake word detection
- `wake word off` - Disable wake word detection
- Say "Hey Sky" when detection is enabled to activate listening mode

Note: You need to install the wake word dependencies and obtain a Picovoice AccessKey:
```bash
pip install pvporcupine pvrecorder
```
Then add your AccessKey to the .env file:
```
PICOVOICE_ACCESS_KEY=your_picovoice_access_key_here
```
Get a free AccessKey by registering at [Picovoice Console](https://console.picovoice.ai/).

### Using a Custom Wake Word Model

To use a custom wake word model like "Hey Sky":

1. Create a custom wake word model at [Picovoice Console](https://console.picovoice.ai/)
2. Download the .ppn file for your platform
3. Place the model in a directory (e.g., `hey-sky/`)
4. Run SKAI with:
```bash
python main.py --wake-word --wake-word-model path/to/your/model.ppn
```

If you place the model in the `hey-sky` directory, SKAI will automatically find it.

## Project Structure

- `skai/`: Main package
  - `agents/`: Specialized agents for different tasks
    - `communicator.py`: Interprets user intent and sentiment
    - `research.py`: Gathers and synthesizes information
    - `voice.py`: Handles voice input/output
  - `config/`: Configuration and settings
  - `kernel/`: Core orchestration logic
  - `memory/`: State and memory management
  - `tools/`: Tool functions for agents
    - `weather_time.py`: Weather and time utilities
    - `workflow.py`: Multi-agent workflow tools
    - `wake_word.py`: Wake word detection (placeholder)
  - `utils/`: Utility functions and helpers
- `main.py`: Entry point for the application
- `Roadmap.md`: Development roadmap and future plans

## Architecture

SKAI is built on a multi-agent architecture using Google's Agent Development Kit (ADK). The system consists of:

- **Kernel Agent**: Central orchestrator that manages all other agents
- **Specialized Agents**: Task-specific agents (e.g., weather, time, research, voice)
- **Memory System**: Conversation history and contextual understanding
- **Tool Integration**: Functions that agents can call to perform tasks

## Current Capabilities

- Answer questions about weather and time in various cities
- Maintain conversation context across user interactions
- Persistent session management
- Basic voice input/output with speech-to-text and text-to-speech
- Text and voice-based conversation modes

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Key Features

### ✨ Sentient Interaction

* Understands emotional tone, urgency, and context through NLP and voice inputs
* Communicator Agent tailors interactions based on user sentiment

### 🧠 Multi-Agent Architecture

* Modular design with specialized agents for:

  * Communication
  * Planning
  * Coding
  * Research
  * Critiquing
  * Voice interaction
  * Self-refinement

### ⚖️ Task Decomposition

* Kernel Agent breaks down complex tasks into subtasks
* Delegates subtasks to appropriate agents

### ⚡ Orchestrated Execution

* Uses ensemble voting and critic evaluation for choosing best results
* Capable of executing parallel agent pipelines

### 🔄 Self-Improvement

* Monitors outcomes and learns from user feedback
* Updates its own codebase via a Self-Improving Agent
* Reinforcement learning for behavioural adjustments

### 🔗 Integrated Tools

* Web scraping, browser automation, API calling
* Semantic memory via vector DB (ChromaDB)
* LangChain-powered RAG for document and knowledge retrieval
* Coqui TTS and speech\_recognition for voice interaction

### 🎤 Voice Interface

* Text-to-speech using Coqui TTS, Piper, or system TTS
* Speech-to-text using Whisper or system recognition
* "Hey Sky" wake word detection using Picovoice Porcupine
* Voice activity detection for better interactions
* Voice tone and sentiment analysis (planned)
* Seamless switching between text and voice modes

### 🌐 Multi-Interface Support

* CLI-based interface
* Streamlit web UI (planned)
* Voice assistant interface

---

## Workflow Example

> User Input:
> "SKAI, I need a market research slide deck comparing OpenAI, Anthropic, and Mistral AI."

**Execution:**

1. **Communicator Agent** detects urgency and formal tone
2. **Kernel Agent** breaks task:

   * Research competitors
   * Summarize key metrics
   * Build PowerPoint slides
3. **Research Agent** fetches data
4. **Analyzer Agent** structures findings
5. **Slide Agent** creates deck (using docx/pptx libs or Google Slides API)
6. **Critic Agent** reviews for completeness
7. **Output**: Downloadable presentation deck

---

## Roadmap

* [x] Kernel + Orchestration Layer
* [x] Agent Communication & Task Routing
* [x] Semantic Search & Vector Database
* [x] Voice I/O with Coqui TTS + speech\_recognition
* [x] Wake word detection with Porcupine
* [ ] ChatGPT-like voice conversations
* [ ] Local agent sandboxing via subprocess containers
* [ ] Full self-improving feedback loop via RLHF
* [ ] Integration with external tools (JIRA, GitHub, Google Docs)

---

## Contributing

Pull requests are welcome. Please submit an issue first to discuss what you would like to change.

---

## Credits

Built by Saurabh Jalendra and the SKY AI team. Powered by OpenRouter LLMs, LangChain, ChromaDB, and Python AI tools.

---

## Contact

For inquiries, reach out at: [info@sky-ai.in](mailto:info@sky-ai.in)
