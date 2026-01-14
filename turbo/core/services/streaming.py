"""Streaming service for real-time AI responses."""

import json
import logging
import os
from typing import AsyncGenerator
from uuid import UUID

import httpx

from turbo.core.database.connection import get_db_session
from turbo.core.services.conversation_context import ConversationContextManager
from turbo.core.services.conversation_memory import ConversationMemoryService
from turbo.core.services.graph import GraphService
from turbo.core.services.tools_registry import get_turbo_tools, filter_tools_by_capabilities
from turbo.core.services.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)

# Get Turbo API URL
TURBO_API_URL = os.getenv("TURBO_API_URL", "http://localhost:8001/api/v1")


async def get_anthropic_api_key() -> str:
    """Retrieve Anthropic API key from database or environment."""
    # Try to get from internal API endpoint (database)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{TURBO_API_URL}/settings/claude/api-key/raw")
            if response.status_code == 200:
                data = response.json()
                api_key = data.get("api_key")
                if api_key:
                    return api_key
    except Exception as e:
        logger.warning(f"Failed to get API key from database: {e}")

    # Fallback to environment variable
    env_key = os.getenv("ANTHROPIC_API_KEY")
    if env_key and not env_key.startswith("your_api_key"):
        return env_key

    raise ValueError("ANTHROPIC_API_KEY not configured. Please set it via the settings UI or environment variable.")


