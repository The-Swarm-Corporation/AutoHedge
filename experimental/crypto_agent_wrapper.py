import os

import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from swarms import Agent

from cryptoagent.main import CryptoAgent
from cryptoagent.prompts import CRYPTO_AGENT_SYS_PROMPT


class CryptoAgentWrapper:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=self.api_key)

        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
        ]

        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=GenerationConfig(temperature=0.1),
            safety_settings=safety_settings,
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
