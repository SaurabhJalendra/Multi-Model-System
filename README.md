# SKAI - Sentient Kernel Adaptive Intelligence

## Overview

**SKAI (Sentient Kernel Adaptive Intelligence)** is a next-generation, self-evolving AI assistant designed to operate as a modular, intelligent agent system. It is more than a chatbot — SKAI acts as an orchestrated collective of AI agents that collaborates to understand tasks, break them into subtasks, execute them efficiently, and continuously improve its own abilities over time.

This project aims to build a sentient kernel capable of coordinating multiple intelligent modules, understanding user sentiment and urgency, performing research, coding, planning, document management, voice communication, and even self-refinement. SKAI is designed to be agentic, self-improving, and context-aware.

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

### 🌐 Multi-Interface Support

* CLI-based interface
* Streamlit web UI
* Voice assistant interface

---

## Architecture

### Kernel Agent (Orchestrator)

* Brain of SKAI
* Receives tasks, assigns subtasks, aggregates results

### Communicator Agent

* Interprets user messages, urgency, sentiment
* Adjusts flow and language of responses

### Task Agents

* **Planner Agent**: Breaks tasks into executable steps
* **Research Agent**: Uses web & document search for background info
* **Coding Agent**: Writes, debugs, and suggests code
* **Critic Agent**: Ranks outputs from other agents
* **Voice Agent**: Converts speech-to-text and text-to-speech
* **Self-Improving Agent**: Analyzes and updates SKAI's code & logic

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

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/SKAI.git
cd SKAI
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables

Create a `.env` file:

```
OPENROUTER_API_KEY=your_openrouter_key
CHROMA_PATH=data/chroma_db
...
```

---

## Usage

### Start SKAI CLI

```bash
python main.py
```

### Web UI (Streamlit)

```bash
streamlit run ui/app.py
```

### Voice Interface

Start the voice assistant module:

```bash
python voice_interface.py
```

---

## Roadmap

* [x] Kernel + Orchestration Layer
* [x] Agent Communication & Task Routing
* [x] Semantic Search & Vector Database
* [x] Voice I/O with Coqui TTS + speech\_recognition
* [ ] Local agent sandboxing via subprocess containers
* [ ] Full self-improving feedback loop via RLHF
* [ ] Integration with external tools (JIRA, GitHub, Google Docs)

---

## Contributing

Pull requests are welcome. Please submit an issue first to discuss what you would like to change.

---

## License

MIT License

---

## Credits

Built by Saurabh Jalendra and the SKY AI team. Powered by OpenRouter LLMs, LangChain, ChromaDB, and Python AI tools.

---

## Contact

For inquiries, reach out at: [info@sky-ai.in](mailto:info@sky-ai.in)
