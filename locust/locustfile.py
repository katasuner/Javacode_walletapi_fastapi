import random
from locust import HttpUser, task, between

WALLET_UUID = "6050391b-5c04-4ae4-b54d-8af1ba4913c0"

class WalletApiUser(HttpUser):
    wait_time = between(1, 3)

    @task(1)
    def get_wallet(self):
        """Тест запроса информации об одном кошельке"""
        self.client.get(f"/api/v1/wallets/{WALLET_UUID}")

    @task(2)
    def deposit(self):
        """Тест операции DEPOSIT для одного кошелька"""
        self.client.post(
            f"/api/v1/wallets/{WALLET_UUID}/operation",
            json={"operationType": "DEPOSIT", "amount": random.randint(10, 500)},
            headers={"Content-Type": "application/json"},
        )
