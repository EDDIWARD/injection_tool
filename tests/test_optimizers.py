import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from injection_tool.core import ROOT
from injection_tool.optimizers import optimize, describe_methods
from injection_tool.optimizers.client import APIError, ChatClient, parse_object, validate_config


def config(base="http://127.0.0.1:1/v1"):
    return {role: {"base_url": base, "model": role, "api_key_env": None, "timeout": 2}
            for role in ("attacker", "target", "judge")}


class FakeClient:
    def __init__(self, success_at=2, off_topic=False):
        self.requests, self.generated = [], 0
        self.success_at, self.off_topic = success_at, off_topic

    def complete(self, role, messages):
        self.requests.append((role, messages))
        if role == "attacker":
            self.generated += 1
            return json.dumps({"prompt": f"candidate {self.generated}", "improvement": "feedback revision"})
        if role == "target":
            value = messages[-1]["content"]
            success = value.startswith("candidate ") and int(value.split()[-1]) >= self.success_at
            return "TEST_OK" if success else "test behavior not met"
        data = json.loads(messages[-1]["content"])
        if "response" not in data:
            return json.dumps({"on_topic": not self.off_topic, "reason": "topic check"})
        success = data["response"] == "TEST_OK"
        score = 10 if success else 2 if data["candidate"].startswith("candidate ") else 0
        return json.dumps({"score": score, "success": success, "reason": "observed response"})


