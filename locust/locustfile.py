import random
from locust import HttpUser, task, between

WALLET_ID = "de9f7c2e-4ff1-4bef-8ef6-0f0e68107215"  # ID существующего кошелька

class WalletApiUser(HttpUser):
    wait_time = between(1, 3)  # Задержка между запросами (для реального сценария)

    @task(1)
    def get_wallet(self):
        """Тест запроса информации о кошельке"""
        self.client.get(f"/wallets/{WALLET_ID}")

    @task(2)
    def create_transaction(self):
        """Тест создания транзакции"""
        self.client.post(
            "/transactions",
            json={"wallet_id": WALLET_ID, "amount": random.randint(10, 500), "type": "deposit"},
            headers={"Content-Type": "application/json"}
        )
