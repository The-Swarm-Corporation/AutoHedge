import os

from swarm_models import OpenAIChat
from swarms import Agent

from cryptoagent.main import CryptoAgent
from cryptoagent.prompts import CRYPTO_AGENT_SYS_PROMPT


class CryptoAgentWrapper:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = OpenAIChat(
            openai_api_key=self.api_key,
            model_name="gpt-4o-mini",
            temperature=0.1,
        )
        self.input_agent = Agent(
            agent_name="Crypto-Analysis-Agent",
            system_prompt=CRYPTO_AGENT_SYS_PROMPT,
            llm=self.model,
            max_loops=1,
            autosave=True,
            dashboard=False,
            verbose=True,
            dynamic_temperature_enabled=True,
            saved_state_path="crypto_agent.json",
            user_name="swarms_corp",
            retry_attempts=1,
            context_length=10000,
        )
        self.crypto_analyzer = CryptoAgent(
            agent=self.input_agent, autosave=True
        )

    def run(self, coin_id: str, analysis_prompt: str) -> str:
        summaries = self.crypto_analyzer.run(
            [coin_id],
            analysis_prompt,
            # real_time=True,
        )
        return summaries


# # Example usage
# if __name__ == "__main__":
#     crypto_agent_wrapper = CryptoAgentWrapper()
#     coin_ids = ["bitcoin", "ethereum"]
#     analysis_prompt = "Conduct a thorough analysis of the following coins:"
#     summaries = crypto_agent_wrapper.summarize_crypto_data(coin_ids, analysis_prompt)
#     print(summaries)
