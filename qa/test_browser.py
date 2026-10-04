"""Real Chromium workflow; no API route mocks or external model calls."""

from uuid import uuid4
from pathlib import Path
import os

import pytest
from playwright.sync_api import expect, sync_playwright

from conftest import local_url


@pytest.fixture
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel=os.environ.get("QA_BROWSER_CHANNEL") or None
        )
        context = browser.new_context()
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        yield page
        Path("artifacts/local").mkdir(parents=True, exist_ok=True)
        context.tracing.stop(path="artifacts/local/browser-trace.zip")
        context.close()
        browser.close()


def test_create_evaluate_review_revise_and_history(page):
    title = "QA browser " + uuid4().hex[:8]
    original = "用户登录后尽快优化导出。"
    page.goto(local_url("QA_WEB_URL", "http://127.0.0.1:5173"))
    page.get_by_role("button", name="新建需求", exact=True).first.click()
    page.get_by_label("需求标题").fill(title)
    page.get_by_label("关联项目").fill("isolated browser QA")
    page.get_by_label("负责人").fill("QA")
    page.get_by_label("原始描述").fill(original)
    page.get_by_role("button", name="保存原始需求").click()
    page.get_by_role("button", name="运行质量评估").click()
    expect(page.get_by_role("heading", name="14 维质量剖面")).to_be_visible(
        timeout=30000
    )
    page.get_by_role("button", name="人工反馈", exact=True).click()
    article = page.locator("article").filter(has=page.get_by_label("复核决定")).first
    article.get_by_label("复核决定").select_option("accept")
    with page.expect_response(
        lambda r: r.url.endswith("/feedback") and r.request.method == "POST"
    ) as saved:
        article.get_by_role("button", name="保存复核记录").click()
    assert saved.value.status == 200
    assert saved.value.json()["payload"]["action"] == "accept"
    expect(page.locator("pre").filter(has_text='"action": "accept"')).to_be_visible()
    page.get_by_role("button", name="修改对比", exact=True).click()
    revised = "用户登录后导出订单，验收标准：100条订单在2秒内返回CSV。"
    page.get_by_label("人工确认后的需求").fill(revised)
    page.get_by_label("变更原因").fill("补齐验收标准")
    page.get_by_role("button", name="保存为新版本").click()
    expect(page.get_by_label("需求版本")).to_have_value("2")
    page.get_by_role("button", name="版本历史", exact=True).click()
    expect(page.get_by_text(original, exact=True)).to_be_visible()
    expect(page.get_by_text(revised, exact=True)).to_be_visible()
    page.get_by_label("需求版本").select_option("1")
    page.get_by_role("button", name="质量评分", exact=True).click()
    expect(page.get_by_role("heading", name="14 维质量剖面")).to_be_visible()
