import os
import sys
import time
import requests
from playwright.sync_api import sync_playwright

# ==================== 配置区域 ====================
USERNAME = os.getenv("PURATYA_USER", "你的Discord账号/邮箱")
PASSWORD = os.getenv("PURATYA_PASS", "你的Discord密码")

# Telegram Bot 配置
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "你的TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "你的TG_CHAT_ID")

LOGIN_URL = "https://cloud.puratya.com/login"
WEB_PANEL_URL = "https://cloud.puratya.com/web"
# =================================================

def send_tg_message(text):
    """发送 TG 文本消息"""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ TG 消息发送失败: {e}")

def send_tg_photo(photo_path, caption=""):
    """发送 TG 图片消息"""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto"
    try:
        with open(photo_path, "rb") as photo:
            payload = {"chat_id": TG_CHAT_ID, "caption": caption}
            files = {"photo": photo}
            requests.post(url, data=payload, files=files, timeout=20)
    except Exception as e:
        print(f"⚠️ TG 图片发送失败: {e}")

def run():
    print("🚀 启动无头浏览器...")
    send_tg_message("🚀 Puratya 自动续期任务已启动...")
    
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
        page = context.new_page()

        try:
            print(f"🌐 正在访问登录页面: {LOGIN_URL}")
            page.goto(LOGIN_URL, wait_until="networkidle", timeout=40000)

            print("🔍 正在查找 Discord 登录入口...")
            selectors = [
                'a[href*="discord"]',
                'button:has-text("Discord")',
                'a:has-text("Discord")',
                'text="Log in with Discord"'
            ]
            
            btn_found = False
            for sel in selectors:
                try:
                    discord_btn = page.locator(sel).first
                    if discord_btn.is_visible(timeout=5000):
                        discord_btn.click()
                        print(f"👆 成功匹配并点击入口: {sel}")
                        btn_found = True
                        break
                except Exception:
                    continue
            
            if not btn_found:
                error_msg = "❌ 未能在页面上找到任何 Discord 登录按钮！"
                print(error_msg)
                page.screenshot(path="no_discord_btn.png")
                send_tg_photo("no_discord_btn.png", error_msg)
                sys.exit(1)

            # 等待跳转至 Discord
            print("⏳ 正在等待跳转至 Discord 授权页面...")
            page.wait_for_url("**/discord.com/**", timeout=30000)
            time.sleep(3)

            # 输入账号密码
            print("⌨️ 正在注入 Discord 凭据...")
            page.locator('input[name="email"]').fill(USERNAME)
            page.locator('input[name="password"]').fill(PASSWORD)
            page.locator('button[type="submit"]').click()

            print("⏳ 等待 Discord 认证及授权跳转...")
            time.sleep(10)
            
            try:
                auth_btn = page.locator('button:has-text("Authorize"), button:has-text("授权")').first
                if auth_btn.is_visible(timeout=5000):
                    auth_btn.click()
                    print("👆 成功点击 Discord 授权按钮")
                    time.sleep(5)
            except Exception:
                print("ℹ️ 未检测到授权按钮，可能已自动授权。")

            # 强制导航至 Web 续期面板，防止停留在其他主页
            print(f"🔄 导航至控制台 Web 面板: {WEB_PANEL_URL}")
            page.goto(WEB_PANEL_URL, wait_until="networkidle", timeout=40000)
            time.sleep(5) 
            
            # 截图：续期前状态
            page.screenshot(path="before_renew.png")
            send_tg_photo("before_renew.png", "📊 当前 Web 面板状态（续期前）")

            # 执行续期操作 (基于截图 image_7a85c3.png，按钮文本为 "↻ 续期")
            print("🔍 正在查找控制台上的“续期”按钮...")
            renew_selectors = [
                'button:has-text("续期")',
                'button:has-text("Renew")'
            ]

            renew_count = 0
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
                                renew_count += 1
                                time.sleep(4) # 等待 API 请求完成
                        except Exception as e:
                            print(f"⚠️ 点击第 {i+1} 个按钮时出现异常: {e}")
                    break # 找到一种选择器并执行后跳出循环

            if renew_count > 0:
                success_msg = f"🌟 本次自动化续期任务圆满执行完毕！共续期 {renew_count} 个服务。"
                print(success_msg)
                
                # 截图：续期后状态
                page.screenshot(path="after_renew.png")
                send_tg_photo("after_renew.png", success_msg)
            else:
                warn_msg = "⚠️ 面板加载成功，但未匹配到需要续期的按钮或服务已是最新状态。"
                print(warn_msg)
                page.screenshot(path="no_renew_needed.png")
                send_tg_photo("no_renew_needed.png", warn_msg)

        except Exception as e:
            error_msg = f"💥 运行期间发生致命异常: {e}"
            print(error_msg)
            try:
                page.screenshot(path="fatal_error.png")
                send_tg_photo("fatal_error.png", error_msg)
            except Exception:
                send_tg_message(error_msg)
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    run()
