from locust import HttpUser, task, between
import random


class TaxSync(HttpUser):
    # Each user waits 1-3 seconds between tasks to attempt to simulate real usage
    wait_time = between(1, 3)

    def on_start(self):
        """Called when a simulated user starts - logs in and stores token"""
        # Retry logic for rate limiting logins
        for attempt in range(3):
            
            response = self.client.post("/token", data={
                "username": "demo_employee",
                "password": "TaxSync2026!"
            })
            if response.status_code == 200:
                token = response.json()["access_token"]
                self.headers = {"Authorization": f"Bearer{token}"}
                return
        self.headers = {}

    # Weight of 3 = called 3x more that other tasks
    @task(3)
    def get_expense(self):
        self.client.get(
            "/expenses/?page=1&page_size=20",
            header=self.headers,
            name="Get /expenses" # To group results in Locust UI
        )

    # Weight of 2
    @task(2)
    def get_final_report(self):
        self.client.get(
            "/final_report?year=2026",
            headers=self.headers,
            name="GET /final_report"
        )

    # Weight of 1
    @task(1)
    def create_expense(self):
        self.client.post(
            "/expenses/",
            headers=self.headers,
            json={
                "description": f"Load test expense {random.randint(1, 1000)}",
                "amount":      random.uniform(100, 5000),
                "category_id": 1
            },
            name="Post /expenses/"
        )