import io
import json
import pathlib
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from notify_discord import get_jobs, run, select_notification, valid_webhook


def event(status="success", kind="push", branch="master"):
    return {"repository": {"full_name": "AleksandrG11/full-stack-open-pokedex"},
            "workflow_run": {"id": 123, "event": kind, "head_branch": branch,
                             "conclusion": status, "head_sha": "a" * 40,
                             "html_url": "https://github.com/AleksandrG11/full-stack-open-pokedex/actions/runs/123"}}


class Response(io.BytesIO):
    status = 204
    def __enter__(self): return self
    def __exit__(self, *args): self.close()


class NotificationTests(unittest.TestCase):
    def test_success_requires_actual_deploy(self):
        self.assertIsNone(select_notification(event(), [{"name": "deploy_pages", "conclusion": "skipped"}]))
        self.assertIn("deployed", select_notification(event(), [{"name": "deploy_pages", "conclusion": "success"}])["embeds"][0]["title"])

    def test_failure_includes_commit_and_run(self):
        p = select_notification(event("failure"), [{"name": "quality", "conclusion": "failure"}])
        self.assertIn("aaaaaaaaaaaa", p["embeds"][0]["description"])
        self.assertIn("runs/123", p["embeds"][0]["description"])

    def test_pull_request_does_not_send(self):
        self.assertIsNone(select_notification(event(kind="pull_request"), [{"name": "deploy_pages", "conclusion": "success"}]))

    def test_webhook_validation(self):
        self.assertTrue(valid_webhook("https://discord.com/api/webhooks/123/secret"))
        for url in ["https://evil.example/api/webhooks/123/secret", "http://discord.com/api/webhooks/123/secret", "https://discord.com.evil.org/api/webhooks/123/secret"]:
            self.assertFalse(valid_webhook(url))

    def test_missing_secret_skips_without_network(self):
        self.assertIn("SKIPPED", run(event(), "", "token", opener=lambda *a, **k: self.fail("network called")))

    def test_actual_send_uses_jobs_api_and_discord_post(self):
        calls = []
        def fake_open(req, timeout):
            calls.append(req)
            if req.full_url.startswith("https://api.github.com/"):
                return Response(json.dumps({"jobs": [{"name": "deploy_pages", "conclusion": "success"}]}).encode())
            return Response()
        out = run(event(), "https://discord.com/api/webhooks/123/secret", "token", opener=fake_open)
        self.assertIn("SENT", out)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[-1].get_method(), "POST")
        self.assertIn("Pokedex deployed successfully", calls[-1].data.decode())

    def test_skipped_deploy_no_discord_post(self):
        calls = []
        def fake_open(req, timeout):
            calls.append(req)
            return Response(json.dumps({"jobs": [{"name": "deploy_pages", "conclusion": "skipped"}]}).encode())
        self.assertIn("SKIPPED", run(event(), "https://discord.com/api/webhooks/123/secret", "token", opener=fake_open))
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()