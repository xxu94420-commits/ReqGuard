"""Read-only detail workload on disposable local Java API; no LLM supplier traffic."""

import os
from urllib.parse import urlsplit

from locust import HttpUser, between, task


class RequirementReader(HttpUser):
    wait_time = between(0.1, 0.3)

    def on_start(self):
        url = urlsplit(self.host)
        if url.scheme != "http" or url.hostname not in {
            "localhost",
            "127.0.0.1",
            "::1",
        }:
            raise ValueError("Use only a disposable local instance")
        self.requirement_id = os.environ.get("QA_REQUIREMENT_ID")
        if not self.requirement_id:
            raise ValueError("Set QA_REQUIREMENT_ID to a seeded local requirement")

    @task
    def read_detail(self):
        with self.client.get(
            f"/api/requirements/{self.requirement_id}",
            name="GET requirement detail",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"HTTP {response.status_code}")
            else:
                try:
                    body = response.json()
                    if (
                        body["requirement"]["id"] != self.requirement_id
                        or not body["versions"]
                    ):
                        response.failure("Unexpected requirement or missing history")
                except (ValueError, KeyError, TypeError):
                    response.failure("Invalid response contract")
