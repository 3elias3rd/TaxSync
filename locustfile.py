from locust import HttpUser, task, between
import random


class TaxSyncUser(HttpUser):

    wait_time = between(1, 3)
    # Each user waits 1-3 seconds between tasks to attempt to simulate real usage
    def on_start(self):
        """Login and store token"""
        response = self.client.post(
            "/token",
            data={
                "username": "max",
                "password": "passmax"
            },
            name="POST /token"
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            self.headers = {}
            print(f"Login failed: {response.status_code} {response.text}")

    @task(3)
    def get_expenses(self):
        self.client.get(
            "/expenses/?page=1&page_size=20",
            headers=self.headers,
            name="GET /expenses/"
        )

    @task(2)
    def get_final_report(self):
        self.client.get(
            "/final_report?year=2026",
            headers=self.headers,
            name="GET /final_report"
        )

    @task(1)
    def create_expense(self):
        self.client.post(
            "/expenses/",
            headers=self.headers,
            json={
                "description": f"Load test expense {random.randint(1, 1000)}",
                "amount":      round(random.uniform(100, 5000), 2),
                "category_id": 1
            },
            name="POST /expenses/"
        )