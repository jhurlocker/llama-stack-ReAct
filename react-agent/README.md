# ReACT Agent for HR Operations

This directory contains a simplified ReACT (Reasoning + Acting) agent implementation that demonstrates intelligent reasoning and tool usage for HR operations using Llama Stack.

## Overview

The ReACT agent combines reasoning and acting to solve complex HR tasks:

- **Reasoning**: The agent thinks through problems step by step
- **Acting**: The agent uses tools to gather information and take actions
- **Tool Integration**: Uses HR MCP server tools for vacation management

## Features

- **Intelligent Vacation Management**: Check balances and book time off with reasoning
- **Multi-step Problem Solving**: Break down complex queries into manageable steps
- **Conditional Logic**: Make decisions based on available data
- **Simple Command Line Interface**: Easy to run and test

## Files

- `simple_agent.py` - Simplified ReACT agent implementation (command line)
- `streamlit_app.py` - **Streamlit web application (main interface)**
- `run_example.py` - Example runner script for command line
- `requirements.txt` - Python dependencies
- `Containerfile.streamlit` - Container build instructions for Streamlit app
- `agent.py` - Original complex implementation (for reference)
- `web_interface.py` - FastAPI web interface (alternative)

## Quick Start

### Option 1: Streamlit Web Interface (Recommended)

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Run Streamlit App**
```bash
streamlit run streamlit_app.py
```

3. **Open your browser** to `http://localhost:8501`

4. **Configure** Llama Stack connection in the sidebar (host: localhost, port: 11011)

5. **Try the example queries** or enter your own!

### Option 2: Command Line Interface

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Run the Example**
```bash
python run_example.py
```

3. **Or Run Directly**
```bash
python simple_agent.py --host localhost --port 11011
```

### Option 3: Container Deployment

```bash
# Build the Streamlit container (UBI-based, OpenShift-ready) for AMD64 platform
podman build --platform linux/amd64 -f Containerfile.streamlit -t quay.io/hayesphilip/llama-stack-react:latest .

# Run the container
podman run -p 8501:8501 react-agent-streamlit

# The container runs as non-root user (1001) and is OpenShift-compatible
```

## Example Queries

The agent will automatically test these HR scenarios:

### 1. Simple Vacation Balance Check
```
What is the vacation balance for employee EMP001?
```

### 2. Conditional Vacation Booking (Your Example!)
```
If user EMP001 has enough remaining vacation days, book two days off for 2nd and 3rd of July 2025
```

### 3. Multi-step Analysis and Recommendations
```
Check if EMP001 has any vacation days left, and if so, suggest when they might want to use them based on their remaining balance
```

## ReACT Process Flow

1. **User Query**: Receives complex request
2. **Reasoning**: Agent thinks through what information is needed  
3. **Tool Selection**: Chooses HR MCP tools based on reasoning
4. **Tool Execution**: Calls HR MCP server to gather data
5. **Analysis**: Processes tool results and determines next steps
6. **Action**: Takes appropriate actions (e.g., booking vacation)
7. **Response**: Provides comprehensive answer with step-by-step reasoning

## Configuration

The agent connects to:
- **Llama Stack Server**: `http://localhost:11011` (configurable)
- **HR MCP Server**: Via `mcp::hr-api-tools` tool

## Expected Output

When you run the example, you'll see:
- 🤔 **Reasoning steps** as the agent thinks through problems
- 🛠️ **Tool executions** when calling HR MCP server
- ✅ **Results and decisions** based on the data gathered
- 📊 **Final responses** with complete reasoning chains

This demonstrates how ReACT agents can provide intelligent, step-by-step reasoning for enterprise HR operations!

# Building

 podman build -t quay.io/hayesphilip/llama-stack-react:latest --platform=linux/amd64  -f Containerfile.streamlit .