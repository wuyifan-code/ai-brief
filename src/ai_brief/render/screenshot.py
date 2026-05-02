"""浏览器截图模块"""

import asyncio
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright


async def _screenshot_async(cards: list[dict[str, Any]], output_dir: Path) -> list[Path]:
    """异步截图"""
    screenshots = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for card in cards:
            page = await browser.new_page(viewport={"width": 1920, "height": 1080})

            # 写入临时 HTML 文件
            html_path = output_dir / f"card_{card['index']}.html"
            html_path.write_text(card["html"], encoding="utf-8")

            # 截图
            screenshot_path = output_dir / f"screenshot_{card['index']}.png"
            await page.goto(f"file:///{html_path.absolute()}")
            await page.screenshot(path=str(screenshot_path), full_page=False)
            await page.close()

            screenshots.append(screenshot_path)

        await browser.close()

    return screenshots


def screenshot_cards(cards: list[dict[str, Any]], output_dir: Path) -> list[Path]:
    """截图生成图片素材"""
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        return asyncio.run(_screenshot_async(cards, output_dir))
    except Exception as e:
        print(f"[screenshot] 截图失败: {e}")
        print("[screenshot] 确保已安装 playwright: python -m playwright install chromium")
        return []
