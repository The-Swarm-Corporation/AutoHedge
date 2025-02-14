import requests
import json
import time
from typing import Dict, Any
import os


class AutoHedgeAPI:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_key = None
        self.headers = {"Content-Type": "application/json"}
        print("🚀 Initializing AutoHedge API...")

    def create_user(self) -> str:
        """Create a new user and get API key"""
        print("\n🔑 Creating new user to get API key...")

        user_data = {
            "username": f"trader_{int(time.time())}",  # Unique username
            "email": f"trader_{int(time.time())}@example.com",
            "fund_name": "Test Trading Fund",
            "fund_description": "Automated test trading strategy",
        }

        try:
            response = requests.post(
                f"{self.base_url}/users",
                headers=self.headers,
                json=user_data,
            )
            response.raise_for_status()
            result = response.json()

            self.api_key = result["api_key"]
            self.headers["X-API-Key"] = self.api_key

            print("✅ Successfully created user and got API key")
            print(f"📝 API Key: {self.api_key}")

            # Save key to file for future use
            with open("api_key.txt", "w") as f:
                f.write(self.api_key)
            print("💾 API key saved to api_key.txt")

            return self.api_key

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to create user: {str(e)}")
            if hasattr(e.response, "json"):
                print(f"Error details: {e.response.json()}")
            raise

    def load_or_create_key(self) -> str:
        """Load existing API key or create new one"""
        try:
            # Try to load existing key
            if os.path.exists("api_key.txt"):
                with open("api_key.txt", "r") as f:
                    self.api_key = f.read().strip()
                    self.headers["X-API-Key"] = self.api_key
                print("📤 Loaded existing API key")
                return self.api_key
        except Exception as e:
            print(f"⚠️ Error loading API key: {str(e)}")

        # Create new key if loading failed
        return self.create_user()

    def _make_request(
        self, method: str, endpoint: str, data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Helper method to make HTTP requests"""
        url = f"{self.base_url}{endpoint}"

        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(
                    url, headers=self.headers, json=data
                )
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers)

            response.raise_for_status()
            return response.json() if response.text else {}

        except requests.exceptions.RequestException as e:
            print(f"❌ Error making request: {str(e)}")
            if hasattr(e.response, "json"):
                print(f"Error details: {e.response.json()}")
            raise

    def test_get_user_profile(self):
        """Test getting user profile"""
        print("\n📋 Testing Get User Profile...")
        try:
            result = self._make_request("GET", "/users/me")
            print("✅ Successfully retrieved user profile:")
            print(json.dumps(result, indent=2))
            return result
        except Exception as e:
            print(f"❌ Failed to get user profile: {str(e)}")

    def test_create_trade(self):
        """Test creating a new trade"""
        print("\n💹 Testing Create Trade...")
        trade_data = {
            "stocks": ["NVDA", "AAPL", "GOOGL"],
            "task": "Analyze tech companies for a $1M allocation with focus on AI capabilities",
            "allocation": 1000000.0,
            "strategy_type": "momentum",
            "risk_level": 7,
        }

        try:
            result = self._make_request("POST", "/trades", trade_data)
            print("✅ Successfully created trade:")
            print(json.dumps(result, indent=2))
            return result
        except Exception as e:
            print(f"❌ Failed to create trade: {str(e)}")

    def test_list_trades(self, limit: int = 5):
        """Test listing trades"""
        print(f"\n📊 Testing List Trades (limit: {limit})...")
        try:
            result = self._make_request(
                "GET", f"/trades?limit={limit}"
            )
            print("✅ Successfully retrieved trades:")
            print(json.dumps(result, indent=2))
            return result
        except Exception as e:
            print(f"❌ Failed to list trades: {str(e)}")

    def test_get_analytics(self):
        """Test getting historical analytics"""
        print("\n📈 Testing Get Historical Analytics...")
        try:
            result = self._make_request(
                "GET", "/analytics/history?days=30"
            )
            print("✅ Successfully retrieved analytics:")
            print(json.dumps(result, indent=2))
            return result
        except Exception as e:
            print(f"❌ Failed to get analytics: {str(e)}")

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n🔍 Running complete test suite...")

        tests = [
            self.test_get_user_profile,
            self.test_create_trade,
            self.test_list_trades,
            self.test_get_analytics,
        ]

        results = {}
        for test in tests:
            try:
                results[test.__name__] = test()
                time.sleep(1)  # Small delay between tests
            except Exception as e:
                results[test.__name__] = f"Failed: {str(e)}"

        print("\n✨ All tests completed!")
        return results


def main():
    # Initialize API client
    api = AutoHedgeAPI()

    # Get or create API key
    api.load_or_create_key()

    # Run all tests
    api.run_all_tests()


if __name__ == "__main__":
    main()
