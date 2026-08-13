import os
import sys
import time
from playwright.sync_api import sync_playwright

# ==================== 配置区域 ====================
# 提取 GitHub Secrets 中的 Cookie
RAW_COOKIE = os.getenv("PURATYA_COOKIE", "")
WEB_PANEL_URL = "https://cloud.puratya.com/web"
DOMAIN = "cloud.puratya.com" # Cookie 适用的域名
# =================================================

def run():
    if not RAW_COOKIE:
        print("❌ 致命错误: 未在环境变量中找到 PURATYA_COOKIE！请检查 GitHub Secrets 配置。")
        sys.exit(1)

    print("🚀 启动无头浏览器 (Cookie 注入直登模式)...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US" 
        )

        # ---------------- 核心逻辑：解析并注入 Cookie ----------------
        cookies_list = []
        try:
            # 将 RAW_COOKIE 字符串分割成字典格式供 Playwright 识别
            for item in RAW_COOKIE.split(';'):
                if '=' in item:
                    name, value = item.strip().split('=', 1)
                    cookies_list.append({
                        "name": name,
                        "value": value,
                        "domain": DOMAIN,
                        "path": "/"
                    })
            context.add_cookies(cookies_list)
            print(f"🍪 成功解析并注入 {len(cookies_list)} 个 Cookie 凭证。")
        except Exception as e:
            print(f"❌ Cookie 解析失败，请确认 Secret 格式是否正确: {e}")
            sys.exit(1)
        # -------------------------------------------------------------

        page = context.new_page()

        try:
            print(f"🌐 正在绕过登录，直达控制台面板: {WEB_PANEL_URL}")
            # 使用 networkidle 确保数据加载完毕
            page.goto(WEB_PANEL_URL, wait_until="networkidle", timeout=30000)
            print(f"📍 当前页面 URL: {page.url}")

            # 验证是否真的进去了（如果没有 cookie 或者 cookie 过期，通常会被重定向回 /login）
            if "login" in page.url.lower():
                print("❌ 认证失败！已为您重定向回登录页。这说明您的 Cookie 可能已过期或不完整，请重新抓取并更新 GitHub Secrets。")
                page.screenshot(path="auth_failed.png")
                sys.exit(1)

            time.sleep(5) # 缓冲时间，等待 React/Vue 渲染倒计时和按钮

            # 执行续期操作
            print("🔍 正在查找控制台上的“续期”按钮...")
            renew_selectors = [
                'button:has-text("续期")',
                'button:has-text("↺ 续期")',
                'text="续期"',
                'button:has-text("Renew")'
            ]

            renew_found = False
            for r_sel in renew_selectors:
                renew_buttons = page.locator(r_sel)
                count = renew_buttons.count()
                if count > 0:
                    print(f"🎉 成功找到 {count} 个“续期”按钮，准备执行点击...")
                    for i in range(count):
                        try:
                            btn = renew_buttons.nth(i)
                            if btn.is_visible():
                                btn.click()
                                print(f"✅ 第 {i+1} 个服务续期点击完成！")
                                time.sleep(3)
                                renew_found = True
                        except Exception as e:
                            print(f"⚠️ 点击第 {i+1} 个按钮时出现异常: {e}")
                    break

            if renew_found:
                print("🌟 本次自动化续期任务圆满执行完毕！")
            else:
                print("⚠️ 面板加载成功，但未匹配到“续期”文本按钮。如果您的服务还在运行，可能是按键状态或文本有变。")
                print("📋 页面文本提取:", page.inner_text("body")[:500])
                page.screenshot(path="dashboard_state.png")

        except Exception as e:
            print(f"💥 运行期间发生致命异常: {e}")
            try:
                page.screenshot(path="fatal_error.png")
            except Exception:
                pass
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    run()
