from typing import Any

import requests


class DecisionForgeAPIError(RuntimeError):
    pass


class DecisionForgeAPI:
    def __init__(
        self,
        base_url: str,
        generation_api_key: str,
    ):
        self.base_url = base_url.rstrip("/")
        self.generation_api_key = generation_api_key
        self.session = requests.Session()

    def _request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> dict[str, Any]:
        try:
            response = self.session.request(
                method=method,
                url=f"{self.base_url}{path}",
                timeout=30,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise DecisionForgeAPIError(
                "Could not connect to the DecisionForge backend."
            ) from exc

        if not response.ok:
            try:
                detail = response.json().get(
                    "detail",
                    response.text,
                )
            except ValueError:
                detail = response.text

            raise DecisionForgeAPIError(
                f"Backend error {response.status_code}: {detail}"
            )

        return response.json()

    def generate_simulation(
        self,
        scenario: str,
        role: str,
        difficulty: str,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/simulations/generate",
            headers={
                "X-Generation-Key": self.generation_api_key,
            },
            json={
                "scenario": scenario,
                "role": role,
                "difficulty": difficulty,
            },
        )

    def get_job(self, job_id: str) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/jobs/{job_id}",
        )

    def start_attempt(
        self,
        simulation_id: int,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/simulations/{simulation_id}/attempts",
        )

    def submit_decision(
        self,
        attempt_id: str,
        option_id: int,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/attempts/{attempt_id}/decisions",
            json={"option_id": option_id},
        )

    def get_result(
        self,
        attempt_id: str,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/attempts/{attempt_id}/result",
        )
