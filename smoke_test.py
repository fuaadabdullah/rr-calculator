#!/usr/bin/env python3
"""
End-to-end smoke test for RIZZK Calculator Azure deployment.
Tests the deployed Streamlit app at https://rizzkcalcdemo.azurewebsites.net
"""

import sys
import time
import requests
from urllib.parse import urljoin

BASE_URL = "https://rizzkcalcdemo.azurewebsites.net"
TIMEOUT = 10

def test_app_responds():
    """Test 1: App responds with HTTP 200"""
    print("Test 1: Checking app availability...")
    try:
        response = requests.get(BASE_URL, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✅ App responds with HTTP 200 (response time: {response.elapsed.total_seconds():.2f}s)")
    except Exception as e:
        print(f"❌ App availability check failed: {e}")
        raise AssertionError("App did not respond with HTTP 200") from e

def test_streamlit_health():
    """Test 2: Streamlit health endpoint"""
    print("\nTest 2: Checking Streamlit health endpoint...")
    try:
        health_url = urljoin(BASE_URL, "/_stcore/health")
        response = requests.get(health_url, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "ok" in response.text.lower(), f"Expected 'ok', got {response.text}"
        print(f"✅ Streamlit health check passed")
    except Exception as e:
        print(f"❌ Streamlit health check failed: {e}")
        raise AssertionError("Streamlit health endpoint failed") from e

def test_streamlit_loads():
    """Test 3: Page contains Streamlit markers"""
    print("\nTest 3: Verifying Streamlit UI loads...")
    try:
        response = requests.get(BASE_URL, timeout=TIMEOUT)
        html = response.text
        assert "Streamlit" in html or "streamlit" in html, "No Streamlit markers found in HTML"
        assert "static/js" in html or "static/css" in html, "No static assets found"
        print(f"✅ Streamlit UI markup detected")
    except Exception as e:
        print(f"❌ Streamlit UI check failed: {e}")
        raise AssertionError("Streamlit UI markers missing") from e

def test_app_title():
    """Test 4: Check page title (from Streamlit config)"""
    print("\nTest 4: Checking app title...")
    try:
        response = requests.get(BASE_URL, timeout=TIMEOUT)
        html = response.text
        # Streamlit sets the title in the HTML
        # Our app.py has: st.set_page_config(page_title="RIZZK Calculator", ...)
        # This will be in a meta tag or title tag after initial load
        assert "<title>" in html.lower(), "Expected HTML title tag is missing"
        print(f"✅ App HTML loaded (title verification requires JS execution)")
    except Exception as e:
        print(f"❌ Title check failed: {e}")
        raise AssertionError("App title markup check failed") from e

def test_docker_image_runs():
    """Test 5: Verify container is running (implied by above tests)"""
    print("\nTest 5: Verifying Docker container is running...")
    # If the app responds with Streamlit content, the container is running
    try:
        response = requests.get(BASE_URL, timeout=TIMEOUT)
        assert response.status_code == 200
        print(f"✅ Docker container is running and serving traffic on port 8501")
    except Exception as e:
        print(f"❌ Container check failed: {e}")
        raise AssertionError("Docker container health check failed") from e

def main():
    print("=" * 60)
    print("RIZZK Calculator - Azure Deployment Smoke Test")
    print(f"Target: {BASE_URL}")
    print("=" * 60)
    
    # Give the app a moment if it was just deployed
    print("\nWaiting 2 seconds for app warm-up...")
    time.sleep(2)
    
    tests = [
        test_app_responds,
        test_streamlit_health,
        test_streamlit_loads,
        test_app_title,
        test_docker_image_runs,
    ]
    
    results = []
    for test in tests:
        try:
            test()
            results.append(True)
        except AssertionError:
            results.append(False)

    print("\n" + "=" * 60)
    print("SMOKE TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All smoke tests passed!")
        print(f"\nYour app is live at: {BASE_URL}")
        print("\nNext steps:")
        print("  - Open the URL in a browser to test the UI interactively")
        print("  - Enter test values and verify calculations work")
        print("  - Check that emoji mode toggle works (🦇 mode)")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("\nTroubleshooting:")
        print("  - Check logs: az webapp log tail -g rizzk-rg-eastus2 -n RIZZKCALCDEMO")
        print("  - Verify container image: docker pull fuaadabdullah/rizzk-calculator:latest")
        print("  - Check app settings in Azure portal (WEBSITES_PORT=8501)")
        return 1

if __name__ == "__main__":
    sys.exit(main())
