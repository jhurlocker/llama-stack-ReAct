#!/usr/bin/env python3
"""
Streamlit Application for HR ReACT Agent

A web interface that uses the llama-stack-client API with ReActAgent
to demonstrate intelligent reasoning and tool usage for HR operations.
"""

import streamlit as st
import uuid
import io
import sys
from contextlib import redirect_stdout, redirect_stderr
import traceback

from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.react.agent import ReActAgent
from llama_stack_client.lib.agents.react.tool_parser import ReActOutput
from llama_stack_client.lib.agents.event_logger import EventLogger


# Page configuration
st.set_page_config(
    page_title="HR ReACT Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
    }
    .reasoning-box {
        background-color: #FFF3E0;
        border-left: 4px solid #FF9800;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
    .tool-box {
        background-color: #E8F5E8;
        border-left: 4px solid #4CAF50;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
    .result-box {
        background-color: #E3F2FD;
        border-left: 4px solid #2196F3;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
    .stButton > button {
        background-color: #2E86AB;
        color: white;
        border-radius: 0.5rem;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'client_connected' not in st.session_state:
        st.session_state.client_connected = False


def connect_to_llama_stack(host: str, port: int):
    """Connect to Llama Stack and initialize ReACT agent"""
    try:
        # Create client
        client = LlamaStackClient(base_url=f"http://{host}:{port}")
        
        # Get available models
        available_models = [
            model.identifier for model in client.models.list() if model.model_type == "llm"
        ]
        
        if not available_models:
            st.error("❌ No available models found on Llama Stack server")
            return False
        
        selected_model = available_models[0]
        st.success(f"✅ Connected! Using model: {selected_model}")
        
        # Initialize ReActAgent with HR MCP server tools
        agent = ReActAgent(
            client=client,
            model=selected_model,
            tools=[
                "mcp::hr-api-tools",  # HR MCP server
            ],
            response_format={
                "type": "json_schema",
                "json_schema": ReActOutput.model_json_schema(),
            },
            sampling_params={
                "strategy": {"type": "top_p", "temperature": 1.0, "top_p": 0.9},
            }
        )
        
        # Create session
        session_id = agent.create_session("hr-react-session")

        # Store in session state
        st.session_state.agent = agent
        st.session_state.session_id = session_id
        st.session_state.client_connected = True
        
        return True
        
    except Exception as e:
        st.error(f"❌ Failed to connect to Llama Stack: {str(e)}")
        st.session_state.client_connected = False
        return False


def process_query_realtime(query: str):
    print(query)
    """Process a query using the ReACT agent with real-time display"""
    if not st.session_state.agent or not st.session_state.session_id:
        st.error("❌ Agent not initialized. Please connect to Llama Stack first.")
        return
    
    try:
        # Create containers for display
        status_container = st.empty()
        response_container = st.container()
        
        status_container.info("🤔 Agent is processing your query...")
        
        # Get the response stream
        response = st.session_state.agent.create_turn(
            messages=[{"role": "user", "content": query}],
            session_id=st.session_state.session_id,
            stream=True,
        )
        
        # Extract and collect all text content from the stream
        all_content = ""
        
        for chunk in response:
            # Extract text from TextDelta if available
            if hasattr(chunk, 'event') and hasattr(chunk.event, 'payload'):
                payload = chunk.event.payload
                if hasattr(payload, 'delta') and hasattr(payload.delta, 'text'):
                    all_content += payload.delta.text
        
        # Display the complete response once
        status_container.success("✅ Response complete!")
        
        with response_container:
            st.markdown("### Agent Response:")
            st.code(all_content, language="json")
        
        return all_content
        
    except Exception as e:
        st.error(f"❌ Error processing query: {str(e)}")
        st.error(f"Full error: {traceback.format_exc()}")
        return None


def format_agent_output(output: str):
    """Format the agent output with better styling, separating answer from reasoning"""
    if not output:
        return
    
    import re
    
    final_answer = None
    
    # Look for final answer patterns in the output
    lines = output.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for final answer patterns
        if any(pattern in line.lower() for pattern in ["final answer:", "answer:", "result:", "the vacation balance", "balance for", "remaining"]):
            # Extract the answer content after common prefixes
            answer_content = line
            for prefix in ["Final Answer:", "Answer:", "Result:", "final answer:", "answer:", "result:"]:
                if prefix in line:
                    answer_content = line.split(prefix, 1)[-1].strip()
                    break
            if answer_content and not any(word in answer_content.lower() for word in ["thought:", "action:", "observation:"]):
                final_answer = answer_content
    
    # Display final answer prominently if found
    if final_answer:
        st.markdown("""
        <div style="background-color: #E8F5E8; border: 2px solid #4CAF50; padding: 1.5rem; margin: 1rem 0; border-radius: 0.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h3 style="color: #2E7D32; margin-top: 0;">🎯 Final Answer</h3>
            <p style="font-size: 1.1rem; margin-bottom: 0; color: #1B5E20;"><strong>{}</strong></p>
        </div>
        """.format(final_answer), unsafe_allow_html=True)
    
    # Show raw response in expandable section
    with st.expander("🔍 View Reasoning Steps", expanded=False):
        st.text(output)


def main():
    """Main Streamlit application"""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🤖 HR ReACT Agent</h1>', unsafe_allow_html=True)
    st.markdown("**Intelligent HR Operations with Reasoning & Acting**")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Llama Stack connection settings
        st.subheader("Llama Stack Server")
        host = st.text_input("Host", value="llama-stack", help="Llama Stack server hostname")
        port = st.number_input("Port", value=80, min_value=1, max_value=65535, help="Llama Stack server port")
        
        # Connect button
        if st.button("🔌 Connect to Llama Stack"):
            connect_to_llama_stack(host, port)
        
        # Connection status
        if st.session_state.client_connected:
            st.success("✅ Connected to Llama Stack")
        else:
            st.warning("⚠️ Not connected to Llama Stack")
        
        st.divider()
        
        # Example queries
        st.subheader("📝 Example Queries")
        
        example_queries = [
            "What is the vacation balance for employee EMP001?",
            "If user EMP001 has enough remaining vacation days, book two days off for 2nd and 3rd of July 2025"
        ]
        
        for i, example in enumerate(example_queries, 1):
            if st.button(f"Example {i}", help=example, key=f"example_{i}"):
                if st.session_state.client_connected:
                    st.session_state.current_query = example
                else:
                    st.error("Please connect to Llama Stack first!")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Chat with the Agent")
        
        # Query input
        query = st.text_area(
            "Enter your HR query:",
            value=st.session_state.get('current_query', ''),
            height=100,
            placeholder="Ask me about vacation management for employees..."
        )
        
        # Process button
        if st.button("🚀 Send Query", disabled=not st.session_state.client_connected):
            if query.strip():
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": query})
                
                # Process the query with real-time display
                agent_output = process_query_realtime(query)
                
                if agent_output:
                    # Add agent response to chat history
                    st.session_state.messages.append({"role": "agent", "content": agent_output})
                
                # Clear the current query
                if 'current_query' in st.session_state:
                    del st.session_state.current_query
            else:
                st.warning("Please enter a query!")
    
    with col2:
        st.subheader("ℹ️ About ReACT")
        st.info("""
        **ReACT (Reasoning + Acting)** combines:
        
        🤔 **Reasoning**: Step-by-step thinking
        
        🛠️ **Acting**: Dynamic tool usage
        
        ✅ **Learning**: Adapting based on results
        """)
        
        st.subheader("🔧 Available Tools")
        st.write("• HR Vacation Balance Check")
        st.write("• Vacation Request Creation")
        st.write("• Employee Data Access")
    
    # Chat history
    if st.session_state.messages:
        st.divider()
   
        
        # Clear history button
        if st.button("🗑️ Clear History"):
            st.session_state.messages = []
            st.rerun()


if __name__ == "__main__":
    main()