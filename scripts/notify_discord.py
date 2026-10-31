#!/usr/bin/env python3
"""Report real CI failures or successful deployments to an optional Discord webhook.

Only trusted master-push workflow_run events are accepted. A passing build that
skips deployment is not reported as a successful deployment.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def valid_webhook(url):
    p = urllib.parse.urlparse(url)
    return (
        p.scheme == "https"
        and p.hostname in {"discord.com", "discordapp.com"}
        and p.path.startswith("/api/webhooks/")
        and len(p.path.split("/")) >= 5
        and not p.username
        and not p.password
    )


def get_jobs(run_id, repository, token, opener=urllib.request.urlopen):
    url = f"https://api.github.com/repos/{repository}/actions/runs/{int(run_id)}/jobs?per_page=100"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "fullstackopen-course-notifier",
    })
    with opener(req, timeout=12) as response:
        return json.load(response).get("jobs", [])


def select_notification(event, jobs):
    run = event.get("workflow_run", {})
    if run.get("event") != "push" or run.get("head_branch") != "master":
        return None
    status = run.get("conclusion")
    deploy_ok = any(j.get("name") == "deploy_pages" and j.get("conclusion") == "success" for j in jobs)
    if status == "success" and not deploy_ok:
        return None
    if status not in ("success", "failure"):
        return None
    sha = run.get("head_sha", "")
    if len(sha) < 7:
        return None
    repo = event.get("repository", {}).get("full_name", "")
    if not repo:
        return None
    url = run.get("html_url", "")
    if not url.startswith("https://github.com/"):
        return None
    success = status == "success"
    title = "Pokedex deployed successfully" if success else "Pokedex CI/CD failed"
    description = (
        f"Repository: {repo}\nCommit: {sha[:12]}\n"
        f"Run: {url}\n"
        + ("Deployment job succeeded." if success else "Inspect failed jobs and this commit.")
    )
    return {"embeds": [{"title": title, "description": description,
                        "color": 3066993 if success else 15158332}]}


def run(event, webhook, token, opener=urllib.request.urlopen):
    if not webhook:
        return "SKIPPED: Discord webhook secret not configured"
    if not valid_webhook(webhook):
        raise ValueError("Webhook URL must be a Discord HTTPS API webhook")
    workflow = event.get("workflow_run", {})
    if workflow.get("event") != "push" or workflow.get("head_branch") != "master":
        return "SKIPPED: not a master push"
    if workflow.get("conclusion") not in ("success", "failure"):
        return "SKIPPED: no final success/failure"
    repo = event.get("repository", {}).get("full_name", "")
    if not repo or not token:
        raise ValueError("Missing repository or GitHub Actions read token")
    jobs = get_jobs(workflow["id"], repo, token, opener=opener)
    payload = select_notification(event, jobs)
    if payload is None:
        return "SKIPPED: no actual deployment or failed run"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(webhook, data=data,
                                 headers={"Content-Type": "application/json", "User-Agent": "course-ci"},
                                 method="POST")
    with opener(req, timeout=12) as response:
        if response.status not in (200, 204):
            raise RuntimeError(f"Discord returned HTTP {response.status}")
    return "SENT: deployment result notification"


if __name__ == "__main__":
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
        event = json.load(f)
    try:
        print(run(event, os.environ.get("DISCORD_WEBHOOK", ""),
                  os.environ.get("GITHUB_TOKEN", "")))
    except (ValueError, KeyError, urllib.error.URLError, RuntimeError) as exc:
        print(f"Notification failed: {type(exc).__name__}", file=sys.stderr)
        sys.exit(1)