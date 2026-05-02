"""GitHub 发布模块"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


class GitHubPublisher:
    """GitHub 发布器"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.publishing_config = config.get("publishing", {})
        self.repo_name = "ai-brief"
        self.branch = "main"

    def publish(self, date: str) -> None:
        """发布到 GitHub"""
        # 检查 gh CLI
        if not self._check_gh():
            print("[GitHub] 未安装 gh CLI，请安装: https://cli.github.com/")
            print("[GitHub] 或手动创建仓库并推送")
            return

        # 检查是否已初始化
        if not self._is_git_repo():
            self._init_repo()

        # 复制文件到正确位置
        self._prepare_files(date)

        # 提交并推送
        self._commit_and_push(date)

    def _check_gh(self) -> bool:
        """检查 gh CLI 是否可用"""
        try:
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _is_git_repo(self) -> bool:
        """检查是否已是 git 仓库"""
        return Path(".git").exists()

    def _init_repo(self) -> None:
        """初始化 Git 仓库"""
        print("[GitHub] 初始化 Git 仓库...")

        # 创建 LICENSE
        Path("LICENSE").write_text(
            "MIT License\n\nCopyright (c) 2024 AI Brief\n\n"
            "Permission is hereby granted, free of charge, to any person obtaining a copy "
            "of this software and associated documentation files (the \"Software\"), to deal "
            "in the Software without restriction...\n",
            encoding="utf-8",
        )

        # 创建 .gitignore
        Path(".gitignore").write_text(
            """__pycache__/
*.py[cod]
*$py.class
.Python
venv/
.venv/
*.egg-info/
dist/
build/
site/
data/raw/
data/processed/
media/
.env
*.log
""",
            encoding="utf-8",
        )

        # 初始化 git
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit: AI Brief project"], check=True)

        # 检查是否已登录
        try:
            subprocess.run(["gh", "auth", "status"], capture_output=True, check=True)
        except subprocess.CalledProcessError:
            print("[GitHub] 请先登录: gh auth login")
            return

        # 创建远程仓库
        result = subprocess.run(
            [
                "gh",
                "repo",
                "create",
                self.repo_name,
                "--public",
                "--source=.",
                "--push",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"[GitHub] 创建仓库失败: {result.stderr}")
        else:
            print(f"[GitHub] 仓库已创建: {result.stdout}")

    def _prepare_files(self, date: str) -> None:
        """准备要推送的文件"""
        # 复制 site 内容到临时目录
        site_dir = Path("site")
        if site_dir.exists():
            # 移动 site 内容到仓库根目录
            for item in site_dir.iterdir():
                shutil.copytree(item, Path(item.name), exist_ok=True)

    def _commit_and_push(self, date: str) -> None:
        """提交并推送"""
        # 检查是否有更改
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
        )

        if not status.stdout.strip():
            print("[GitHub] 没有新的更改需要推送")
            return

        # 添加所有文件
        subprocess.run(["git", "add", "."], check=True)

        # 提交
        commit_message = f"Update: AI 早报 {date}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)

        # 推送
        result = subprocess.run(
            ["git", "push", "origin", self.branch, "--force"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(f"[GitHub] 已推送更新: {commit_message}")
        else:
            print(f"[GitHub] 推送失败: {result.stderr}")

    def setup_github_actions(self) -> None:
        """设置 GitHub Actions"""
        workflow_dir = Path(".github/workflows")
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow_content = """name: Daily AI Brief

on:
  schedule:
    - cron: '0 0 * * *'  # 每天 00:00 UTC = 08:00 CST
  workflow_dispatch:  # 手动触发

jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 60

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .

      - name: Collect news
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          OPENAI_BASE_URL: ${{ secrets.OPENAI_BASE_URL }}
          OPENAI_MODEL_FAST: ${{ secrets.OPENAI_MODEL_FAST }}
          OPENAI_MODEL_WRITER: ${{ secrets.OPENAI_MODEL_WRITER }}
          MINIMAX_API_KEY: ${{ secrets.MINIMAX_API_KEY }}
        run: |
          python -m ai_brief run-daily --date $(date +%Y-%m-%d)

      - name: Deploy to GitHub Pages
        if: success()
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add site/ content/daily/
          git commit -m "Deploy: $(date +%Y-%m-%d)"
          git push
"""

        workflow_path = workflow_dir / "daily-brief.yml"
        workflow_path.write_text(workflow_content, encoding="utf-8")
        print(f"[GitHub] GitHub Actions workflow 已创建: {workflow_path}")
