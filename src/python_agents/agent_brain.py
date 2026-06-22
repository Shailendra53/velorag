import chromadb
import zmq

from typing import TypedDict
from chromadb.utils import embedding_functions
from langgraph.graph import StateGraph, END

# Get DB PATH from env
def get_db_path() -> str:
    """Returns the path for ChromaDB persistence."""
    import os
    return os.getenv("CHROMADB_PERSIST_DIR", "./chroma_storage")

# ==========================================
# 1. SETUP LOCAL VECTOR DATABASE (CHROMA)
# ==========================================
DB_PATH = get_db_path()
chroma_client = chromadb.PersistentClient(path=DB_PATH)
default_ef = embedding_functions.DefaultEmbeddingFunction()
collection = chroma_client.get_or_create_collection(name="market_history", embedding_function=default_ef)

def seed_historical_data():
    if collection.count() == 0:
        collection.add(
            documents=[
                "In 2018, the FED unexpectedly raised rates, causing tech stocks to drop 15% over the quarter.",
                "Q2 earnings surges above 20% historically spark an immediate 3-5% rally in semiconductor stocks.",
                "Regulatory crackdowns on crypto exchanges typically drive institutional money back into gold and bonds."
            ],
            metadatas=[{"impact": "bearish"}, {"impact": "bullish"}, {"impact": "bearish"}],
            ids=["hist_001", "hist_002", "hist_003"]
        )

# ==========================================
# 2. DEFINE LANGGRAPH STATE
# ==========================================
# This class acts as the shared memory ledger between our agents
class AgentState(TypedDict):
    raw_headline: str
    historical_context: str
    sentiment_score: float
    risk_action: str  # "APPROVED" or "BLOCKED"

# ==========================================
# 3. DEFINE THE AGENTS (NODES)
# ==========================================

def analyst_node(state: AgentState) -> dict:
    """Queries Vector DB and assigns a sentiment score."""
    headline = state["raw_headline"]
    print(f"\n[Analyst Agent] Processing: '{headline}'")
    
    # Query ChromaDB
    results = collection.query(query_texts=[headline], n_results=1)
    context = results['documents'][0][0] if results['documents'] else "No context found"
    
    # Simple semantic rule-engine for sentiment score
    score = 0.85 if "surge" in context or "bullish" in context else -0.75
    
    print(f"[Analyst Agent] Found History: \"{context}\" -> Sentiment: {score}")
    return {"historical_context": context, "sentiment_score": score}

def risk_gatekeeper_node(state: AgentState) -> dict:
    """Evaluates if the sentiment signal violates safety risk boundaries."""
    score = state["sentiment_score"]
    print(f"[Risk Agent] Evaluating system safety for sentiment score: {score}")
    
    # Extreme sentiment scores represent high volatility market anomalies
    if abs(score) > 0.80:
        action = "BLOCKED (Volatility Alert: Risk metrics exceeded)"
    else:
        action = "APPROVED"
        
    print(f"[Risk Agent] Action Decision: {action}")
    return {"risk_action": action}

# ==========================================
# 4. BUILD THE GRAPH COMPILATION
# ==========================================

# Initialize the stateful graph workflow
workflow = StateGraph(AgentState)

# Add our processing units (Nodes)
workflow.add_node("analyst", analyst_node)
workflow.add_node("risk_gatekeeper", risk_gatekeeper_node)

# Connect nodes together linearly (Edges)
workflow.set_entry_point("analyst")
workflow.add_edge("analyst", "risk_gatekeeper")
workflow.add_edge("risk_gatekeeper", END)

# Compile into an executable application
velo_agent_app = workflow.compile()

if __name__ == "__main__":
    seed_historical_data()

    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://localhost:5555")
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "") # Subscribe to all messages

    print("=== VeloRAG LangGraph Listener Active ===")
    print("Awaiting low-latency feeds from C++ core...")

    try:
        while True:
            # 2. Block until a network message comes from C++ (Consumes 0% CPU while idle)
            message_bytes = subscriber.recv()
            incoming_headline = message_bytes.decode('utf-8')
            
            print(f"\n[ZeroMQ Bridge] Caught Stream: '{incoming_headline}'")
            
            # 3. Fire up the stateful LangGraph engine dynamically for this headline
            initial_state = {
                "raw_headline": incoming_headline,
                "historical_context": "",
                "sentiment_score": 0.0,
                "risk_action": ""
            }
            
            final_output = velo_agent_app.invoke(initial_state)
            
            print("--- Execution Complete ---")
            print(f"Result Action: {final_output['risk_action']}\n")
            
    except KeyboardInterrupt:
        print("\nShutting down network wire listener.")
