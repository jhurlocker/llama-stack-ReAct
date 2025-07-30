#!/usr/bin/env python3
"""
ReACT Agent for Llama Stack HR Operations

This agent demonstrates the ReACT (Reasoning + Acting) paradigm for
intelligent tool usage with Llama Stack. It can reason through complex
HR operations like checking vacation balances and booking time off.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

import httpx
from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.agent import ReActAgent
from llama_stack_client.types import (
    AgentTurnCreateRequest,
    AgentCreateRequest,
    Message,
    MessageRole,
    AgentCreate,
    AgentTurn,
    ReActAgentConfig,
    ToolCallMessage,
    ToolResultMessage,
    AgentSession,
    Attachment
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HRReActAgent:
    """
    ReACT Agent for HR operations with reasoning capabilities
    """
    
    def __init__(self, llama_stack_url: str = "http://llama-stack:11011", hr_api_url: str = "http://hr-api:3000"):
        self.client = LlamaStackClient(base_url=llama_stack_url)
        self.hr_api_url = hr_api_url
        self.model = "llama3.2:3b-instruct"
        self.agent_id = None
        self.current_session = None
        
        # Define available tools for HR operations
        self.tools = [
            {
                "name": "hr_vacation_balance",
                "description": "Check vacation balance for an employee",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employee_id": {
                            "type": "string",
                            "description": "Employee ID (e.g., EMP001)"
                        }
                    },
                    "required": ["employee_id"]
                }
            },
            {
                "name": "hr_vacation_request",
                "description": "Create a vacation request for an employee",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employee_id": {
                            "type": "string",
                            "description": "Employee ID (e.g., EMP001)"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for vacation request"
                        }
                    },
                    "required": ["employee_id", "start_date", "end_date"]
                }
            }
        ]
    
    async def initialize_agent(self):
        """Initialize the ReACT agent with Llama Stack"""
        try:
            # Create the agent
            agent_config = ReActAgentConfig(
                model=self.model,
                tools=self.tools,
                instructions="""You are an intelligent HR assistant that uses ReACT (Reasoning + Acting) to help with vacation management.

IMPORTANT: Always think step by step and show your reasoning process:
1. First, reason about what information you need
2. Use tools to gather that information
3. Analyze the results and reason about next steps
4. Take appropriate actions based on your analysis

For vacation requests:
- Always check vacation balance first before booking
- Verify the employee has enough days available
- Only book if sufficient days are available
- Provide clear feedback about the booking status

Use this format for your responses:
🤔 Reasoning: [Your thought process]
🛠 [Tool usage]
✅ [Final result/action]

Be helpful, accurate, and always explain your reasoning.""",
                enable_session_persistence=True,
                max_infer_iters=10
            )
            
            response = await self.client.agents.create(
                request=AgentCreateRequest(
                    agent_id=f"hr-react-agent-{datetime.now().isoformat()}",
                    config=agent_config
                )
            )
            
            self.agent_id = response.agent_id
            logger.info(f"Created ReACT agent with ID: {self.agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise
    
    async def create_session(self) -> str:
        """Create a new agent session"""
        try:
            response = await self.client.agents.create_session(
                agent_id=self.agent_id,
                request={}
            )
            self.current_session = response.session_id
            logger.info(f"Created session: {self.current_session}")
            return self.current_session
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HR tool calls by interacting with HR API"""
        try:
            async with httpx.AsyncClient() as client:
                if tool_name == "hr_vacation_balance":
                    employee_id = parameters["employee_id"]
                    response = await client.get(f"{self.hr_api_url}/api/vacations/{employee_id}")
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            "employee_id": employee_id,
                            "vacation_balance": data.get("balance", 0),
                            "total_days": data.get("total_days", 0),
                            "used_days": data.get("used_days", 0)
                        }
                    else:
                        return {"error": f"Failed to get vacation balance: {response.text}"}
                
                elif tool_name == "hr_vacation_request":
                    employee_id = parameters["employee_id"]
                    start_date = parameters["start_date"]
                    end_date = parameters["end_date"]
                    reason = parameters.get("reason", "Personal time off")
                    
                    request_data = {
                        "employee_id": employee_id,
                        "start_date": start_date,
                        "end_date": end_date,
                        "reason": reason,
                        "status": "approved"
                    }
                    
                    response = await client.post(
                        f"{self.hr_api_url}/api/vacations",
                        json=request_data
                    )
                    
                    if response.status_code == 201:
                        return {
                            "success": True,
                            "message": "Vacation request created successfully",
                            "booking_id": response.json().get("id"),
                            "employee_id": employee_id,
                            "start_date": start_date,
                            "end_date": end_date
                        }
                    else:
                        return {"error": f"Failed to create vacation request: {response.text}"}
                
                else:
                    return {"error": f"Unknown tool: {tool_name}"}
                    
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {"error": str(e)}
    
    async def process_query(self, query: str) -> str:
        """Process a user query using ReACT reasoning"""
        try:
            if not self.current_session:
                await self.create_session()
            
            # Create turn with user message
            messages = [
                Message(
                    role=MessageRole.user,
                    content=query
                )
            ]
            
            response = await self.client.agents.create_turn(
                agent_id=self.agent_id,
                session_id=self.current_session,
                request=AgentTurnCreateRequest(
                    messages=messages,
                    stream=False
                )
            )
            
            # Process the response and handle tool calls
            result_messages = []
            
            for event in response.events:
                if hasattr(event, 'payload'):
                    if hasattr(event.payload, 'tool_call'):
                        # Handle tool call
                        tool_call = event.payload.tool_call
                        tool_result = await self.execute_tool(
                            tool_call.tool_name,
                            tool_call.arguments
                        )
                        
                        # Send tool result back
                        tool_result_msg = ToolResultMessage(
                            call_id=tool_call.call_id,
                            tool_name=tool_call.tool_name,
                            content=json.dumps(tool_result)
                        )
                        result_messages.append(tool_result_msg)
                    
                    elif hasattr(event.payload, 'message'):
                        # Regular message
                        result_messages.append(event.payload.message)
            
            # Return the final response
            if result_messages:
                return result_messages[-1].content if hasattr(result_messages[-1], 'content') else str(result_messages[-1])
            else:
                return "No response generated"
                
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return f"Error processing query: {str(e)}"

async def main():
    """Main function to demonstrate ReACT agent usage"""
    agent = HRReActAgent()
    
    try:
        # Initialize the agent
        await agent.initialize_agent()
        
        # Test queries
        test_queries = [
            "What is the vacation balance for employee EMP001?",
            "If user EMP001 has enough remaining vacation days, book two days off for 2nd and 3rd of July 2025",
            "Check if EMP001 has any vacation days left, and if so, suggest when they might want to use them"
        ]
        
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print(f"{'='*60}")
            
            response = await agent.process_query(query)
            print(f"Response: {response}")
            
    except Exception as e:
        logger.error(f"Main execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())