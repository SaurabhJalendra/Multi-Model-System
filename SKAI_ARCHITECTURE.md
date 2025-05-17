# SKAI Architecture Overview – Sentient Kernel Adaptive Intelligence

## 🎯 Purpose

This document outlines the **technical architecture** of the SKAI system, detailing its modular agent-based design, data flow, interaction layers, and model integration. The architecture is built for adaptability, modularity, and real-time orchestration, making it suitable for both assistant-level tasks and future autonomous system expansions.

---

## 🧠 High-Level System Architecture

### Core Layers:

1. **Interface Layer** (Input/Output)

   * CLI / Web UI (Streamlit)
   * Voice Interface (Mic + TTS)
   * Optional: API / Mobile App

2. **Orchestration Layer**

   * Kernel Agent: Primary controller
   * Task Router: Subtask delegation and scheduling
   * Context Manager: Tracks session state, memory, feedback

3. **Agent Layer** (Specialised Agents)

   * Communicator Agent
   * Research Agent
   * Coding Agent
   * Planner Agent
   * Critic Agent
   * Voice Agent
   * Self-Improving Agent

4. **Skill/Tool Layer**

   * Tools: Search, file parsing, TTS/STT, web automation
   * LLMs (via OpenRouter)
   * Vector Store (ChromaDB)
   * LangChain RAG modules

5. **Persistence Layer**

   * Long-Term Memory (Vector DB)
   * Local Task Logs and Feedback
   * Configs (.env / YAML)

---

## 🧩 Modular Agent Breakdown

### 🧠 Kernel Agent (Orchestrator)

* Manages agent task flow
* Decomposes complex inputs into subtasks
* Logs results, monitors errors

### 🗣 Communicator Agent

* Parses user input
* Detects sentiment, tone, and intent
* Applies task typing for Kernel to route

### 📝 Planner Agent

* Transforms broad goals into sequences of actionable tasks
* Delegates to other agents via Kernel

### 🔍 Research Agent

* Uses browser/API to gather information
* Supports prompt chaining for deeper queries

### 👨‍💻 Coding Agent

* Writes, edits, or debugs code
* Can call DeepSeek/Code LLMs from OpenRouter

### 🧪 Critic Agent

* Evaluates multiple outputs (e.g., from multiple LLMs)
* Votes or ranks based on completeness and quality

### 🔁 Self-Improving Agent

* Watches logs and agent outcomes
* Proposes improvements to code and logic
* Stores improvement history (version-aware)

### 🔊 Voice Agent

* STT via `speech_recognition`
* TTS via `Coqui TTS`
* Handles audio loopback (for live chat mode)

---

## 🔗 LLM Model Access

SKAI supports multiple LLMs through OpenRouter. They are invoked via tool wrappers and routed dynamically based on:

* Task type (e.g., code, summarization, planning)
* Token budget & context size
* Performance preferences

**Models Used**:

* `deepseek/deepseek-chat-v3`
* `meta-llama/llama-3.2-8b-instruct`
* `nous-hermes-2-mixtral`
* `microsoft/phi-2`

---

## 🔄 Data Flow (Typical Interaction)

```text
User → Voice/CLI Input
     ↓
Communicator Agent (classifies intent)
     ↓
Kernel Agent (creates plan)
     ↓
Task Agent(s) (execute subtasks)
     ↓
Critic Agent (optional evaluation)
     ↓
Response Synthesized (TTS or text)
     ↓
User Output + Logging + Memory Update
```

---

## 🛠 Core Dependencies

* `LangChain`, `ChromaDB`, `OpenRouter`
* `Coqui TTS`, `speech_recognition`
* `Python-dotenv`, `requests`, `pydantic`
* ADK (optional agent orchestration upgrade)

---

## 📦 Deployment Considerations

* Lightweight setup for CLI or desktop assistant
* Can scale to server-hosted orchestration with background agent runner
* Local LLM support (via Ollama/llama.cpp) optionally supported

---

## 🧠 Future Architectural Enhancements

* Multimodal pipeline: image and audio processing
* Distributed agent scheduling
* Plugin interface for adding/removing agents at runtime
* Real-time streaming architecture for low-latency speech mode

---

## 🧭 Summary

SKAI’s architecture is:

* Modular and agent-based
* LLM-flexible and cloud/local friendly
* Designed for continuous self-improvement
* Capable of scaling from personal assistant to semi-autonomous system

This foundation enables advanced features like memory, tool-use, multi-agent orchestration, and future self-upgrading AI capabilities.
