import random
from locust import HttpUser, task, between

WALLET_UUID = "5a33a9ab-9080-4618-b122-5d4be176d9d1"

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
