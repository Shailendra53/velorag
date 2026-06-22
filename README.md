# VeloRAG 🦅

**VeloRAG** (Velocity Retrieval-Augmented Generation) is a high-performance, cross-language financial stream processing framework designed to ingest raw market signals at low-latency, process them with semantic context, and apply safe risk-mitigation guardrails via AI agents.

## 🏗️ System Architecture

The pipeline decouples high-speed data parsing from heavy semantic computation using an asynchronous memory network:

1. **Ingestion Layer (C++20):** Monitors incoming unstructured payloads, applies zero-allocation text cleanup, and pushes strings over the network layer.
2. **Transport Layer (ZeroMQ):** Bypasses the disk boundary entirely using an in-memory Publisher/Subscriber network socket to pipe data between runtimes.
3. **Cognitive Layer (Python 3.14 + LangGraph):** Handles inbound data via an infinite network event loop, feeding data directly into a stateful, cyclic multi-agent graph.
4. **Memory Layer (ChromaDB):** An on-device vector database providing semantic similarity lookup against historical financial market anomalies.

## 🚀 Getting Started

### Prerequisites
- macOS (Apple Silicon optimized)
- CMake 3.16+
- ZeroMQ (`brew install zeromq`)
- Python 3.14+

### Compiling the C++ Core Engine
```bash
cd src/cpp_engine
mkdir build && cd build
cmake ..
make
./velorag
