# Ensure all models are imported so SQLAlchemy create_all discovers them
from app.models.agent import Agent  # noqa: F401
from app.models.api_key import APIKey  # noqa: F401
from app.models.checkpoint import ExecutionCheckpoint  # noqa: F401
from app.models.condition import ConditionBranch  # noqa: F401
from app.models.crew import Crew, ProcessType  # noqa: F401
from app.models.execution import Execution, TaskExecution  # noqa: F401
from app.models.flow_config import FlowConfig  # noqa: F401
from app.models.human_review import HumanReviewConfig  # noqa: F401
from app.models.iteration import Iteration  # noqa: F401
from app.models.llm_provider import LLMProvider  # noqa: F401
from app.models.loop import LoopConfig  # noqa: F401
from app.models.mcp_server import MCPServer  # noqa: F401
from app.models.memory import AgentKnowledgeMapping, AgentMemory, MemoryConfig  # noqa: F401
from app.models.plugin import PluginConfig  # noqa: F401
from app.models.plugin_review import PluginReview  # noqa: F401
from app.models.published_workflow import PublishedWorkflow  # noqa: F401
from app.models.scheduled_task import ScheduledTask  # noqa: F401
from app.models.skill import Skill  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.template import Template  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.webhook import Webhook  # noqa: F401
