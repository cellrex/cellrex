#!/usr/bin/env python3
import random
import time

import gevent
from locust import HttpUser, task
from locust.env import Environment
from locust.log import setup_logging
from locust.stats import stats_history, stats_printer

setup_logging("INFO")


class BiofilesUser(HttpUser):
    host = "http://localhost:8000/v1"

    @task(2)
    def query_all_files(self, params={"limit": 1000, "offset": 0}):
        """Test the /biofiles/all endpoint"""
        _ = self.client.get("/biofiles/all", timeout=15, params=params)

    @task(3)
    def query_file_by_id(self):
        """Test the /biofiles/id/{file_id} endpoint"""
        # use random file IDs between 1-100 for testing
        file_id = random.randint(1, 100)
        _ = self.client.get(
            f"/biofiles/id/{file_id}", name="/biofiles/id/[id]", timeout=15
        )

    @task(1)
    def query_file_by_search(self, params={"limit": 1000, "offset": 0}):
        """Test the /biofiles/search endpoint"""
        search_query = {
            "species": ["Human"],
            "origin": ["iPSC"],
            "pharmacology": ["Bicuculline"],
        }
        _ = self.client.post(
            "/biofiles/search", json=search_query, timeout=15, params=params
        )


def main():
    # setup environment and runner
    env = Environment(user_classes=[BiofilesUser])
    runner = env.create_local_runner()

    # start WebUI for monitoring
    web_ui = env.create_web_ui("127.0.0.1", 8089)

    # execute init event handlers
    env.events.init.fire(environment=env, runner=runner, web_ui=web_ui)

    print("Starting performance test in 15 seconds...")
    time.sleep(15)

    # start stats printing and history tracking
    gevent.spawn(stats_printer(env.stats))
    gevent.spawn(stats_history, env.runner)

    # start the test with 10 users, spawn rate of 2 users per second

    runner.start(25, spawn_rate=2)

    # run test for 60 seconds
    gevent.spawn_later(60, runner.quit)

    # wait for completion
    runner.greenlet.join()

    while 1:
        pass

    # cleanup
    web_ui.stop()
    print("Performance test completed!")


if __name__ == "__main__":
    main()
