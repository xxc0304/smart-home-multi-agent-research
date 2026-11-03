"""Stateless DeepSeek Responses transport. No tools, hidden history or evaluator access."""
from __future__ import annotations

import json
import http.client
import os
import socket
import time
import urllib.error
import urllib.request
from typing import Callable

from .schemas import ProtocolError


class DeepSeekClient:
    def __init__(self, config: dict, log: Callable, transport=None, token_counter=None):
        self.config, self.log = config, log
        self.transport = transport or self._http
        self.token_counter = token_counter
        self.count_mode = "local_tokenizer_estimate" if token_counter else "conservative_utf8_bytes"
        self.attempts = 0

    def payload(self, instructions, schema, max_output):
        settings = self.config["generation"]
        return {"model": self.config["model"], "instructions": instructions,
                "input": "Return the stage output as the specified JSON object.",
                "reasoning": {"effort": settings["reasoning_effort"]},
                "temperature": settings["temperature"], "max_output_tokens": max_output,
                "text": {"format": {"type": "json_schema", "name": "coreta_stage", "schema": schema}}}

    def size(self, payload):
        serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        return self.token_counter(serialized) + 256 if self.token_counter else len(serialized.encode("utf-8")) + 256

    def _http(self, payload, timeout):
        key = os.environ.get("DEEPSEEK_API_KEY")
        if not key:
            raise ProtocolError("MODEL_UNAVAILABLE", "DEEPSEEK_API_KEY is not configured")
        req = urllib.request.Request(self.config["base_url"].rstrip("/") + "/responses",
                                     data=json.dumps(payload).encode("utf-8"),
                                     headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
                                     method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def complete(self, payload, *, deadline, logical_seed):
        if self.size(payload) > self.config["generation"]["max_input_tokens"]:
            raise ProtocolError("CONTEXT_OVERFLOW", "Stage input exceeds configured conservative/tokenizer budget")
        for retry in range(self.config["protocol"]["transport_retries_per_request"] + 1):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ProtocolError("MODEL_TIMEOUT", "Task deadline exhausted")
            timeout = min(remaining, self.config["protocol"]["request_timeout_seconds"])
            start = time.monotonic()
            self.attempts += 1
            # Headers and credentials are intentionally absent from trace.
            self.log("requests.jsonl", {"attempt": self.attempts, "retry": retry,
                                       "logical_seed": logical_seed, "seed_sent": False,
                                       "input_count_mode": self.count_mode, "estimated_input_count": self.size(payload),
                                       "payload": payload})
            try:
                response = self.transport(payload, timeout)
            except (urllib.error.URLError, TimeoutError, socket.timeout, http.client.HTTPException, json.JSONDecodeError) as exc:
                code = exc.code if isinstance(exc, urllib.error.HTTPError) else None
                retryable = code is None or code == 429 or code >= 500
                self.log("responses.jsonl", {"attempt": self.attempts, "status": "transport_error",
                                            "http_status": code, "error_type": type(exc).__name__,
                                            "uncertain_usage": True, "latency_seconds": time.monotonic() - start})
                if retryable and retry < self.config["protocol"]["transport_retries_per_request"]:
                    continue
                raise ProtocolError("MODEL_TIMEOUT" if isinstance(exc, (TimeoutError, socket.timeout)) else "MODEL_UNAVAILABLE",
                                    f"DeepSeek transport failed ({type(exc).__name__}, HTTP {code})") from exc
            self.log("responses.jsonl", {"attempt": self.attempts, "response": response,
                                        "latency_seconds": time.monotonic() - start, "uncertain_usage": False})
            if response.get("status") not in {None, "completed"}:
                raise ProtocolError("SCHEMA_ERROR", "Response incomplete or failed; raw response retained")
            chunks = [part["text"] for item in response.get("output", []) if item.get("type") == "message"
                      for part in item.get("content", []) if part.get("type") == "output_text"]
            if not chunks:
                raise ProtocolError("SCHEMA_ERROR", "Response has no output_text")
            return "".join(chunks)
        raise AssertionError("Retry loop did not terminate")
