#!/usr/bin/env python3
"""
Web Interface for ReACT Agent

Provides a simple web interface to interact with the ReACT agent
for HR operations and vacation management.
"""

import asyncio
import logging
from typing import Optional
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn

from agent import HRReActAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="ReACT Agent Interface", description="HR Operations with ReACT Agent")

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Global agent instance
react_agent: Optional[HRReActAgent] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the ReACT agent on startup"""
    global react_agent
    try:
        react_agent = HRReActAgent()
        await react_agent.initialize_agent()
        logger.info("ReACT Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize ReACT Agent: {e}")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main interface page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/query")
async def process_query(query: str = Form(...)):
    """Process a query through the ReACT agent"""
    if not react_agent:
        return JSONResponse(
            status_code=500,
            content={"error": "ReACT Agent not initialized"}
        )
    
    try:
        response = await react_agent.process_query(query)
        return JSONResponse(content={"response": response})
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to process query: {str(e)}"}
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent_initialized": react_agent is not None}

@app.get("/examples")
async def get_examples():
    """Get example queries for testing"""
    examples = [
        {
            "title": "Check Vacation Balance",
            "query": "What is the vacation balance for employee EMP001?",
            "description": "Simple query to check how many vacation days an employee has remaining"
        },
        {
            "title": "Conditional Vacation Booking",
            "query": "If user EMP001 has enough remaining vacation days, book two days off for 2nd and 3rd of July 2025",
            "description": "Complex conditional logic - check balance first, then book if sufficient days available"
        },
        {
            "title": "Multi-step Reasoning",
            "query": "Check if EMP001 has any vacation days left, and if so, suggest when they might want to use them based on their remaining balance",
            "description": "Demonstrates ReACT reasoning with analysis and recommendations"
        },
        {
            "title": "Vacation Request with Analysis",
            "query": "I want to book vacation for EMP001 from July 15-20, 2025. Check if they have enough days and book it if possible.",
            "description": "Date range booking with automatic balance checking"
        }
    ]
    return JSONResponse(content={"examples": examples})

if __name__ == "__main__":
    uvicorn.run(
        "web_interface:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )