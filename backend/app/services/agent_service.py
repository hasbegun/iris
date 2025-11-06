"""
LangChain Agent Service using ReAct Pattern
Orchestrates LLM with vision analysis and YOLO detection tools for intelligent image analysis
"""
try:
    from langchain.agents import create_react_agent, AgentExecutor
except ImportError:
    try:
        # Try newer import path
        from langchain.agents import AgentExecutor
        from langchain.agents.react.agent import create_react_agent
    except ImportError:
        # Fallback: define a stub that will be caught later
        AgentExecutor = None
        create_react_agent = None
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import render_text_description
from langchain_ollama import ChatOllama
from typing import Dict, List, Optional
import logging

from app.config import settings
from app.services.vision_tools import create_vision_tools
from app.services.context_manager import context_manager
from app.services.agent_prompt import instruction_addition, REACT_TEMPLATE_FALLBACK

logger = logging.getLogger(__name__)


class VisionAgentService:
    """
    Vision Agent Service using LangChain ReAct pattern
    Integrates LLM with vision analysis and YOLO detection tools for intelligent image queries

    Following the ReAct (Reasoning and Action) framework for better compatibility with Ollama
    """

    def __init__(self):
        """Initialize the vision agent framework (LLM and prompt)"""
        self.llm = None
        self.prompt_template = None
        self.initialized = False
        self.initialization_error = None

        try:
            self._initialize_llm_and_prompt()
            self.initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            logger.warning("Agent will not be available. Direct ML service calls will still work.")
            self.initialization_error = str(e)

    def _initialize_llm_and_prompt(self):
        """
        Initialize LLM and prompt template (tools created per-request with session_id)
        Uses ReAct (Reasoning and Action) framework for better Ollama compatibility
        """
        try:
            logger.info(f"Initializing vision agent with model: {settings.agent_llm_model}")

            # Initialize Ollama LLM with ReAct-compatible settings
            self.llm = ChatOllama(
                model=settings.agent_llm_model,
                base_url=settings.ollama_host,
                temperature=0,  # Zero temperature for more deterministic tool selection
            )
            logger.info(f"Initialized LLM: {settings.agent_llm_model}")

            # Store prompt template (will be customized per request with tools)
            self.prompt_template = REACT_TEMPLATE_FALLBACK

            logger.info("✅ Vision agent (ReAct pattern) initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize agent: {e}", exc_info=True)
            raise

    def _create_agent_for_session(self, session_id: str):
        """
        Create an agent with tools bound to a specific session.

        This approach allows tools to have simple signatures that work better
        with the ReAct parser.

        Args:
            session_id: The session ID to bind to tools

        Returns:
            AgentExecutor ready for this session
        """
        # Create tools with session_id pre-bound
        tools = create_vision_tools(session_id)

        # Render tool descriptions
        tool_strings = render_text_description(tools)
        tool_names = ", ".join([t.name for t in tools])

        logger.debug(f"Created tools for session {session_id}: {tool_names}")

        # Create prompt with tools
        prompt = PromptTemplate.from_template(self.prompt_template)
        prompt = prompt.partial(
            tools=tool_strings,
            tool_names=tool_names,
            instruction_addition=instruction_addition
        )

        # Bind stop sequence
        llm_with_stop = self.llm.bind(stop=["\nObservation:"])

        # Create ReAct agent
        agent = create_react_agent(
            llm=llm_with_stop,
            tools=tools,
            prompt=prompt
        )

        # Create executor
        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=settings.agent_verbose,
            max_iterations=settings.agent_max_iterations,
            handle_parsing_errors=True
        )

        return executor

    async def analyze_query(
        self,
        query: str,
        session_id: str,
        chat_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Analyze a user query about an image using the ReAct agent

        The agent will reason about which tools to use and execute them automatically.
        Tools are created with session_id pre-bound for simpler parsing.

        Args:
            query: User's question about the image
            session_id: Session ID to retrieve the image
            chat_history: Optional conversation history (not used in ReAct pattern)

        Returns:
            Agent response dictionary
        """
        # Check if agent is initialized
        if not self.initialized:
            return {
                "status": "error",
                "query": query,
                "response": f"Agent is not available. Error: {self.initialization_error}. Please use direct detection endpoints instead.",
                "session_id": session_id
            }

        try:
            # Create agent executor with tools bound to this session
            executor = self._create_agent_for_session(session_id)

            # Run agent using ReAct pattern with simple query
            logger.info(f"Running ReAct agent for query: '{query}' (session: {session_id})")
            result = await executor.ainvoke({"input": query})

            # Extract output and sanitize technical errors
            output = result.get("output", "")

            # Check for technical error messages and replace with user-friendly ones
            if not output or len(output.strip()) == 0:
                response_text = "I couldn't process your request. Please try rephrasing your question."
            elif "iteration limit" in output.lower() or "time limit" in output.lower():
                response_text = "I'm having trouble processing this request. Could you try asking something simpler or more specific?"
            elif "agent stopped" in output.lower():
                response_text = "I couldn't complete that analysis. Please try rephrasing your question or asking about something more specific."
            elif output.startswith("Error:") or output.startswith("error:"):
                # Keep user-friendly tool errors but clean them up
                response_text = output
            else:
                response_text = output

            # Build response
            response = {
                "status": "success",
                "query": query,
                "response": response_text,
                "session_id": session_id
            }

            logger.info(f"Agent response generated successfully")
            return response

        except Exception as e:
            logger.error(f"Agent analysis failed: {e}", exc_info=True)
            return {
                "status": "error",
                "query": query,
                "response": "I encountered an error while analyzing your image. Please try again.",
                "session_id": session_id
            }

    async def simple_detect(
        self,
        session_id: str,
        object_types: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> Dict:
        """
        Simple object detection without agent (direct tool call)
        Useful for quick detections without LLM overhead

        Args:
            session_id: Session ID
            object_types: Comma-separated object types
            confidence: Detection confidence (ignored, always uses 0.7)

        Returns:
            Detection results
        """
        try:
            # Create tools for this session
            tools = create_vision_tools(session_id)

            # Get the find_objects tool
            find_objects_tool = next((t for t in tools if t.name == "find_objects"), None)
            if not find_objects_tool:
                raise Exception("find_objects tool not found")

            # Call the tool with object types
            result = await find_objects_tool.ainvoke({"objects": object_types or ""})

            return {
                "status": "success",
                "message": result,
                "session_id": session_id
            }
        except Exception as e:
            logger.error(f"Simple detection failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }


# Singleton instance
vision_agent = VisionAgentService()
