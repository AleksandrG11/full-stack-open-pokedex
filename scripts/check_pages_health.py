#!/usr/bin/env python3
"""Check the public static Pokedex deployment, failing loudly on bad HTTP/JSON."""
import argparse
import json
import re
import sys
from urllib.parse import urljoin
from urllib.request import Request, urlopen

def get(url, timeout):
    request = Request(url, headers={"User-Agent": "FullStackOpen-HealthMonitor/1.0", "Cache-Control": "no-cache"})
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"{url}: HTTP {response.status}")
        return response.read(200_000)

def check(base, timeout):
    base = base.rstrip("/") + "/"
    html = get(urljoin(base, "index.html"), timeout)
    if b"<html" not in html.lower():
        raise ValueError("Deployed index.html is not HTML")
    health = json.loads(get(urljoin(base, "health.json"), timeout))
    if health.get("status") != "ok":
        raise ValueError("Health status not ok")
    sha = health.get("sha")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Missing or invalid deployment commit SHA")
    return sha

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="https://aleksandrg11.github.io/full-stack-open-pokedex/")
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args()
    try:
        sha = check(args.base, args.timeout)
    except Exception as exc:
        print(f"UNHEALTHY: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"HEALTHY: deployed commit {sha}")
