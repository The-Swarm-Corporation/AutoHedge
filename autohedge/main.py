from pathlib import Path

from loguru import logger
from swarms import Conversation

from autohedge.backends import create_director, resolve_llm_backend


class AutoHedge:
    """
    Main trading system that coordinates all agents and manages the trading cycle.
    Tickers to analyze are derived from the task by the director (no predefined list).

    ``llm_backend="codex"`` selects a research-only pipeline on supplied data.
    ``codex_config`` accepts ``model`` and a per-stage ``timeout``. Explicit
    values take precedence over AUTOHEDGE_LLM_BACKEND and AUTOHEDGE_CODEX_*
    environment settings. The default backend remains ``litellm``.
    """

    def __init__(
        self,
        name: str = "autohedge",
        description: str = "fully autonomous hedgefund",
        output_dir: str = "outputs",
        output_file_path: str = None,
        output_type: str = "list",
        llm_backend: str | None = None,
        codex_config: dict | None = None,
    ):
        self.llm_backend = resolve_llm_backend(llm_backend)
        self.director = create_director(
            self.llm_backend, codex_config
        )
        self.name = name
        self.description = description
        self.output_type = output_type
        self.output_file_path = output_file_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        logger.info(
            "Initializing AutoHedge research workflow"
            if self.llm_backend == "codex"
            else "Initializing Automated Trading System"
        )
        self.conversation = Conversation(time_enabled=True)

    def run(self, task: str, *args, **kwargs):
        """
        Execute one complete trading cycle for all stocks.

        Args:
            task (str): The task to be executed.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            List: List of logs for each stock.
        """
        logger.info(
            "Starting research cycle"
            if self.llm_backend == "codex"
            else "Starting trading cycle"
        )
        self.conversation.add(role="user", content=f"Task: {task}")

        try:
            output = self.director.run(task=task)
            self.conversation.add(role="director", content=output)

            if self.output_type == "list":
                return self.conversation.return_messages_as_list()
            if self.output_type == "dict":
                return (
                    self.conversation.return_messages_as_dictionary()
                )
            if self.output_type == "str":
                return self.conversation.return_history_as_string()
            return self.conversation.return_messages_as_list()
        except Exception as e:
            logger.error(f"Error in trading cycle: {str(e)}")
            raise