class OptimizerTests(unittest.TestCase):
    def test_pair_uses_feedback_and_keeps_best_with_exact_budget(self):
        client = FakeClient()
        events = []
        result = optimize("TEST_OK", method="pair", config=config(), client=client, on_event=events.append)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["baseline_score"], 0)
        self.assertEqual(result["score_gain"], 10)
        self.assertEqual(result["calls"], {"attacker": 2, "target": 3, "judge": 3, "total": 8})
        self.assertEqual(result["best"]["parent_id"], "candidate-0002")
        generations = [m for role, m in client.requests if role == "attacker"]
        history = json.loads(generations[1][-1]["content"])["recent_history"]
        self.assertEqual(history[-1]["score"], 2)
        self.assertEqual(events[-1]["event"], "complete")
        # Events are snapshots, not references that change later.
        self.assertEqual(next(e for e in events if e["event"] == "candidate")["candidate"]["status"], "pending")

    def test_budget_counts_all_roles_and_keeps_unscored_candidate(self):
        result = optimize("TEST_OK", config=config(), client=FakeClient(), max_calls=4)
        self.assertEqual(result["status"], "budget_exhausted")
        self.assertEqual(result["calls"]["total"], 4)
        self.assertEqual(result["history"][-1]["status"], "unscored")
        self.assertEqual(result["best"]["round"], 0)
        self.assertFalse(result["success"])

    def test_tap_prunes_before_target_and_selects_best_frontier(self):
        client = FakeClient(off_topic=True)
        result = optimize("TEST_OK", method="tap", config=config(), client=client)
        self.assertEqual(result["status"], "no_candidates")
        self.assertEqual(result["calls"]["target"], 1)
        self.assertEqual(sum(r["status"] == "pruned" for r in result["history"]), 2)
        result = optimize("TEST_OK", method="tap", config=config(), client=FakeClient(success_at=99),
                          width=1, branching=2, rounds=2, max_calls=30)
        self.assertEqual(result["status"], "round_limit")
        self.assertEqual(len(result["history"]), 5)
        parents = {r["parent_id"] for r in result["history"] if r["round"] == 2}
        self.assertEqual(len(parents), 1)

    def test_gptfuzz_runs_seed_pool_mutations(self):
        client = FakeClient(success_at=99)
        result = optimize("TEST_OK", method="gptfuzz", config=config(), client=client, rounds=4)
        self.assertEqual(len(result["seed_ids"]), 3)
        self.assertEqual(result["calls"]["attacker"], 4)
        self.assertEqual([r["operation"] for r in result["history"] if r["round"]],
                         ["paraphrase", "shorten", "expand_context", "combine_two_candidates"])
        last = json.loads([m for role, m in client.requests if role == "attacker"][-1][-1]["content"])
        self.assertIn("second_candidate", last)

    def test_pair_multiple_streams_and_duplicate_avoidance(self):
        result = optimize("TEST_OK", config=config(), client=FakeClient(success_at=99), streams=3, rounds=1)
        self.assertEqual(result["calls"]["attacker"], 3)
        self.assertTrue(all(r["parent_id"] == "candidate-0001" for r in result["history"] if r["round"]))
        client = FakeClient()
        original = client.complete
        client.complete = lambda role, messages: json.dumps({"prompt": "TEST_OK"}) if role == "attacker" else original(role, messages)
        result = optimize("TEST_OK", config=config(), client=client, rounds=2)
        self.assertEqual(result["calls"]["target"], 1)
        self.assertEqual(len(result["history"]), 1)

    def test_model_failure_and_bad_judgment_preserve_partial_history(self):
        client = FakeClient()
        original = client.complete
        def fail(role, messages):
            if role == "attacker":
                raise APIError("test API unavailable")
            return original(role, messages)
        client.complete = fail
        result = optimize("TEST_OK", config=config(), client=client)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["calls"]["total"], 3)
        self.assertEqual(result["best"]["score"], 0)
        client.complete = lambda role, messages: '{"score":true,"success":true}' if role == "judge" else original(role, messages)
        result = optimize("TEST_OK", config=config(), client=client)
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["best"])
        self.assertEqual(result["history"][0]["status"], "unscored")

    def test_baseline_success_does_not_claim_optimization_gain(self):
        class AlreadySuccessful:
            def complete(self, role, messages):
                if role == "target": return "TEST_OK"
                if role == "judge": return '{"score":10,"success":true,"reason":"marker present"}'
                raise AssertionError("Should not call attacker")
        result = optimize("TEST_OK", config=config(), client=AlreadySuccessful())
        self.assertEqual(result["score_gain"], 0)
        self.assertEqual(result["calls"]["total"], 2)

    def test_preflight_and_json_validation(self):
        for invalid in (dict(rounds=0), dict(max_calls=1), dict(threshold=True), dict(method="llmattacks"), dict(seed_ids=["missing"])):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                optimize("TEST_OK", config=config(), **invalid)
        with self.assertRaises(APIError): parse_object('text {"score":10}')
        self.assertEqual(parse_object('```json\n{"score": 1}\n```'), {"score": 1})
        for value in ("https://user:password@example.test/v1", "https://example.test/v1?key=secret", None):
            cfg = config(); cfg["attacker"]["base_url"] = value
            with self.assertRaises(ValueError): validate_config(cfg)
        cfg = config(); cfg["target"]["api_key_env"] = "MISSING_OPTIMIZER_TEST_KEY"
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError): ChatClient(cfg).preflight()
            result = optimize("TEST_OK", config=cfg, dry_run=True)
            self.assertEqual(result["calls"]["total"], 0)

    def test_upstream_sources_are_pinned_and_byte_exact(self):
        manifest = json.loads((ROOT / "data/optimizer_sources.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["sources"]), 6)
        for source in manifest["sources"]:
            self.assertRegex(source["commit"], r"^[0-9a-f]{40}$")
            self.assertTrue((ROOT / source["directory"] / source["entrypoint"]).exists())
            self.assertTrue(any(Path(r["path"]).name.startswith("LICENSE") for r in source["files"]))
            for record in source["files"]:
                content = (ROOT / source["directory"] / record["path"]).read_bytes()
                self.assertEqual(hashlib.sha256(content).hexdigest(), record["sha256"])
        self.assertEqual(sum(m["api_adapter"] for m in describe_methods()["methods"]), 3)


class HTTPIntegrationTests(unittest.TestCase):
    def setUp(self):
        fake = FakeClient(success_at=2)
        self.received = []
        received = self.received
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_POST(self):
                request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                received.append((self.path, dict(self.headers), request))
                if request["model"] == "http-error":
                    self.send_response(429); self.end_headers(); self.wfile.write(b"DO_NOT_LOG_SECRET"); return
                if request["model"] == "redirect":
                    self.send_response(302); self.send_header("Location", "/stolen"); self.end_headers(); return
                reply = fake.complete(request["model"], request["messages"])
                response = json.dumps({"choices": [{"message": {"content": reply}}]}).encode()
                self.send_response(200); self.send_header("Content-Type", "application/json")
                self.end_headers(); self.wfile.write(response)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}/v1"

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)

    def test_cli_runs_real_http_loop_and_writes_progress(self):
        cfg = config(self.base)
        cfg["target"]["system_prompt"] = "Keep the configured task context."
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            path, out, events = directory / "config.json", directory / "result.json", directory / "events.jsonl"
            path.write_text(json.dumps(cfg), encoding="utf-8")
            command = [sys.executable, str(ROOT / "app.py"), "optimize", "--goal", "TEST_OK", "--config", str(path), "--out", str(out), "--events", str(events)]
            p = subprocess.run(command, capture_output=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            result = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["calls"]["total"], len(self.received))
            stream = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(stream[-1]["event"], "complete")
            target = next(body for _, _, body in self.received if body["model"] == "target")
            self.assertEqual(target["messages"][0]["content"], cfg["target"]["system_prompt"])
            self.assertTrue(all(url == "/v1/chat/completions" for url, _, _ in self.received))
            count = len(self.received)
            p = subprocess.run(command, capture_output=True)
            self.assertEqual(p.returncode, 2)
            self.assertEqual(len(self.received), count)

    def test_credentials_and_server_error_bodies_are_not_in_results(self):
        cfg = config(self.base)
        cfg["target"]["model"] = "http-error"
        cfg["target"]["api_key_env"] = "OPTIMIZER_TEST_KEY"
        with patch.dict(os.environ, {"OPTIMIZER_TEST_KEY": "DO_NOT_LOG_SECRET"}):
            result = optimize("TEST_OK", config=cfg)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["calls"]["total"], 1)
        self.assertNotIn("DO_NOT_LOG_SECRET", json.dumps(result))
        self.assertIn("429", result["error"])
        self.assertEqual(self.received[0][1]["Authorization"], "Bearer DO_NOT_LOG_SECRET")

    def test_http_redirect_is_not_followed(self):
        cfg = config(self.base)
        cfg["target"]["model"] = "redirect"
        result = optimize("TEST_OK", config=cfg)
        self.assertEqual(result["status"], "error")
        self.assertEqual(len(self.received), 1)


if __name__ == "__main__":
    unittest.main()
