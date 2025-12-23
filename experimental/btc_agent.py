import os
from loguru import logger
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from swarms import Agent
from typing import Dict, Any
import websocket
import json
from datetime import datetime
import threading
import signal
import sys

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
]

# Use Google Gemini for analysis
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=GenerationConfig(temperature=0.1),
    safety_settings=safety_settings,
)


BTC_AGENT_SYSTEM_PROMPT = """You are a specialized Bitcoin transaction analysis agent.
Your role is to analyze new Bitcoin transactions in real-time and provide insights about:
1. Transaction significance and context
2. Pattern analysis and behavioral indicators
3. Risk assessment and unusual characteristics
4. Network flow and relationship analysis
5. Economic implications and market impact

For each transaction, evaluate:
- Transaction value and its market significance
- Historical context of the addresses involved
- Unusual patterns or behaviors
- Network flow implications
- Risk indicators and notable characteristics

Provide actionable insights in a clear, structured format."""


class BTCTransactionMonitor:
    def __init__(self):
        """Initialize the BTC transaction monitor with swarms Agent"""
        self.agent = Agent(
            agent_name="BTC-Analysis-Agent",
            system_prompt=BTC_AGENT_SYSTEM_PROMPT,
            agent_description="Real-time Bitcoin transaction analysis agent",
            llm=model,
            max_loops="auto",
            autosave=True,
            verbose=True,
            streaming_on=True,
            dynamic_temperature_enabled=True,
            saved_state_path="btc_agent_state.json",
            retry_attempts=3,
        )

        self.running = False
        self.ws = None
        self.monitored_address = None

    def analyze_transaction(self, tx_data: Dict[str, Any]) -> str:
        """
        Use the swarms agent to analyze a transaction

        Args:
            tx_data: Transaction data to analyze

        Returns:
            Analysis results as a string
        """
        # Calculate the transaction value in BTC
        value_btc = (
            sum(out.get("value", 0) for out in tx_data.get("out", []))
            / 100000000.0
        )

        # Format transaction data for analysis
        analysis_prompt = f"""
        New Bitcoin transaction detected:
        Transaction Hash: {tx_data.get('hash', 'Unknown')}
        Time: {datetime.fromtimestamp(tx_data.get('time', 0))}
        Value: {value_btc} BTC
        Inputs: {len(tx_data.get('inputs', []))}
        Outputs: {len(tx_data.get('out', []))}
        
        Please analyze this transaction focusing on:
        1. Transaction significance
        2. Pattern recognition
        3. Risk indicators
        4. Network flow implications
        5. Notable characteristics
        """

        return self.agent.run(analysis_prompt)

    def _on_message(self, ws, message):
        """Handle incoming websocket messages"""
        try:
            data = json.loads(message)

            # Check if this is a transaction message
            if data.get("op") == "utx" or data.get("op") == "tx":
                tx_data = data.get("x", {})

                # Check if transaction involves our monitored address
                addresses = []
                # Check outputs
                for out in tx_data.get("out", []):
                    addresses.append(out.get("addr", ""))
                # Check inputs
                for inp in tx_data.get("inputs", []):
                    prev_out = inp.get("prev_out", {})
                    addresses.append(prev_out.get("addr", ""))

                if self.monitored_address in addresses:
                    logger.info(
                        f"New transaction detected: {tx_data.get('hash', 'Unknown')}"
                    )

                    # Analyze the transaction
                    analysis = self.analyze_transaction(tx_data)

                    # Log and store the analysis
                    logger.info(
                        f"\nTransaction Analysis:\n{analysis}"
                    )
                    self._store_analysis(
                        tx_data.get("hash", "unknown"),
                        {
                            "transaction": tx_data,
                            "analysis": analysis,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )

        except json.JSONDecodeError:
            logger.error("Failed to decode websocket message")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")

    def _on_error(self, ws, error):
        """Handle websocket errors"""
        logger.error(f"WebSocket error: {str(error)}")

    def _on_close(self, ws, close_status_code, close_msg):
        """Handle websocket connection closing"""
        logger.info("WebSocket connection closed")
        if self.running:
            logger.info("Attempting to reconnect...")
            self._connect_websocket()

    def _on_open(self, ws):
        """Handle websocket connection opening"""
        logger.info("WebSocket connection established")
        # Subscribe to address
        subscription = {
            "op": "addr_sub",
            "addr": self.monitored_address,
        }
        ws.send(json.dumps(subscription))

    def _connect_websocket(self):
        """Establish WebSocket connection"""
        self.ws = websocket.WebSocketApp(
            "wss://ws.blockchain.info/inv",
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open,
        )

    def _store_analysis(self, tx_hash: str, analysis: Dict[str, Any]):
        """
        Store transaction analysis results

        Args:
            tx_hash: Transaction hash
            analysis: Analysis results to store
        """
        try:
            filename = f"analysis_{tx_hash}.json"
            with open(filename, "w") as f:
                json.dump(analysis, f, indent=2)
            logger.info(f"Stored analysis results in {filename}")
        except Exception as e:
            logger.error(f"Error storing analysis: {str(e)}")

    def monitor_address(self, address: str):
        """
        Start monitoring a Bitcoin address

        Args:
            address: Bitcoin address to monitor
        """
        self.monitored_address = address
        self.running = True

        logger.info(
            f"Starting real-time monitoring for address: {address}"
        )

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        # Connect and run WebSocket in a separate thread
        self._connect_websocket()
        ws_thread = threading.Thread(target=self.ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        # Keep main thread alive
        while self.running:
            signal.pause()

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Shutting down...")
        self.stop()
        sys.exit(0)

    def stop(self):
        """Stop the monitoring process"""
        self.running = False
        if self.ws:
            self.ws.close()
        logger.info("Monitoring stopped")


def main():
    # Example usage
    btc_monitor = BTCTransactionMonitor()

    # Replace with the Bitcoin address you want to monitor
    address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"

    try:
        btc_monitor.monitor_address(address)
    except KeyboardInterrupt:
        btc_monitor.stop()
        logger.info("Monitoring stopped by user")


if __name__ == "__main__":
    main()
