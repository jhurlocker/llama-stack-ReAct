#!/usr/bin/env python3
"""
Simple ReACT Agent for HR Operations

A simplified implementation based on the weather MCP example,
updated to use the HR MCP server for vacation management.
"""

import os
import uuid
import logging

import fire
from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.react.agent import ReActAgent
from llama_stack_client.lib.agents.react.tool_parser import ReActOutput
from llama_stack_client.lib.agents.event_logger import EventLogger
from termcolor import colored

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main(host: str = "llama-stack", port: int = 80):
    """
    Main function to run the HR ReACT agent
    
    Args:
        host: Llama Stack server host (default: llama-stack)
        port: Llama Stack server port (default: 80)
    """
    client = LlamaStackClient(
        base_url=f"http://{host}:{port}"
    )

    # Get available models
    available_models = [
        model.identifier for model in client.models.list() if model.model_type == "llm"
    ]
    if not available_models:
        print(colored("No available models. Exiting.", "red"))
        return

    selected_model = available_models[0]
    print(colored(f"Using model: {selected_model}", "green"))

    # Initialize ReActAgent with HR MCP server tools
    logger.info("Creating ReActAgent with response format schema...")
    schema = ReActOutput.model_json_schema()
    logger.debug(f"ReActOutput schema: {schema}")
    
    try:
        agent = ReActAgent(
            client=client,
            model=selected_model,
            tools=[
                "mcp::hr-api-tools",  # HR MCP server
            ],
            response_format={
                "type": "json_schema",
                "json_schema": schema,
            },
            sampling_params={
                "strategy": {"type": "top_p", "temperature": 1.0, "top_p": 0.9},
            }
        )
        logger.info("ReActAgent created successfully")
    except Exception as e:
        logger.error(f"Failed to create ReActAgent: {e}")
        raise

    # Create a session
    session_id = agent.create_session(f"hr-react-session-{uuid.uuid4().hex}")

    # HR-focused user prompts
    user_prompts = [
        "What is the vacation balance for employee EMP001?",
        "If user EMP001 has enough remaining vacation days, book two days off for 2nd and 3rd of July 2025",
        "Check if EMP001 has any vacation days left, and if so, suggest when they might want to use them based on their remaining balance",
    ]

    print(colored("\n🤖 HR ReACT Agent initialized! Testing vacation management capabilities...\n", "green"))

    for prompt in user_prompts:
        print(colored(f"User> {prompt}", "blue"))
        print(colored("=" * 80, "yellow"))
        
        try:
            logger.info(f"Creating turn for prompt: {prompt}")
            response = agent.create_turn(
                messages=[{"role": "user", "content": prompt}],
                session_id=session_id,
                stream=True,
            )
            logger.info("Turn created, processing response stream...")

            # Log the ReACT reasoning and tool usage
            for log in EventLogger().log(response):
                try:
                    # Log the raw event before printing
                    logger.debug(f"Processing event: {type(log)} - {log}")
                    log.print()
                except Exception as log_error:
                    logger.error(f"Error processing log event: {log_error}")
                    logger.error(f"Raw log event: {log}")
                    if hasattr(log, 'raw_content'):
                        logger.error(f"Raw content: {log.raw_content}")
                    if hasattr(log, '_raw_message'):
                        logger.error(f"Raw message: {log._raw_message}")
                    # Try to extract any JSON content for debugging
                    log_str = str(log)
                    if '{' in log_str and '}' in log_str:
                        start_idx = log_str.find('{')
                        end_idx = log_str.rfind('}') + 1
                        potential_json = log_str[start_idx:end_idx]
                        logger.error(f"Potential JSON content: {potential_json}")
            
        except Exception as e:
            logger.error(f"Error in turn processing: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        print(colored("\n" + "=" * 80 + "\n", "yellow"))


if __name__ == "__main__":
    fire.Fire(main)