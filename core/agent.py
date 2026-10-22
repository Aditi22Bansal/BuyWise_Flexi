from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class AgentMessage:
    id: str = field(default_factory=lambda: str(uuid4()))
    sender: str = ""
    recipient: str = ""
    action: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    correlation_id: Optional[str] = None


class AgentContext:
    """Shared context passed between agents during a procurement run."""

    def __init__(self, requirement, settings):
        self.requirement = requirement
        self.settings = settings
        self.products: List[Any] = []
        self.vendors: List[Any] = []
        self.quotes: List[Any] = []
        self.evaluations: List[Any] = []
        self.negotiation_results: List[Any] = []
        self.decision: Optional[Any] = None
        self.messages: List[AgentMessage] = []
        self.metadata: Dict[str, Any] = {}

    def add_message(self, message: AgentMessage):
        self.messages.append(message)

    def get_messages(self, sender: Optional[str] = None,
                     recipient: Optional[str] = None,
                     action: Optional[str] = None) -> List[AgentMessage]:
        result = self.messages
        if sender:
            result = [m for m in result if m.sender == sender]
        if recipient:
            result = [m for m in result if m.recipient == recipient]
        if action:
            result = [m for m in result if m.action == action]
        return result


class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def execute(self, context: AgentContext) -> AgentContext:
        pass

    def _emit(self, context: AgentContext, recipient: str, action: str,
              payload: Dict[str, Any], correlation_id: Optional[str] = None) -> AgentMessage:
        msg = AgentMessage(
            sender=self.name,
            recipient=recipient,
            action=action,
            payload=payload,
            correlation_id=correlation_id,
        )
        context.add_message(msg)
        return msg

    def log(self, context: AgentContext, message: str):
        entry = f"[{self.name}] {message}"
        context.metadata.setdefault("logs", []).append(entry)
        print(entry)


class Orchestrator:
    def __init__(self, agents: List[BaseAgent]):
        self.agents = agents
        self.agent_map = {a.name: a for a in agents}

    def run(self, context: AgentContext) -> AgentContext:
        for agent in self.agents:
            context = agent.execute(context)
        return context

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        return self.agent_map.get(name)