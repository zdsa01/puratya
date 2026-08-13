import os
import sys
import time
from playwright.sync_api import sync_playwright

# ==================== 配置区域 ====================
# 这里现在需要填写的是你的 Discord 账号和密码
USERNAME = os.getenv("PURATYA_USER", "你的Discord账号/邮箱")
PASSWORD = os.getenv("PURATYA_PASS", "你的Discord密码")

BASE_URL = "https://cloud.puratya.com"
WEB_PANEL_URL = "https://cloud.puratya.com/web"
# =================================================

def run():
    print("🚀 启动无头浏览器...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()

        try:
            print(f"🌐 正在访问主页面: {BASE_URL}")
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=40000)
            time.sleep(3)

            # 1. 寻找并点击 "Log in with Discord" 按钮
            print("🔍 正在查找 Discord 登录入口...")
            login_entry_selectors = [
                'text="Log in with Discord"',
                'a[href*="discord.com/oauth2"]',
                'button:has-text("Discord")'
            ]
            
            clicked_discord = False
            for sel in login_entry_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=3000):
                        btn.click()
                        print(f"👆 已点击 Discord 登录按钮: {sel}")
                        clicked_discord = True
                        break
                except Exception:
                    continue
            
            if not clicked_discord:
                print("❌ 未能在页面上找到 Discord 登录入口！")
                page.screenshot(path="no_discord_btn.png")
                sys.exit(1)

            # 2. 等待跳转至 Discord 登录页面
            print("⏳ 等待跳转至 Discord 登录页面...")
            page.wait_for_url("**/discord.com/**", timeout=30000)
            time.sleep(3)
            print(f"📍 当前 URL: {page.url}")

            # 3. 在 Discord 页面输入账号密码
            print("⌨️ 正在输入 Discord 凭据...")
            page.locator('input[name="email"]').fill(USERNAME)
            page.locator('input[name="password"]').fill(PASSWORD)
            page.locator('button[type="submit"]').click()

            # 4. 等待 Discord 登录完成及授权
            print("⏳ 等待 Discord 认证及可能的授权跳转...")
            time.sleep(8)
            
            # 处理可能出现的 Discord "授权 (Authorize)" 按钮
            try:
                auth_btn = page.locator('button:has-text("Authorize"), button:has-text("授权")').first
                if auth_btn.is_visible(timeout=5000):
                    auth_btn.click()
                    print("👆 点击了 Discord 授权按钮")
                    time.sleep(5)
            except Exception:
                pass # 如果没有授权按钮则忽略

            # 5. 等待跳回 Puratya Web 控制台
            print(f"🔄 等待导航回 Web 控制台: {WEB_PANEL_URL}")
            page.wait_for_url("**/cloud.puratya.com/web**", timeout=40000)
            time.sleep(5)

            # 6. 执行续期操作
            print("🔍 正在查找“续期”按钮...")
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
                    print(f"🎉 找到 {count} 个“续期”按钮，正在点击...")
                    for i in range(count):
                        try:
                            btn = renew_buttons.nth(i)
                            if btn.is_visible():
                                btn.click()
                                print(f"✅ 第 {i+1} 个服务续期成功！")
                                time.sleep(3)
                                renew_found = True
                        except Exception as e:
                            print(f"⚠️ 点击第 {i+1} 个按钮异常: {e}")
                    break

            if renew_found:
                print("🌟 自动续期任务执行完毕！")
            else:
                print("⚠️ 未匹配到“续期”按钮，正在截取面板视图...")
                page.screenshot(path="dashboard_state.png")

        except Exception as e:
            print(f"💥 运行遭遇异常: {e}")
            try:
                page.screenshot(path="fatal_error.png")
            except Exception:
                pass
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    run()
