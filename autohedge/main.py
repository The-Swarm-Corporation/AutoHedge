import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger
from pydantic import BaseModel
from swarms import Agent, create_file_in_folder
from tickr_agent.main import TickrAgent

# Director Agent - Manages overall strategy and coordinates other agents
DIRECTOR_PROMPT = """
You are a Trading Director AI, responsible for orchestrating the trading process. 

Your primary objectives are:
1. Conduct in-depth market analysis to identify opportunities and challenges.
2. Develop comprehensive trading theses, encompassing both technical and fundamental aspects.
3. Collaborate with specialized agents to ensure a cohesive strategy.
4. Make informed, data-driven decisions on trade executions.

For each stock under consideration, please provide the following:

- A concise market thesis, outlining the overall market position and expected trends.
- Key technical and fundamental factors influencing the stock's performance.
- A detailed risk assessment, highlighting potential pitfalls and mitigation strategies.
- Trade parameters, including entry and exit points, position sizing, and risk management guidelines.
"""


# Quant Analysis Agent
QUANT_PROMPT = """
You are a Quantitative Analysis AI, tasked with providing in-depth numerical analysis to support trading decisions. Your primary objectives are:

1. **Technical Indicator Analysis**: Evaluate various technical indicators such as moving averages, relative strength index (RSI), and Bollinger Bands to identify trends, patterns, and potential reversals.
2. **Statistical Pattern Evaluation**: Apply statistical methods to identify patterns in historical data, including mean reversion, momentum, and volatility analysis.
3. **Risk Metric Calculation**: Calculate risk metrics such as Value-at-Risk (VaR), Expected Shortfall (ES), and Greeks to quantify potential losses and position sensitivity.
4. **Trade Success Probability**: Provide probability scores for trade success based on historical data analysis, technical indicators, and risk metrics.

To accomplish these tasks, you will receive a trading thesis from the Director Agent, outlining the stock under consideration, market position, expected trends, and key factors influencing the stock's performance. Your analysis should build upon this thesis, providing detailed numerical insights to support or challenge the Director's hypothesis.

In your analysis, include confidence scores for each aspect of your evaluation, indicating the level of certainty in your findings. This will enable the Director to make informed decisions, weighing the potential benefits against the risks associated with each trade.

Your comprehensive analysis will be instrumental in refining the trading strategy, ensuring that it is grounded in empirical evidence and statistical rigor. By working together with the Director Agent, you will contribute to a cohesive and data-driven approach to trading, ultimately enhancing the overall performance of the trading system.
"""


class AutoHedgeOutput(BaseModel):
    id: str = uuid.uuid4().hex
    thesis: Optional[str] = None
    risk_assessment: Optional[str] = None
    order: Optional[str] = None
    decision: str = None
    timestamp: str = datetime.now().isoformat()
    current_stock: str


