from locust import HttpUser, task, between
from uuid import UUID
import random

WALLET_UUID = "af994f42-524e-4ecb-b52d-3b521185d157"

class WalletApiUser(HttpUser):
    wait_time = between(1, 3)

    @task(1)
    def get_wallet(self):
        """Тест запроса информации о кошельке"""
        self.client.get(f"/api/v1/wallets/{WALLET_UUID}")

    @task(2)
    def deposit(self):
        """Тест операции DEPOSIT"""
        self.client.post(
            f"/api/v1/wallets/{WALLET_UUID}/operation",
            json={"operationType": "DEPOSIT", "amount": random.randint(10, 500)},
            headers={"Content-Type": "application/json"},
        )
