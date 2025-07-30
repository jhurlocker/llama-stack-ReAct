#!/usr/bin/env python3
"""
Run the HR ReACT Agent example

This script demonstrates how to use the ReACT agent for HR operations
with step-by-step reasoning and tool execution.
"""

import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simple_agent import main

if __name__ == "__main__":
    print("🚀 Starting HR ReACT Agent Example...")
    print("This will demonstrate:")
    print("  1. Checking vacation balances")
    print("  2. Conditional vacation booking with reasoning")
    print("  3. Multi-step analysis and recommendations")
    print("\n" + "="*60 + "\n")
    
    # Run with default settings (localhost:11011)
    main()
    
    print("\n" + "="*60)
    print("✅ Example completed! The ReACT agent demonstrated:")
    print("  🤔 Step-by-step reasoning")
    print("  🛠️ Dynamic tool usage")
    print("  ✅ Intelligent decision making")
    print("  🔄 Multi-step problem solving")