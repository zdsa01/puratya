import os
import sys
import time
import requests
from playwright.sync_api import sync_playwright

# ==================== 配置区域 ====================
USERNAME = os.getenv("PURATYA_USER", "")
PASSWORD = os.getenv("PURATYA_PASS", "")

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")

# 直接定位到你指定的子站点页面
TARGET_SITE_URL = "https://cloud.puratya.com/sites/366"
LOGIN_URL = "https://cloud.puratya.com/"
# =================================================

def send_tg_message(text):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text}, timeout=10)
    except Exception:
        pass

def send_tg_photo(photo_path, caption=""):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto"
    try:
        with open(photo_path, "rb") as photo:
            requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": caption}, files={"photo": photo}, timeout=20)
    except Exception:
        pass

def run():
    print("🚀 启动自动化续期脚本 (指定站点模式)...")
    send_tg_message(f"🚀 Puratya 自动续期任务已启动，目标: {TARGET_SITE_URL}")
    
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
            print(f"🌐 正在访问 Puratya 首页: {LOGIN_URL}")
            page.goto(LOGIN_URL, wait_until="networkidle", timeout=40000)

            print("🔍 正在查找登录按钮 (包含 Log in again 状态)...")
            # 兼容截图 image_79a87e.jpg 中的特殊状态按钮
            selectors = [
                'button:has-text("Log in again")',
                'button:has-text("Discordでログインして始める")',
                'button:has-text("Discord")',
                'a:has-text("Log in again")'
            ]
            
            btn_found = False
            for sel in selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=5000):
                        btn.click()
                        print(f"👆 成功点击首页入口按钮，匹配器: {sel}")
                        btn_found = True
                        break
                except:
                    continue
            
            if not btn_found:
                page.screenshot(path="no_login_btn.png")
                send_tg_photo("no_login_btn.png", "❌ 未能在首页找到登录按钮！")
                raise Exception("无法找到 Discord 登录入口。")

            print("⏳ 正在等待跳转至 Discord...")
            page.wait_for_url("**/discord.com/**", timeout=30000)
            time.sleep(3)

            print("⌨️ 正在输入账号密码进行常规登录...")
            page.locator('input[name="email"]').fill(USERNAME)
            page.locator('input[name="password"]').fill(PASSWORD)
            page.locator('button[type="submit"]').click()
            
            print("⏳ 正在等待 Discord 认证，时长 15 秒 (防风控缓冲)...")
            time.sleep(15)

            # 尝试处理授权界面的 Authorize 按钮
            try:
                auth_btn = page.locator('button:has-text("Authorize"), button:has-text("授权")').first
                if auth_btn.is_visible(timeout=5000):
                    auth_btn.click()
                    print("👆 成功点击 Discord 授权按钮")
                    time.sleep(5)
            except Exception:
                print("ℹ️ 未检测到手动授权按钮，可能已自动通过。")

            # ================= 直接导航到目标站点 =================
            print(f"🎯 直接强制导航至目标站点: {TARGET_SITE_URL}")
            page.goto(TARGET_SITE_URL, wait_until="networkidle", timeout=40000)
            time.sleep(8) # 给予页面数据加载时间
            
            # 校验是否成功进入了目标页面（如果仍然停留在未登录状态或主页）
            if "login" in page.url.lower() or "discord" in page.url.lower():
                page.screenshot(path="auth_failed.png")
                send_tg_photo("auth_failed.png", "❌ 登录失败，被 Discord 验证码拦截或重定向回了主页。")
                raise Exception("原生账号密码登录失败，可能遇到了验证码风控。")

            page.screenshot(path="before_renew.png")
            send_tg_photo("before_renew.png", "📊 目标站点状态（续期前）")

            # ================= 在特定页面执行续期 =================
            print("🔍 正在当前页面查找“续期”按钮...")
            renew_selectors = [
                'button:has-text("续期")',
                'button:has-text("↻ 续期")',
                'button:has-text("Renew")'
            ]
            
            renew_success = False
            for r_sel in renew_selectors:
                btn = page.locator(r_sel).first
                try:
                    if btn.is_visible(timeout=3000):
                        print("🎉 找到续期按钮，准备点击...")
                        btn.click()
                        time.sleep(5) # 等待后端 API 请求完成
                        renew_success = True
                        break
                except Exception:
                    continue

            if renew_success:
                success_msg = f"🌟 站点 {TARGET_SITE_URL} 续期任务圆满执行完毕！"
                print(success_msg)
                page.screenshot(path="after_renew.png")
                send_tg_photo("after_renew.png", success_msg)
            else:
                warn_msg = "⚠️ 成功进入目标站点页面，但未找到续期按钮，可能服务已是最新状态或未过期。"
                print(warn_msg)
                page.screenshot(path="no_renew_needed.png")
                send_tg_photo("no_renew_needed.png", warn_msg)

        except Exception as e:
            error_msg = f"💥 发生异常: {e}"
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
    if not USERNAME or not PASSWORD:
        print("❌ 错误: 环境变量 PURATYA_USER 或 PURATYA_PASS 未设置！")
        sys.exit(1)
    run()
