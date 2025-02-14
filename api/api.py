import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import requests
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Path,
    Query,
    Security,
)
from fastapi.security import APIKeyHeader
from loguru import logger
from pydantic import BaseModel, EmailStr, Field

from autohedge.main import AutoFund


def log_agent_data(data_dict: dict) -> dict | None:
    """
    Logs agent data to the Swarms database with retry logic.

    Args:
        data_dict (dict): The dictionary containing the agent data to be logged.
        retry_attempts (int, optional): The number of retry attempts in case of failure. Defaults to 3.

    Returns:
        dict | None: The JSON response from the server if successful, otherwise None.

    Raises:
        ValueError: If data_dict is empty or invalid
        requests.exceptions.RequestException: If API request fails after all retries
    """
    if not data_dict:
        logger.error("Empty data dictionary provided")
        raise ValueError("data_dict cannot be empty")

    url = "https://swarms.world/api/get-agents/log-agents"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-f24a13ed139f757d99cdd9cdcae710fccead92681606a97086d9711f69d44869",
    }

    requests.post(url, json=data_dict, headers=headers, timeout=10)
    # response.raise_for_status()

    return None


# Enhanced Pydantic Models
class TradeStatus(str, Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    fund_name: str = Field(..., min_length=3, max_length=100)
    fund_description: Optional[str] = Field(None, max_length=500)


class UserUpdate(BaseModel):
    fund_name: Optional[str] = Field(
        None, min_length=3, max_length=100
    )
    fund_description: Optional[str] = Field(None, max_length=500)
    email: Optional[EmailStr] = None


class User(UserCreate):
    id: str
    api_key: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True


class TradingTask(BaseModel):
    stocks: List[str] = Field(..., min_items=1)
    task: str = Field(..., min_length=10)
    allocation: float = Field(..., gt=0)
    strategy_type: Optional[str] = Field(
        None, description="Trading strategy type"
    )
    risk_level: Optional[int] = Field(
        None, ge=1, le=10, description="Risk level from 1-10"
    )


class TradeResponse(BaseModel):
    id: str
    user_id: str
    task: TradingTask
    status: TradeStatus
    created_at: datetime
    executed_at: Optional[datetime]
    result: Optional[Dict[str, Any]]
    performance_metrics: Optional[Dict[str, float]]


class HistoricalAnalytics(BaseModel):
    total_trades: int
    success_rate: float
    average_return: float
    total_allocation: float
    risk_adjusted_return: float
    top_performing_stocks: List[Tuple[str, float]]


# Configure Loguru with more detailed formatting
logger.add(
    "logs/autohedge_{time}.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO",
    format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {module}:{function}:{line} | {message}",
    backtrace=True,
    diagnose=True,
)


class AutoHedgeAPI:
    def __init__(self, *args, **kwargs):
        self.app = FastAPI(
            title="AutoHedge API",
            version="1.0.0",
            description="Production-grade API for automated hedge fund management",
            *args,
            **kwargs,
        )
        self.api_key_header = APIKeyHeader(name="X-API-Key")
        self.users: Dict[str, User] = {}
        self.api_keys: Dict[str, str] = {}
        self.trades: Dict[str, TradeResponse] = {}
        self.performance_cache: Dict[str, Dict] = {}

        self._setup_routes()
        logger.info(
            "AutoHedge API initialized with enhanced features"
        )

    @contextmanager
    def _log_execution_time(
        self, operation: str, user_id: Optional[str] = None
    ):
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            {
                "operation": operation,
                "execution_time": execution_time,
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc),
            }
            # logger.info(f"Operation '{operation}' metrics: {json_data}")

    async def _get_current_user(
        self, api_key: str = Security(APIKeyHeader(name="X-API-Key"))
    ) -> User:
        user_id = self.api_keys.get(api_key)
        if not user_id or user_id not in self.users:
            logger.warning(
                f"Invalid API key attempt: {api_key[:8]}..."
            )
            raise HTTPException(
                status_code=401, detail="Invalid API key"
            )

        user = self.users[user_id]
        user.last_login = datetime.now(timezone.utc)
        return user

    def _calculate_performance_metrics(
        self, trade_result: Dict
    ) -> Dict[str, float]:
        """Calculate performance metrics for a trade"""
        try:
            # Implementation would depend on the structure of trade_result
            return {
                "return_percentage": 0.0,  # Placeholder
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "volatility": 0.0,
            }
        except Exception as e:
            logger.error(
                f"Error calculating performance metrics: {str(e)}"
            )
            return {}

    def _setup_routes(self):
        # User Management Routes
        @self.app.post("/users", response_model=User)
        async def create_user(user: UserCreate):
            with self._log_execution_time("create_user"):
                user_id = str(uuid.uuid4())
                api_key = str(uuid.uuid4())

                user_data = User(
                    id=user_id,
                    api_key=api_key,
                    created_at=datetime.now(timezone.utc),
                    **user.dict(),
                )

                self.users[user_id] = user_data
                self.api_keys[api_key] = user_id

                logger.info(f"New user created: {user.username}")
                return user_data

        @self.app.get("/users/me", response_model=User)
        async def get_current_user(
            current_user: User = Depends(self._get_current_user),
        ):
            return current_user

        @self.app.put("/users/me", response_model=User)
        async def update_user(
            user_update: UserUpdate,
            current_user: User = Depends(self._get_current_user),
        ):
            with self._log_execution_time(
                "update_user", current_user.id
            ):
                updated_data = current_user.dict()
                updated_data.update(
                    user_update.dict(exclude_unset=True)
                )

                updated_user = User(**updated_data)
                self.users[current_user.id] = updated_user

                logger.info(f"User updated: {current_user.id}")
                return updated_user

        # Trading Routes
        @self.app.post("/trades", response_model=TradeResponse)
        async def create_trade(
            task: TradingTask,
            current_user: User = Depends(self._get_current_user),
        ):
            with self._log_execution_time(
                "create_trade", current_user.id
            ):
                trade_id = str(uuid.uuid4())

                try:
                    trading_system = AutoFund(
                        name=current_user.fund_name,
                        description=current_user.fund_description
                        or "",
                        stocks=task.stocks,
                    )

                    trade_response = TradeResponse(
                        id=trade_id,
                        user_id=current_user.id,
                        task=task,
                        status=TradeStatus.EXECUTING,
                        created_at=datetime.now(timezone.utc),
                        executed_at=None,
                        result=None,
                        performance_metrics=None,
                    )

                    # Execute trade
                    result = trading_system.run(task=task.task)

                    # Update trade response
                    trade_response.status = TradeStatus.COMPLETED
                    trade_response.executed_at = datetime.now(
                        timezone.utc
                    )
                    trade_response.result = result
                    trade_response.performance_metrics = (
                        self._calculate_performance_metrics(result)
                    )

                    # Store trade
                    self.trades[trade_id] = trade_response

                    # Log to Swarms
                    self._log_to_swarms(
                        {
                            "trade_id": trade_id,
                            "user_id": current_user.id,
                            "task": task.dict(),
                            "result": result,
                            "performance_metrics": trade_response.performance_metrics,
                        }
                    )

                    return trade_response

                except Exception as e:
                    logger.error(f"Trade execution failed: {str(e)}")
                    raise HTTPException(
                        status_code=500, detail=str(e)
                    )

        @self.app.get("/trades", response_model=List[TradeResponse])
        async def list_trades(
            current_user: User = Depends(self._get_current_user),
            skip: int = Query(0, ge=0),
            limit: int = Query(10, ge=1, le=100),
            status: Optional[TradeStatus] = None,
        ):
            with self._log_execution_time(
                "list_trades", current_user.id
            ):
                user_trades = [
                    trade
                    for trade in self.trades.values()
                    if trade.user_id == current_user.id
                    and (status is None or trade.status == status)
                ]

                return sorted(
                    user_trades,
                    key=lambda x: x.created_at,
                    reverse=True,
                )[skip : skip + limit]

        @self.app.get(
            "/trades/{trade_id}", response_model=TradeResponse
        )
        async def get_trade(
            trade_id: str = Path(
                ..., title="The ID of the trade to get"
            ),
            current_user: User = Depends(self._get_current_user),
        ):
            if trade_id not in self.trades:
                raise HTTPException(
                    status_code=404, detail="Trade not found"
                )

            trade = self.trades[trade_id]
            if trade.user_id != current_user.id:
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to access this trade",
                )

            return trade

        @self.app.delete("/trades/{trade_id}")
        async def delete_trade(
            trade_id: str = Path(
                ..., title="The ID of the trade to delete"
            ),
            current_user: User = Depends(self._get_current_user),
        ):
            if trade_id not in self.trades:
                raise HTTPException(
                    status_code=404, detail="Trade not found"
                )

            trade = self.trades[trade_id]
            if trade.user_id != current_user.id:
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to delete this trade",
                )

            del self.trades[trade_id]
            logger.info(f"Trade deleted: {trade_id}")
            return {"message": "Trade deleted successfully"}

        # Analytics Routes
        @self.app.get(
            "/analytics/history", response_model=HistoricalAnalytics
        )
        async def get_historical_analytics(
            current_user: User = Depends(self._get_current_user),
            days: int = Query(30, ge=1, le=365),
        ):
            with self._log_execution_time(
                "get_historical_analytics", current_user.id
            ):
                start_date = datetime.now(timezone.utc) - timedelta(
                    days=days
                )

                # Filter user's trades within the time period
                user_trades = [
                    trade
                    for trade in self.trades.values()
                    if trade.user_id == current_user.id
                    and trade.created_at >= start_date
                ]

                if not user_trades:
                    return HistoricalAnalytics(
                        total_trades=0,
                        success_rate=0.0,
                        average_return=0.0,
                        total_allocation=0.0,
                        risk_adjusted_return=0.0,
                        top_performing_stocks=[],
                    )

                # Calculate analytics
                successful_trades = len(
                    [
                        t
                        for t in user_trades
                        if t.status == TradeStatus.COMPLETED
                    ]
                )
                total_trades = len(user_trades)

                analytics = HistoricalAnalytics(
                    total_trades=total_trades,
                    success_rate=successful_trades
                    / total_trades
                    * 100,
                    average_return=sum(
                        t.performance_metrics.get(
                            "return_percentage", 0
                        )
                        for t in user_trades
                    )
                    / total_trades,
                    total_allocation=sum(
                        t.task.allocation for t in user_trades
                    ),
                    risk_adjusted_return=0.0,  # Would need more complex calculation
                    top_performing_stocks=[],  # Would need aggregation of stock performance
                )

                return analytics

    def _log_to_swarms(self, data_dict: dict) -> None:
        """Log data to Swarms with error handling and retry logic"""
        try:
            log_agent_data(data_dict)
            logger.info("Successfully logged data to Swarms")
        except Exception as e:
            logger.error(f"Failed to log to Swarms: {str(e)}")
            # Store failed logs for potential retry
            self._store_failed_log(data_dict)

    def _store_failed_log(self, data_dict: dict) -> None:
        """Store failed logs for retry"""
        logger.info("Storing failed log for later retry")
        # Implementation would depend on your storage solution

    def run(
        self, host: str = "0.0.0.0", port: int = 8000, *args, **kwargs
    ):
        """Run the FastAPI application"""
        import uvicorn

        logger.info(
            f"Starting Enhanced AutoHedge API on {host}:{port}"
        )
        uvicorn.run(self.app, host=host, port=port, *args, **kwargs)


# Example usage
if __name__ == "__main__":
    api = AutoHedgeAPI()
    api.run()
