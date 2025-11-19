#!/usr/bin/env python3
"""
Automated screenshot capture for RIZZK Calculator
Captures multiple views of the live app for portfolio/media use
"""

import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    """Setup Chrome WebDriver with headless mode for automation"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in background
    options.add_argument('--window-size=1920,1080')  # Standard desktop size
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def capture_screenshots():
    """Main function to capture screenshots"""
    driver = setup_driver()
    url = "https://rizzk-calculator-demo-eus2-f1.azurewebsites.net"

    try:
        print("🚀 Opening RIZZK Calculator...")
        driver.get(url)

        # Wait for page to load - look for Streamlit app container
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # Additional wait for Streamlit to fully render
        time.sleep(3)

        # Create media directory if it doesn't exist
        media_dir = os.path.join(os.path.dirname(__file__), "media")
        os.makedirs(media_dir, exist_ok=True)

        # 1. Initial load screenshot
        print("📸 Capturing initial view...")
        driver.save_screenshot(os.path.join(media_dir, "01_initial_load.png"))

        # 2. Scroll down to see more content
        print("📜 Scrolling to show more content...")
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)
        driver.save_screenshot(os.path.join(media_dir, "02_scrolled_view.png"))

        # 3. Scroll to bottom to see footer
        print("� Scrolling to bottom...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.save_screenshot(os.path.join(media_dir, "03_full_page.png"))

        # 4. Try to expand trading strategies section if visible
        print("📚 Attempting to expand trading strategies...")
        try:
            # Look for any clickable element that might expand content
            expanders = driver.find_elements(By.XPATH, "//div[contains(@class, 'expander')] | //button | //div[contains(text(), 'Trading')]")
            if expanders:
                expanders[0].click()
                time.sleep(2)
                driver.save_screenshot(os.path.join(media_dir, "04_expanded_content.png"))
        except Exception as e:
            print(f"⚠️ Could not expand content: {e}")

        # 5. Mobile view screenshot
        print("📱 Capturing mobile view...")
        driver.set_window_size(375, 667)  # iPhone size
        time.sleep(1)
        driver.save_screenshot(os.path.join(media_dir, "05_mobile_view.png"))

        # 6. Tablet view screenshot
        print("📱 Capturing tablet view...")
        driver.set_window_size(768, 1024)  # iPad size
        time.sleep(1)
        driver.save_screenshot(os.path.join(media_dir, "06_tablet_view.png"))

        print("✅ All screenshots captured successfully!")
        print(f"📁 Screenshots saved to: {media_dir}")

        # List captured files
        files = os.listdir(media_dir)
        for file in sorted(files):
            if file.endswith('.png'):
                print(f"  • {file}")

    except Exception as e:
        print(f"❌ Error during screenshot capture: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()

if __name__ == "__main__":
    capture_screenshots()