class AutoHedgeOutputMain(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    id: str = uuid.uuid4().hex
    stocks: Optional[list] = None
    task: Optional[str] = None
    timestamp: str = datetime.now().isoformat()
    logs: List[AutoHedgeOutput] = None


# Risk Assessment Agent
RISK_PROMPT = """You are a Risk Assessment AI. Your primary objective is to evaluate and mitigate potential risks associated with a given trade. 

Your responsibilities include:

1. Evaluating position sizing to determine the optimal amount of capital to allocate to a trade.
2. Calculating potential drawdown to anticipate and prepare for potential losses.
3. Assessing market risk factors, such as volatility, liquidity, and market sentiment.
4. Monitoring correlation risks to identify potential relationships between different assets.

To accomplish these tasks, you will be provided with a comprehensive thesis and analysis from the Quantitative Analysis Agent. 

The thesis will include:
- A clear direction (long or short) for the trade
- A confidence level indicating the strength of the trade signal
- An entry price and stop loss level to define the trade's parameters
- A take profit level to determine the trade's potential upside
- A timeframe for the trade, indicating the expected duration
- Key factors influencing the trade, such as technical indicators or fundamental metrics
- Potential risks associated with the trade, such as market volatility or economic uncertainty

The analysis will include:
- Technical scores indicating the strength of the trade signal based on technical indicators
- Volume scores indicating the level of market participation and conviction
- Trend strength scores indicating the direction and magnitude of the market trend
- Key levels, such as support and resistance, to identify potential areas of interest

Using this information, please provide clear risk metrics and trade size recommendations, including:
- A recommended position size based on the trade's potential risk and reward
- A maximum drawdown risk to anticipate and prepare for potential losses
- A market risk exposure assessment to identify potential risks and opportunities
- An overall risk score to summarize the trade's potential risks and rewards

Your output should be in a structured format, including all relevant metrics and recommendations.
"""


class RiskManager:
    def __init__(self):
        self.risk_agent = Agent(
            agent_name="Risk-Manager",
            system_prompt=RISK_PROMPT,
            model_name="groq/deepseek-r1-distill-llama-70b",
            output_type="str",
            max_loops=1,
            verbose=True,
            context_length=16000,
        )

    def assess_risk(
        self, stock: str, thesis: str, quant_analysis: str
    ) -> str:
        prompt = f"""
        Stock: {stock}
        Thesis: {thesis}
        Quant Analysis: {quant_analysis}
        
        Provide risk assessment including:
        1. Recommended position size
        2. Maximum drawdown risk
        3. Market risk exposure
        4. Overall risk score
        """
        assessment = self.risk_agent.run(prompt)

        return assessment


# Execution Agent
EXECUTION_PROMPT = """You are a Trade Execution AI. Your primary objective is to execute trades with precision and accuracy. Your key responsibilities include:

1. **Generating structured order parameters**: Define the essential details of the trade, including the stock symbol, quantity, and price.
2. **Setting precise entry/exit levels**: Determine the exact points at which to enter and exit the trade, ensuring optimal profit potential and risk management.
3. **Determining order types**: Choose the most suitable order type for the trade, such as market order, limit order, or stop-loss order, based on market conditions and trade strategy.
4. **Specifying time constraints**: Define the timeframe for the trade, including the start and end dates, to ensure timely execution and minimize exposure to market volatility.

To execute trades effectively, provide exact trade execution details in a structured format, including:

* Stock symbol and quantity
* Entry and exit prices
* Order type (market, limit, stop-loss, etc.)
* Time constraints (start and end dates, time in force)
* Any additional instructions or special requirements

By following these guidelines, you will ensure that trades are executed efficiently, minimizing potential losses and maximizing profit opportunities.
"""


class ExecutionAgent:
    def __init__(self):
        self.execution_agent = Agent(
            agent_name="Execution-Agent",
            system_prompt=EXECUTION_PROMPT,
            model_name="groq/deepseek-r1-distill-llama-70b",
            output_type="str",
            max_loops=1,
            verbose=True,
            context_length=16000,
        )

    def generate_order(
        self, stock: str, thesis: Dict, risk_assessment: Dict
    ) -> str:
        prompt = f"""
        Stock: {stock}
        Thesis: {thesis}
        Risk Assessment: {risk_assessment}
        
        Generate trade order including:
        1. Order type (market/limit)
        2. Quantity
        3. Entry price
        4. Stop loss
        5. Take profit
        6. Time in force
        """
        order = self.execution_agent.run(prompt)
        return order


class TradingDirector:
    """
    Trading Director Agent responsible for generating trading theses and coordinating strategy.

    Attributes:
        director_agent (Agent): Swarms agent for thesis generation
        tickr (TickrAgent): Agent for market data collection
        output_dir (Path): Directory for storing outputs

    Methods:
        generate_thesis: Generates trading thesis for a given stock
        save_output: Saves thesis to JSON file
    """

    def __init__(
        self,
        stocks: List[str],
        output_dir: str = "outputs",
        cryptos: List[str] = None,
    ):

        logger.info("Initializing Trading Director")
        self.director_agent = Agent(
            agent_name="Trading-Director",
            system_prompt=DIRECTOR_PROMPT,
            model_name="groq/deepseek-r1-distill-llama-70b",
            output_type="str",
            max_loops=1,
            verbose=True,
            context_length=16000,
        )

        # self.crypto_agent = CryptoAgentWrapper()

    def generate_thesis(
        self,
        task: str = "Generate a thesis for the stock",
        stock: str = None,
        crypto: str = None,
    ) -> str:
        """
        Generate trading thesis for a given stock.

        Args:
            stock (str): Stock ticker symbol

        Returns:
            TradingThesis: Generated thesis
        """
        logger.info(f"Generating thesis for {stock}")

        self.tickr = TickrAgent(
            stocks=[stock],
            max_loops=1,
            workers=10,
            retry_attempts=1,
            context_length=16000,
        )

        try:
            market_data = self.tickr.run(
                f"{task} Analyze current market conditions and key metrics for {stock}"
            )

            prompt = f"""
            Task: {task}
            \n
            Stock: {stock}
            Market Data: {market_data}
            """

            thesis = self.director_agent.run(prompt)
            return thesis, market_data

        except Exception as e:
            logger.error(
                f"Error generating thesis for {stock}: {str(e)}"
            )
            raise

    def make_decision(self, task: str, thesis: str, *args, **kwargs):
        return self.director_agent.run(
            f"According to the thesis, {thesis}, should we execute this order: {task}"
        )

    def generate_thesis_crypto(
        self,
        task: str = None,
        crypto: str = None,
    ):
        logger.info(f"Generating thesis for {crypto}")
        try:
            market_data = self.crypto_agent.run(
                crypto,
                f"{task} Analyze current market conditions and key metrics for {crypto}",
            )

            prompt = f"""
            Task: {task}
            \n
            Stock: {crypto}
            Market Data: {market_data}
            """

            thesis = self.director_agent.run(prompt)
            return thesis

        except Exception as e:
            logger.error(
                f"Error generating thesis for {crypto}: {str(e)}"
            )
            raise


class QuantAnalyst:
    """
    Quantitative Analysis Agent responsible for technical and statistical analysis.

    Attributes:
        quant_agent (Agent): Swarms agent for analysis
        output_dir (Path): Directory for storing outputs
    """

    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        logger.info("Initializing Quant Analyst")
        self.quant_agent = Agent(
            agent_name="Quant-Analyst",
            system_prompt=QUANT_PROMPT,
            model_name="groq/deepseek-r1-distill-llama-70b",
            output_type="str",
            max_loops=1,
            verbose=True,
            context_length=16000,
        )

    def analyze(self, stock: str, thesis: str) -> str:
        """
        Perform quantitative analysis for a stock.

        Args:
            stock (str): Stock ticker symbol
            thesis (TradingThesis): Trading thesis

        Returns:
            QuantAnalysis: Quantitative analysis results
        """
        logger.info(f"Performing quant analysis for {stock}")
        try:
            prompt = f"""
            Stock: {stock}
            Thesis from your Director: {thesis}
            
            Generate quantitative analysis for the {stock}
            
            "ticker": str,
            "technical_score": float (0-1),
            "volume_score": float (0-1),
            "trend_strength": float (0-1),
            "volatility": float,
            "probability_score": float (0-1),
            "key_levels": {{
                "support": float,
                "resistance": float,
                "pivot": float
            }}
            """

            analysis = self.quant_agent.run(prompt)
            return analysis

        except Exception as e:
            logger.error(
                f"Error in quant analysis for {stock}: {str(e)}"
            )
            raise


class AutoFund:
    """
    Main trading system that coordinates all agents and manages the trading cycle.

    Attributes:
        stocks (List[str]): List of stock tickers to trade
        director (TradingDirector): Trading director agent
        quant (QuantAnalyst): Quantitative analysis agent
        risk (RiskManager): Risk management agent
        execution (ExecutionAgent): Trade execution agent
        output_dir (Path): Directory for storing outputs
    """

    def __init__(
        self,
        stocks: List[str],
        name: str = "autohedge",
        description: str = "fully autonomous hedgefund",
        output_dir: str = "outputs",
        output_file_path: str = None,
    ):
        """
        Initialize the AutoFund class.

        Args:
            stocks (List[str]): List of stock tickers to trade
            name (str, optional): Name of the trading system. Defaults to "autohedge".
            description (str, optional): Description of the trading system. Defaults to "fully autonomous hedgefund".
            output_dir (str, optional): Directory for storing outputs. Defaults to "outputs".
            output_file_path (str, optional): Path to the output file. Defaults to None.
        """
        self.name = name
        self.description = description
        self.stocks = stocks
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        logger.info("Initializing Automated Trading System")
        self.director = TradingDirector(stocks, output_dir)
        self.quant = QuantAnalyst()
        self.risk = RiskManager()
        self.execution = ExecutionAgent()
        self.logs = AutoHedgeOutputMain(
            name=self.name,
            description=self.description,
            stocks=stocks,
            task="",
            logs=[],
        )

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
        logger.info("Starting trading cycle")

        try:
            for stock in self.stocks:
                logger.info(f"Processing {stock}")

                # Generate thesis
                thesis, market_data = self.director.generate_thesis(
                    task=task, stock=stock
                )

                # Perform analysis
                analysis = self.quant.analyze(
                    stock + market_data, thesis
                )

                # Assess risk
                risk_assessment = self.risk.assess_risk(
                    stock + market_data, thesis, analysis
                )

                # # Generate order if approved
                order = self.execution.generate_order(
                    stock, thesis, risk_assessment
                )

                order = str(order)

                # Final decision
                decision = self.director.make_decision(
                    order + market_data + risk_assessment, thesis
                )

                log = AutoHedgeOutput(
                    thesis=thesis,
                    risk_assessment=risk_assessment,
                    current_stock=stock,
                    order=order,
                    decision=decision,
                )

                # logs.append(log.model_dump_json(indent=4))
                self.logs.task = task
                self.logs.logs.append(log)

            create_file_in_folder(
                self.output_dir,
                f"analysis-{uuid.uuid4().hex}.json",
                self.logs.model_dump_json(indent=4),
            )

            return self.logs.model_dump_json(indent=4)

        except Exception as e:
            logger.error(f"Error in trading cycle: {str(e)}")
            raise
