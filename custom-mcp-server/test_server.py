#!/usr/bin/env python3
"""
Test script for the HR MCP Server to verify initialization
"""

import asyncio
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from server import mcp, create_starlette_app

async def test_mcp_server_initialization():
    """Test that the MCP server initializes correctly"""
    print("Testing MCP server initialization...")
    
    try:
        # Test FastMCP initialization
        print(f"FastMCP instance: {mcp}")
        print(f"FastMCP name: {mcp.name}")
        
        # Test MCP server access
        mcp_server = mcp._mcp_server
        print(f"Internal MCP server: {mcp_server}")
        print(f"MCP server type: {type(mcp_server)}")
        
        if mcp_server is None:
            print("❌ FAILED: MCP server is None")
            return False
        
        # Test Starlette app creation
        print("Testing Starlette app creation...")
        app = create_starlette_app(mcp_server, debug=True)
        print(f"Starlette app: {app}")
        print(f"Starlette routes: {[route.path for route in app.routes]}")
        
        print("✅ SUCCESS: All components initialized correctly")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tool_registration():
    """Test that tools are properly registered"""
    print("\nTesting tool registration...")
    
    try:
        # Get tools from FastMCP - try different attributes
        tools = None
        if hasattr(mcp, '_tools'):
            tools = mcp._tools
        elif hasattr(mcp, 'tools'):
            tools = mcp.tools
        elif hasattr(mcp, '_mcp_server') and hasattr(mcp._mcp_server, 'tools'):
            tools = mcp._mcp_server.tools
        
        if tools is None:
            print("No tools found in FastMCP instance")
            return False
            
        print(f"Tools type: {type(tools)}")
        
        if isinstance(tools, dict):
            print(f"Registered tools: {len(tools)}")
            for tool_name, tool_func in tools.items():
                print(f"  - {tool_name}: {tool_func}")
        elif isinstance(tools, list):
            print(f"Registered tools: {len(tools)}")
            for tool in tools:
                print(f"  - {tool}")
        else:
            print(f"Tools in unknown format: {tools}")
        
        print("✅ SUCCESS: Tools found")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("=== HR MCP Server Test Suite ===\n")
    
    success = True
    success &= await test_mcp_server_initialization()
    success &= test_tool_registration()
    
    print(f"\n=== Test Results ===")
    if success:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)