#!/usr/bin/env python3
"""
Simple HR MCP Server - Demo server with one tool to check vacation balance.
"""

from typing import Any
import httpx
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server for HR tools (SSE)
mcp = FastMCP("hr-tools")

# Constants
HR_API_BASE = os.getenv("HR_API_BASE_URL", "http://hr-enterprise-api:80")
HR_API_KEY = os.getenv("HR_API_KEY", "hr-api-default-key")

async def make_hr_request(url: str, method: str = "GET", data: dict = None) -> dict[str, Any] | None:
    """Make a request to the HR API with proper error handling."""
    headers = {
        "X-API-Key": HR_API_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers, timeout=30.0)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data, timeout=30.0)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"HR API request failed: {e}")
            return None

@mcp.tool()
async def get_vacation_balance(employee_id: str) -> str:
    """Get vacation balance for an employee.

    Args:
        employee_id: Employee ID (e.g. EMP001)
    """
    url = f"{HR_API_BASE}/api/v1/vacations/balance/{employee_id}"
    data = await make_hr_request(url)

    if not data:
        return f"Unable to fetch vacation balance for employee {employee_id}."

    return f"""Vacation Balance for {employee_id}:
• Annual Leave: {data['remainingAnnual']}/{data['annualDays']} days remaining
• Sick Leave: {data['remainingSick']}/{data['sickDays']} days remaining
• Personal Leave: {data['remainingPersonal']}/{data['personalDays']} days remaining"""

@mcp.tool()
async def create_vacation_request(
    employee_id: str,
    vacation_type: str,
    start_date: str,
    end_date: str,
    days: int,
    reason: str
) -> str:
    """Create a new vacation request for an employee.

    Args:
        employee_id: Employee ID (e.g. EMP001)
        vacation_type: Type of vacation - MUST be one of: "annual", "sick", "personal", "maternity", "paternity"
        start_date: Start date in YYYY-MM-DD format (e.g. "2025-07-02")
        end_date: End date in YYYY-MM-DD format (e.g. "2025-07-03")
        days: Number of vacation days (integer, e.g. 2)
        reason: Reason for the vacation request (e.g. "Vacation time off")
        
    Example usage:
        create_vacation_request("EMP001", "annual", "2025-07-02", "2025-07-03", 2, "Summer vacation")
    """
    url = f"{HR_API_BASE}/api/v1/vacations"
    
    vacation_data = {
        "employeeId": employee_id,
        "type": vacation_type,
        "startDate": start_date,
        "endDate": end_date,
        "days": days,
        "reason": reason
    }
    
    data = await make_hr_request(url, method="POST", data=vacation_data)

    if not data:
        return f"Unable to create vacation request for employee {employee_id}."

    return f"""Vacation Request Created Successfully!
• Request ID: {data.get('id', 'N/A')}
• Employee: {data.get('employeeId', employee_id)}
• Type: {data.get('type', vacation_type)}
• Dates: {data.get('startDate', start_date)} to {data.get('endDate', end_date)}
• Days: {data.get('days', days)}
• Status: {data.get('status', 'pending')}
• Reason: {data.get('reason', reason)}"""

def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can serve the provided mcp server with SSE."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> Response:
        """Handle SSE connection for MCP server communication."""
        try:
            logger.info("Handling SSE connection")
            
            # Ensure we have proper access to the send function
            send_func = getattr(request, '_send', None)
            if send_func is None:
                logger.error("Request._send is None, cannot establish SSE connection")
                return Response("SSE connection failed: send function not available", status_code=500)
            
            async with sse.connect_sse(
                    request.scope,
                    request.receive,
                    send_func,
            ) as (read_stream, write_stream):
                logger.info("SSE connection established, starting MCP server")
                await mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp_server.create_initialization_options(),
                )
                logger.info("MCP server run completed")
                
        except Exception as e:
            logger.error(f"SSE handler error: {e}")
            return Response(f"SSE handler error: {str(e)}", status_code=500)
        
        # Return empty response - SSE connection handles its own response
        return Response()

    async def handle_health(request: Request) -> Response:
        """Health check endpoint."""
        from starlette.responses import JSONResponse
        return JSONResponse({
            "status": "healthy",
            "server": "hr-mcp-server",
            "hr_api_url": HR_API_BASE,
            "mcp_server_initialized": mcp_server is not None
        })

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/health", endpoint=handle_health),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run HR MCP SSE-based server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to listen on')
    args = parser.parse_args()

    # Initialize MCP server with proper error handling
    try:
        mcp_server = mcp._mcp_server  # noqa: WPS437
        if mcp_server is None:
            logger.error("Failed to initialize MCP server - mcp._mcp_server is None")
            exit(1)
        
        logger.info(f"MCP server initialized successfully: {type(mcp_server)}")
        logger.info(f"Starting HR MCP Server on {args.host}:{args.port}")
        logger.info(f"SSE endpoint: http://{args.host}:{args.port}/sse")
        logger.info(f"Health endpoint: http://{args.host}:{args.port}/health")

        # Bind SSE request handling to MCP server
        starlette_app = create_starlette_app(mcp_server, debug=True)

        uvicorn.run(starlette_app, host=args.host, port=args.port)
        
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        exit(1)