async def get_streaming_response(
    entity_type: str,
    entity_id: UUID,
    user_message_content: str
) -> AsyncGenerator[str, None]:
    """
    Stream AI response for a conversation message.

    Args:
        entity_type: Type of entity ("staff" - mentor is deprecated)
        entity_id: UUID of the staff member
        user_message_content: The user's message content

    Yields:
        String chunks of the AI response as they are generated
    """
    # Get API key from database or environment
    ANTHROPIC_API_KEY = await get_anthropic_api_key()

    # Fetch entity and build enhanced context
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch staff member details
        entity_response = await client.get(f"{TURBO_API_URL}/staff/{entity_id}")
        entity_response.raise_for_status()
        entity = entity_response.json()

        # Get messages for context
        messages_response = await client.get(
            f"{TURBO_API_URL}/staff/{entity_id}/messages",
            params={"limit": 100}
        )
        messages_response.raise_for_status()
        messages_data = messages_response.json()
        messages = messages_data.get("messages", [])

    # Build enhanced context
    async for db in get_db_session():
        try:
            graph_service = GraphService()
            memory_service = ConversationMemoryService(db, ANTHROPIC_API_KEY)
            context_manager = ConversationContextManager(db, memory_service, graph_service)

            context = await context_manager.build_context(
                entity_type=entity_type,
                entity_id=entity_id,
                current_message=user_message_content
            )

            # Trigger memory extraction every 10 messages
            if len(messages) % 10 == 0 and len(messages) > 0:
                await context_manager.trigger_memory_extraction(
                    entity_type=entity_type,
                    entity_id=entity_id
                )

            break
        except Exception as e:
            logger.error(f"Failed to build enhanced context: {e}", exc_info=True)
            context = None
            break

    # Build prompt from context
    from scripts.claude_webhook_server import build_enhanced_staff_prompt, build_basic_staff_prompt

    if context:
        user_prompt = build_enhanced_staff_prompt(entity, context)
    else:
        # Fallback to basic prompt
        conversation_lines = []
        for msg in messages[-20:]:
            role = "User" if msg["message_type"] == "user" else "Staff"
            conversation_lines.append(f"**{role}:** {msg['content']}\n")
        conversation_history = "\n".join(conversation_lines) if conversation_lines else "_No previous conversation_"

        user_prompt = build_basic_staff_prompt(entity, conversation_history)

    system_prompt = f"""You are {entity.get('name', 'Unknown')}, a {entity.get('role_type', 'leadership')} staff member.

**Your Role**:
- Adopt the staff member's defined persona and communication style
- Provide expert guidance within your domain
- Be direct, professional, and action-oriented
- Help coordinate work and remove blockers
- Provide strategic and tactical guidance

**Your Persona**:
{entity.get('persona', '')}

**Your Capabilities**:
{', '.join(entity.get('capabilities', []))}
"""

    # Get tools based on staff capabilities
    all_tools = get_turbo_tools()
    entity_capabilities = entity.get("capabilities", [])
    filtered_tools = filter_tools_by_capabilities(all_tools, entity_capabilities)

    # Stream from Claude API
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    request_body = {
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": 4096,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
        "tools": filtered_tools,  # Add tools based on staff capabilities
        "stream": True  # Enable streaming
    }

    # Tool executor
    tool_executor = ToolExecutor(TURBO_API_URL)

    # Track conversation for tool use
    conversation_messages = [{"role": "user", "content": user_prompt}]

    # Maximum 5 tool use rounds to prevent infinite loops
    for round_num in range(5):
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream(
                    "POST",
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=request_body
                ) as response:
                    # Check for HTTP errors
                    if response.status_code != 200:
                        # For streaming responses, read error from stream
                        error_chunks = []
                        async for chunk in response.aiter_bytes():
                            error_chunks.append(chunk)
                        error_text = b"".join(error_chunks).decode()
                        logger.error(f"Claude API error {response.status_code}: {error_text}")
                        yield f"\n\n_[Error: Claude API returned {response.status_code}. Check API key and request format.]_\n\n"
                        return

                    # Collect the full response
                    assistant_content = []
                    current_text = ""
                    current_tool_use = None
                    tool_input_json = ""

                    # Parse SSE stream from Claude
                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix

                            if data_str == "[DONE]":
                                break

                            try:
                                data = json.loads(data_str)

                                # Handle content block start
                                if data.get("type") == "content_block_start":
                                    block = data.get("content_block", {})
                                    if block.get("type") == "text":
                                        current_text = ""
                                    elif block.get("type") == "tool_use":
                                        current_tool_use = {
                                            "type": "tool_use",
                                            "id": block.get("id"),
                                            "name": block.get("name"),
                                            "input": {}
                                        }
                                        tool_input_json = ""
                                        # Notify user that tool is being used
                                        yield f"\n\n_[Using tool: {block.get('name')}...]_\n\n"

                                # Handle content deltas
                                elif data.get("type") == "content_block_delta":
                                    delta = data.get("delta", {})

                                    if delta.get("type") == "text_delta":
                                        # Stream text chunks
                                        text = delta.get("text", "")
                                        if text:
                                            current_text += text
                                            yield text

                                    elif delta.get("type") == "input_json_delta":
                                        # Accumulate tool input JSON
                                        tool_input_json += delta.get("partial_json", "")

                                # Handle content block stop
                                elif data.get("type") == "content_block_stop":
                                    if current_text:
                                        assistant_content.append({
                                            "type": "text",
                                            "text": current_text
                                        })
                                        current_text = ""
                                    elif current_tool_use:
                                        # Parse completed tool input
                                        try:
                                            current_tool_use["input"] = json.loads(tool_input_json)
                                        except json.JSONDecodeError:
                                            current_tool_use["input"] = {}
                                        assistant_content.append(current_tool_use)
                                        current_tool_use = None
                                        tool_input_json = ""

                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse SSE data: {data_str}")
                                continue

                    # Check if any tools were used
                    tool_uses = [block for block in assistant_content if block.get("type") == "tool_use"]

                    if not tool_uses:
                        # No tools used, we're done
                        break

                    # Execute tools and prepare next round
                    tool_results = []
                    for tool_use in tool_uses:
                        tool_name = tool_use["name"]
                        tool_input = tool_use["input"]
                        tool_id = tool_use["id"]

                        logger.info(f"Executing tool: {tool_name} with input: {tool_input}")
                        result = await tool_executor.execute_tool(tool_name, tool_input)

                        # Convert result to string and truncate if too large
                        result_str = json.dumps(result)
                        max_result_size = 10000  # 10k characters max per tool result

                        if len(result_str) > max_result_size:
                            # Truncate large results
                            truncated_result = {
                                "truncated": True,
                                "size": len(result_str),
                                "preview": result_str[:max_result_size],
                                "message": f"Result too large ({len(result_str)} chars), showing first {max_result_size} chars"
                            }
                            result_content = json.dumps(truncated_result)
                            logger.warning(f"Tool result truncated: {len(result_str)} chars -> {max_result_size} chars")
                        else:
                            result_content = result_str

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result_content
                        })

                        # Show tool result to user (truncated for display)
                        display_result = result_str[:500] + "..." if len(result_str) > 500 else result_str
                        yield f"_[Tool executed: {tool_name}]_\n\n"

                    # Build next request with tool results
                    conversation_messages.append({"role": "assistant", "content": assistant_content})
                    conversation_messages.append({"role": "user", "content": tool_results})

                    request_body["messages"] = conversation_messages

            except httpx.HTTPStatusError as e:
                # HTTP error from Claude API
                logger.error(f"Claude API HTTP error: {e}", exc_info=True)
                yield f"\n\n_[Error: Claude API request failed with status {e.response.status_code}]_\n\n"
                return
            except Exception as e:
                # Other errors (timeout, network, etc.)
                logger.error(f"Streaming error: {e}", exc_info=True)
                yield f"\n\n_[Error: {str(e)}]_\n\n"
                return

    # If we hit max rounds, warn user
    if round_num >= 4:
        yield "\n\n_[Warning: Maximum tool use rounds reached]_"
