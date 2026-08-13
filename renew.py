from playwright.sync_api import sync_playwright
import time

# ================= 配置区域 =================
LOGIN_URL = "https://cloud.puratya.com/login" # 假设的登录页面，请根据实际情况修改
DASHBOARD_URL = "https://cloud.puratya.com/web" # 登录后的面板页面
USERNAME = "your_email@example.com"
PASSWORD = "your_password"
# ============================================

def auto_renew_via_browser():
    print("启动无头浏览器...")
    with sync_playwright() as p:
        # 启动浏览器 (headless=True 表示不显示界面在后台运行)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            # 1. 访问登录页
            print("正在访问登录页面...")
            page.goto(LOGIN_URL, timeout=30000)
            
            # 2. 执行登录操作 (需根据实际网页的元素定位修改选择器)
            # 以下选择器为示例，请按F12审查元素获取真实的 input name 或 id
            page.fill('input[type="email"]', USERNAME)
            page.fill('input[type="password"]', PASSWORD)
            page.click('button[type="submit"]')
            
            print("登录请求已发送，等待页面跳转...")
            # 3. 等待面板加载完成 (等待出现 image_7beadb.png 中的特征元素)
            page.wait_for_url("**/web*", timeout=20000)
            time.sleep(5) # 额外等待动态数据(如SLEEP IN 倒计时)渲染完毕
            
            # 4. 定位并点击“续期”按钮
            # 这里的匹配文本 "续期" 必须与面板上的文字完全一致
            renew_button = page.locator('button:has-text("续期")')
            
            if renew_button.count() > 0:
                # 遍历所有找到的续期按钮（以防有多个服务）并点击
                for i in range(renew_button.count()):
                    print(f"正在点击第 {i+1} 个续期按钮...")
                    renew_button.nth(i).click()
                    time.sleep(3) # 点击后的缓冲时间
                print("✅ 续期操作执行完毕。")
            else:
                print("❌ 未在页面上找到包含“续期”文本的按钮，请检查选择器或页面语言。")

        except Exception as e:
            print(f"⚠️ 执行过程中出现错误: {e}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    auto_renew_via_browser()
