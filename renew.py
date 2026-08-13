import os
import sys
import time
from playwright.sync_api import sync_playwright

# ==================== 配置区域 ====================
USERNAME = os.getenv("PURATYA_USER", "你的Discord账号/邮箱")
PASSWORD = os.getenv("PURATYA_PASS", "你的Discord密码")

LOGIN_URL = "https://cloud.puratya.com/login"
WEB_PANEL_URL = "https://cloud.puratya.com/web"
# =================================================

def run():
    print("🚀 启动无头浏览器...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        
        # 【关键修改 1】：强制指定 locale="en-US"，防止网页根据服务器 IP 自动渲染为日文 (ja)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US" 
        )
        page = context.new_page()

        try:
            print(f"🌐 正在访问登录页面: {LOGIN_URL}")
            page.goto(LOGIN_URL, wait_until="networkidle", timeout=40000)
            print(f"📍 当前页面 URL: {page.url}")

            print("🔍 正在等待并查找 Discord 登录入口...")
            
            # 【关键修改 2】：使用多维度、不完全依赖文本的泛化选择器
            selectors = [
                'a[href*="discord"]',          # 黄金法则：匹配所有超链接目标地址中包含 discord 的 a 标签
                'button:has-text("Discord")',  # 包含 Discord 关键词的按钮
                'a:has-text("Discord")',       # 包含 Discord 关键词的超链接
                'text="Log in with Discord"',  # 英文备用
                'text="Discordでログイン"'       # 日文备用
            ]
            
            btn_found = False
            for sel in selectors:
                try:
                    discord_btn = page.locator(sel).first
                    # 使用较短的超时时间轮询每个选择器
                    if discord_btn.is_visible(timeout=5000):
                        discord_btn.click()
                        print(f"👆 成功匹配并点击入口，使用的选择器是: {sel}")
                        btn_found = True
                        break
                except Exception:
                    continue
            
            if not btn_found:
                print("❌ 未能在页面上找到任何 Discord 登录按钮！")
                print("📋 页面源码片段 (排错用):")
                print(page.content()[:2000])
                page.screenshot(path="no_discord_btn.png")
                sys.exit(1)

            # 等待跳转至 Discord 登录页面
            print("⏳ 正在等待跳转至 Discord 授权页面...")
            page.wait_for_url("**/discord.com/**", timeout=30000)
            time.sleep(3)
            print(f"📍 当前已进入 Discord 页面: {page.url}")

            # 在 Discord 页面输入账号密码
            print("⌨️ 正在注入 Discord 凭据...")
            page.locator('input[name="email"]').fill(USERNAME)
            page.locator('input[name="password"]').fill(PASSWORD)
            page.locator('button[type="submit"]').click()

            # 等待 Discord 登录完成及授权
            print("⏳ 等待 Discord 认证及授权跳转 (如果在此卡住，说明触发了 Discord 的人机验证)...")
            time.sleep(10)
            
            try:
                auth_btn = page.locator('button:has-text("Authorize"), button:has-text("授权")').first
                if auth_btn.is_visible(timeout=5000):
                    auth_btn.click()
                    print("👆 成功点击 Discord 授权 (Authorize) 按钮")
                    time.sleep(5)
            except Exception:
                print("ℹ️ 未检测到授权按钮，可能已自动授权。")

            # 等待跳回 Puratya Web 控制台
            print(f"🔄 等待导航回控制台面板: {WEB_PANEL_URL}")
            page.wait_for_url("**/cloud.puratya.com/web**", timeout=40000)
            time.sleep(8) 
            print(f"📍 成功进入面板 URL: {page.url}")

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
                print("⚠️ 面板加载成功，但未匹配到“续期”文本按钮，正在截取面板视图...")
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
