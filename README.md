# VeloRAG 🦅

**VeloRAG** (Velocity Retrieval-Augmented Generation) is a high-performance, cross-language financial stream processing framework designed to ingest raw market signals at low-latency, process them with semantic context, and apply safe risk-mitigation guardrails via AI agents.

## 🏗️ System Architecture

The pipeline decouples high-speed data parsing from heavy semantic computation using an asynchronous memory network:

1. **Ingestion Layer (C++20):** Monitors `src/data_input/` for incoming unstructured JSON payloads, applies zero-allocation text cleanup, and publishes cleaned headlines over the network layer.
2. **Transport Layer (ZeroMQ):** Bypasses the disk boundary entirely using an in-memory Publisher/Subscriber network socket (`tcp://*:5555`) to pipe data between runtimes.
3. **Cognitive Layer (Python + LangGraph):** Subscribes to the wire feed and routes each headline through a stateful, multi-agent graph:
   - **Analyst Agent:** Queries the Memory Layer for historical precedent and asks a local LLM to score sentiment (-1.0 to +1.0) with a rationale.
   - **Router:** High-conviction signals (`|score| > 0.60`) are sent to the Execution Agent; everything else skips straight to risk review.
   - **Execution Agent:** Simulates order preparation (direction + position size) for high-conviction signals.
   - **Risk Gatekeeper:** Blocks any signal whose sentiment score exceeds the `|0.80|` volatility threshold; otherwise approves it.
4. **Memory Layer (ChromaDB):** An on-device vector database providing semantic similarity lookup against historical financial market anomalies, embedding queries via Chroma's default embedding function.

Inference is served locally through **Ollama** (`llama3:latest`) — no external API calls are made for the analyst's sentiment scoring.

## 🚀 Getting Started

### Prerequisites
- macOS (Apple Silicon optimized — `CMakeLists.txt` hardcodes `/opt/homebrew` include/lib paths)
- CMake 3.16+
- ZeroMQ (`brew install zeromq`)
- Python 3.9+
- [Ollama](https://ollama.com) running locally, with the `llama3` model pulled:
  ```bash
  ollama pull llama3
  ```

### 1. Compile the C++ Core Engine
```bash
cd src/cpp_engine
mkdir -p build && cd build
cmake ..
make
```

### 2. Set up the Python Cognitive Layer
```bash
cd src
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

The `.env` file controls where the ingestion pipeline reads and writes data:

| Variable | Purpose | Default |
|---|---|---|
| `DATA_INPUT_DIR` | Directory the streamer writes JSON headlines into, and the C++ engine watches | `./data_input` |
| `MOCK_HEADLINES_FILE` | Source file of sample headlines used to generate mock alerts | `mock_headlines.txt` |
| `CHROMADB_PERSIST_DIR` | On-disk path for the persistent Chroma vector store | `../chroma_db` |

### 3. Run the full pipeline
Each layer runs as its own long-lived process. Open three terminals from the project root:

**Terminal 1 — C++ ingestion engine** (run from `src/cpp_engine/build` so its relative `../data_input` path resolves to `src/data_input`):
```bash
cd src/cpp_engine/build
./velorag
```

**Terminal 2 — Python cognitive layer** (subscribes to the ZeroMQ feed and runs the agent graph):
```bash
cd src
source .venv/bin/activate
python3 python_agents/agent_brain.py
```

**Terminal 3 — Mock news streamer** (drops a random headline into `data_input/` every 2 seconds):
```bash
cd src
source .venv/bin/activate
python3 streamer.py
```

You should see the C++ engine ingest and clean each headline, publish it over ZeroMQ, and the Python agent graph print the Analyst's sentiment score, the routing decision, and the Risk Gatekeeper's final APPROVED/BLOCKED verdict.
