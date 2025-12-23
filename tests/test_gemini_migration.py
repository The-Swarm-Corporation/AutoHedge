import os
import sys
from dotenv import load_dotenv
from loguru import logger
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
dotenv_loaded = load_dotenv()
logger.info(f"dotenv loaded: {dotenv_loaded}")
logger.info(f"GOOGLE_API_KEY value from os.getenv: {os.getenv('GOOGLE_API_KEY')}")

try:
    from autohedge.main import AutoHedge
except ImportError as e:
    logger.error(f"Failed to import AutoHedge. Make sure the project structure is correct and all dependencies are installed. Error: {e}")
    sys.exit(1)

def run_test():
    """
    Runs an end-to-end test of the AutoHedge system with the Gemini migration.
    """
    logger.info("Starting Gemini migration end-to-end test...")

    # Check if the Google API key is set
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY is not set.")
        logger.error("Please edit the .env file and add your valid Google API key.")
        return
    
    # Configure genai with API key globally
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    logger.info("Listing available Gemini models:")
    available_models = [
        m.name
        for m in genai.list_models()
        if "generateContent" in m.supported_generation_methods
    ]
    if available_models:
        logger.info(f"Supported models for generateContent: {available_models}")
    else:
        logger.warning("No Gemini models supporting 'generateContent' found with this API key.")
        return

    # 1. Instantiate AutoHedge with a liquid stock
    try:
        auto_hedge_system = AutoHedge(stocks=["AAPL"])
        logger.info("AutoHedge system instantiated successfully for AAPL.")
    except Exception as e:
        logger.error(f"Failed to instantiate AutoHedge: {e}")
        return

    # 2. Define a simple analysis task
    task = "Provide a brief market analysis and decide if a trade is warranted."

    # 3. Run the main loop
    try:
        logger.info(f"Running task: '{task}'")
        result = auto_hedge_system.run(task)
        logger.info("AutoHedge run completed.")
    except Exception as e:
        logger.error(f"An error occurred during the AutoHedge run: {e}")
        return

    # 4. Print the output
    logger.info("--- Test Run Output ---")
    print(result)
    logger.info("--- End of Test Run Output ---")

    if result:
        logger.success("Test completed successfully. Output was generated.")
    else:
        logger.warning("Test completed, but the result was empty.")

if __name__ == "__main__":
    run_test()
