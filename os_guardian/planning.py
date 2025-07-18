from __future__ import annotations

"""LangChain-based planner turning instructions into tool sequences.

The planner exposes :class:`GuardianPlanner` which builds a small LangChain agent
using the perception and action modules as tools. Generated plans are stored in a
vector store so future instructions may reference past context.
"""

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import List, Sequence

try:  # pragma: no cover - optional dependency
    from langchain.agents import AgentType, Tool, initialize_agent
    from langchain.chat_models import ChatOpenAI
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.memory import VectorStoreRetrieverMemory
    from langchain.schema import Document
    from langchain.vectorstores import FAISS
except Exception:  # pragma: no cover - optional dependency
    AgentType = Tool = initialize_agent = None  # type: ignore
    ChatOpenAI = None  # type: ignore
    HuggingFaceEmbeddings = None  # type: ignore
    VectorStoreRetrieverMemory = None  # type: ignore
    Document = None  # type: ignore
    FAISS = None  # type: ignore

from . import action_engine, perception

logger = logging.getLogger(__name__)

_MEMORY_DIR = Path("data/os_guardian_memory")


def _load_memory(path: Path = _MEMORY_DIR) -> VectorStoreRetrieverMemory | None:
    """Return a vector memory instance stored at ``path`` if possible."""
    if FAISS is None or HuggingFaceEmbeddings is None or VectorStoreRetrieverMemory is None:
        return None
    path.mkdir(parents=True, exist_ok=True)
    emb = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    index = path / "faiss"
    if index.exists():
        store = FAISS.load_local(str(index), emb)
    else:
        store = FAISS.from_texts([], emb)
        store.save_local(str(index))
    retriever = store.as_retriever(search_kwargs={"k": 4})
    return VectorStoreRetrieverMemory(retriever=retriever)


def _get_tools() -> Sequence[Tool]:
    if Tool is None:
        return []
    return [
        Tool.from_function(
            name="analyze_frame",
            func=perception.analyze_frame,
            description="Analyze a screen capture for UI elements",
        ),
        Tool.from_function(
            name="click",
            func=action_engine.click,
            description="Click on screen coordinates",
        ),
        Tool.from_function(
            name="type_text",
            func=action_engine.type_text,
            description="Type text with the keyboard",
        ),
        Tool.from_function(
            name="open_url",
            func=action_engine.open_url,
            description="Open a URL in the browser",
        ),
    ]


@dataclass
class GuardianPlanner:
    """LangChain agent wrapper for OS Guardian planning."""

    memory_path: Path = _MEMORY_DIR
    llm: ChatOpenAI | None = None

    def __post_init__(self) -> None:  # pragma: no cover - init
        if self.llm is None and ChatOpenAI is not None:
            self.llm = ChatOpenAI(temperature=0)
        self.memory = _load_memory(self.memory_path)

    # Internal -----------------------------------------------------------------
    def _build_agent(self):
        if initialize_agent is None or self.llm is None:
            return None
        return initialize_agent(
            tools=_get_tools(),
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=False,
        )

    # Public API ---------------------------------------------------------------
    def plan(self, instruction: str) -> List[str]:
        """Generate an ordered list of tool invocations for ``instruction``."""
        agent = self._build_agent()
        if agent is None:
            logger.error("LangChain not available")
            return []
        result = agent.run(instruction)
        if self.memory is not None:
            self.memory.save_context({"instruction": instruction}, {"plan": result})
        return [
            line.lstrip("0123456789. -").strip()
            for line in result.splitlines()
            if line.strip()
        ]

    def interactive_plan(self, instruction: str, perception_feedback: str) -> List[str]:
        """Adjust a plan using additional perception feedback."""
        agent = self._build_agent()
        if agent is None:
            logger.error("LangChain not available")
            return []
        query = f"{instruction}\nFeedback: {perception_feedback}"
        result = agent.run(query)
        if self.memory is not None:
            self.memory.save_context({"instruction": query}, {"plan": result})
        return [
            line.lstrip("0123456789. -").strip()
            for line in result.splitlines()
            if line.strip()
        ]


def plan(command: str) -> List[str]:
    """Convenience wrapper returning plan steps for ``command``."""
    return GuardianPlanner().plan(command)


__all__ = ["plan", "GuardianPlanner"]
