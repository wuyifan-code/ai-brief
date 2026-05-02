"""GitHub 资讯采集器"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx


class GitHubCollector:
    """GitHub 采集器"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.github_config = config.get("github", {})
        self.repos = self.github_config.get("repos", [])
        self.keywords = self.github_config.get("keywords", [])
        self.api_base = "https://api.github.com"

    def collect(self, date: str) -> list[dict[str, Any]]:
        """采集指定日期的 GitHub 资讯"""
        all_items: list[dict[str, Any]] = []
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        window_start = target_date - timedelta(days=3)

        for repo in self.repos:
            if not repo.get("enabled", True):
                continue

            owner = repo["owner"]
            repo_name = repo["repo"]
            category = repo.get("category", "GitHub")
            weight = repo.get("weight", 5)

            try:
                # 采集 Releases
                releases = self._fetch_releases(owner, repo_name)
                for release in releases:
                    published = self._parse_date(release.get("published_at"))
                    if published is None:
                        continue

                    if published.date() > target_date or published.date() < window_start:
                        continue

                    item = self._release_to_item(release, owner, repo_name, category, weight)
                    all_items.append(item)

                # 采集 Repository Events
                events = self._fetch_events(owner, repo_name)
                for event in events:
                    created = self._parse_date(event.get("created_at"))
                    if created is None:
                        continue

                    if created.date() > target_date or created.date() < window_start:
                        continue

                    if self._event_matches_keywords(event):
                        item = self._event_to_item(event, owner, repo_name, category, weight)
                        all_items.append(item)

            except Exception as e:
                print(f"[GitHub] 采集失败 {owner}/{repo_name}: {e}")

        # 保存到 raw data
        self._save_raw(date, all_items)
        return all_items

    def _fetch_releases(self, owner: str, repo: str) -> list[dict]:
        """获取仓库 releases"""
        url = f"{self.api_base}/repos/{owner}/{repo}/releases"
        headers = {"Accept": "application/vnd.github.v3+json"}

        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    def _fetch_events(self, owner: str, repo: str) -> list[dict]:
        """获取仓库 events"""
        url = f"{self.api_base}/repos/{owner}/{repo}/events"
        headers = {"Accept": "application/vnd.github.v3+json"}

        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    def _release_to_item(
        self, release: dict, owner: str, repo: str, category: str, weight: int
    ) -> dict[str, Any]:
        """将 release 转换为统一格式"""
        return {
            "id": f"github:{owner}/{repo}/release/{release.get('id')}",
            "title": release.get("name") or release.get("tag_name", "Release"),
            "link": release.get("html_url", f"https://github.com/{owner}/{repo}/releases"),
            "summary": release.get("body", "")[:500],
            "published": release.get("published_at"),
            "source": f"{owner}/{repo}",
            "source_url": f"https://github.com/{owner}/{repo}",
            "category": category,
            "weight": weight,
            "type": "github_release",
        }

    def _event_to_item(
        self, event: dict, owner: str, repo: str, category: str, weight: int
    ) -> dict[str, Any]:
        """将 event 转换为统一格式"""
        event_type = event.get("type", "Event")
        payload = event.get("payload", {})

        title = self._event_to_title(event_type, payload)
        link = event.get("actor", {}).get("html_url", f"https://github.com/{owner}/{repo}")

        return {
            "id": f"github:{owner}/{repo}/event/{event.get('id')}",
            "title": title,
            "link": link,
            "summary": f"{event_type} event in {owner}/{repo}",
            "published": event.get("created_at"),
            "source": f"{owner}/{repo}",
            "source_url": f"https://github.com/{owner}/{repo}",
            "category": category,
            "weight": weight,
            "type": "github_event",
        }

    def _event_to_title(self, event_type: str, payload: dict) -> str:
        """将事件类型转换为标题"""
        titles = {
            "PushEvent": f"Code push to {payload.get('ref', 'repository')}",
            "CreateEvent": f"Created {payload.get('ref_type', 'resource')} in repository",
            "IssuesEvent": f"Issue {payload.get('action', '')}: {payload.get('issue', {}).get('title', '')}",
            "PullRequestEvent": f"Pull request {payload.get('action', '')}: {payload.get('pull_request', {}).get('title', '')}",
            "ReleaseEvent": f"Released {payload.get('release', {}).get('tag_name', '')}",
            "ForkEvent": f"Forked repository",
            "WatchEvent": "Starred repository",
            "MemberEvent": "Repository membership changed",
        }
        return titles.get(event_type, f"{event_type} in repository")

    def _event_matches_keywords(self, event: dict) -> bool:
        """检查事件是否匹配关键词"""
        if not self.keywords:
            return True

        event_text = json.dumps(event, ensure_ascii=False).lower()
        return any(kw.lower() in event_text for kw in self.keywords)

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """解析日期字符串"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            try:
                from dateutil import parser

                return parser.parse(date_str)
            except Exception:
                return None

    def _save_raw(self, date: str, items: list[dict[str, Any]]) -> None:
        """保存原始数据"""
        raw_path = Path(f"data/raw/{date}.jsonl")
        raw_path.parent.mkdir(parents=True, exist_ok=True)

        with raw_path.open("a", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
