import os
import sys
import time
from playwright.sync_api import sync_playwright

# ==================== 配置区域 ====================
# 支持从环境变量读取（推荐 GitHub Secrets），若没有则使用下方硬编码
USERNAME = os.getenv("PURATYA_USER", "你的账号或邮箱")
PASSWORD = os.getenv("PURATYA_PASS", "你的密码")

# 网址配置
BASE_URL = "https://cloud.puratya.com"
LOGIN_URL = "https://cloud.puratya.com/login"  # 若登录页即首页，可改填 https://cloud.puratya.com
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
            print(f"🌐 正在访问登录页面: {LOGIN_URL}")
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=40000)
            time.sleep(3)

            print(f"📍 当前页面 URL: {page.url}")
            print(f"📄 当前页面标题: {page.title()}")

            # 多选择器兼容方案：按顺序查找账号输入框
            username_selectors = [
                'input[type="email"]',
                'input[type="text"]',
                'input[name="email"]',
                'input[name="username"]',
                'input[name="user"]',
                'input[placeholder*="邮"]',
                'input[placeholder*="用"]',
                'input[placeholder*="账号"]',
                'input[placeholder*="Email"]',
                'input'  # 若均无则尝试页面第一个输入框
            ]

            user_input = None
            for selector in username_selectors:
                try:
                    loc = page.locator(selector).first
                    if loc.is_visible(timeout=2000):
                        user_input = loc
                        print(f"✅ 找到账号输入框: {selector}")
                        break
                except Exception:
                    continue

            if not user_input:
                print("❌ 未能在页面上找到任何账号输入框！")
                print("📋 页面文本预览：\n", page.inner_text("body")[:500])
                page.screenshot(path="login_error.png")
                sys.exit(1)

            user_input.fill(USERNAME)

            # 查找密码输入框
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder*="密"]',
                'input[placeholder*="Password"]'
            ]
            pass_input = None
            for selector in password_selectors:
                try:
                    loc = page.locator(selector).first
                    if loc.is_visible(timeout=2000):
                        pass_input = loc
                        print(f"✅ 找到密码输入框: {selector}")
                        break
                except Exception:
                    continue

            if not pass_input:
                print("❌ 未找到密码输入框！")
                page.screenshot(path="password_error.png")
                sys.exit(1)

            pass_input.fill(PASSWORD)

            # 点击登录按钮
            login_buttons = [
                'button[type="submit"]',
                'button:has-text("登录")',
                'button:has-text("Login")',
                'input[type="submit"]',
                '.btn-primary'
            ]
            clicked = False
            for btn_sel in login_buttons:
                try:
                    btn = page.locator(btn_sel).first
                    if btn.is_visible(timeout=1500):
                        btn.click()
                        print(f"👆 点击登录按钮: {btn_sel}")
                        clicked = True
                        break
                except Exception:
                    continue

            if not clicked:
                pass_input.press("Enter")
                print("👆 在密码框按回车提交登录")

            # 等待登录响应并跳转
            print("⏳ 等待登录认证完成...")
            time.sleep(5)

            # 明确跳转至 Web 管理控制台
            print(f"🔄 导航至 Web 控制台: {WEB_PANEL_URL}")
            page.goto(WEB_PANEL_URL, wait_until="domcontentloaded", timeout=30000)
            time.sleep(5)

            print(f"📍 当前控制台 URL: {page.url}")

            # 匹配并点击“续期”按钮
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
                print("⚠️ 未能在页面匹配到“续期”按钮，正在截取面板视图...")
                page.screenshot(path="dashboard_state.png")
                print("📋 控制台页面文本：\n", page.inner_text("body")[:600])

        except Exception as e:
            print(f"💥 运行遭遇异常: {e}")
            try:
                page.screenshot(path="fatal_error.png")
            except Exception:
                pass
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    run()
