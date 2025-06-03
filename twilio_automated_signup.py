"""
Automated Twilio Account Creation via Puppeteer
Handles signup, phone verification, and credential extraction
"""

import asyncio
import json
from playwright.async_api import async_playwright

class TwilioAutomatedSignup:
    """Automated Twilio signup with phone verification handling"""
    
    def __init__(self, email="bwatson@ragleinc.com"):
        self.email = email
        self.credentials = {}
        
    async def create_twilio_account(self):
        """Automated Twilio account creation"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Visible for phone verification
            page = await browser.new_page()
            
            try:
                print("🚀 Starting automated Twilio signup...")
                
                # Navigate to Twilio signup
                await page.goto('https://www.twilio.com/try-twilio')
                
                # Fill signup form
                print("📝 Filling signup form...")
                await page.fill('input[name="email"]', self.email)
                await page.fill('input[name="password"]', 'Traxovo_2025!')
                await page.fill('input[name="firstName"]', 'Brett')
                await page.fill('input[name="lastName"]', 'Watson')
                
                # Submit form
                await page.click('button[type="submit"]')
                await page.wait_for_load_state('networkidle')
                
                print("📱 Phone verification required - please complete on screen")
                print("⏳ Waiting for phone verification...")
                
                # Wait for user to complete phone verification
                await page.wait_for_url('**/console**', timeout=300000)  # 5 minute timeout
                
                print("✅ Phone verification completed")
                print("🔑 Extracting credentials...")
                
                # Extract Account SID
                account_sid_element = await page.query_selector('[data-test="account-sid"]')
                if account_sid_element:
                    self.credentials['TWILIO_ACCOUNT_SID'] = await account_sid_element.inner_text()
                
                # Extract Auth Token
                auth_token_element = await page.query_selector('[data-test="auth-token"]')
                if auth_token_element:
                    self.credentials['TWILIO_AUTH_TOKEN'] = await auth_token_element.inner_text()
                
                # Get phone number from console
                await page.goto('https://console.twilio.com/us1/develop/phone-numbers/manage/incoming')
                await page.wait_for_load_state('networkidle')
                
                phone_element = await page.query_selector('[data-testid="phone-number"]')
                if phone_element:
                    self.credentials['TWILIO_PHONE_NUMBER'] = await phone_element.inner_text()
                
                print("🎉 Credentials extracted successfully!")
                return self.credentials
                
            except Exception as e:
                print(f"❌ Error during signup: {e}")
                return None
                
            finally:
                await browser.close()
    
    def save_credentials_to_env(self):
        """Save credentials for immediate use"""
        if self.credentials:
            with open('.env', 'a') as f:
                for key, value in self.credentials.items():
                    f.write(f"{key}={value}\n")
            print("💾 Credentials saved to .env file")

async def run_twilio_signup():
    """Run the automated Twilio signup process"""
    signup = TwilioAutomatedSignup()
    credentials = await signup.create_twilio_account()
    
    if credentials:
        signup.save_credentials_to_env()
        print("\n🔑 Your Twilio Credentials:")
        for key, value in credentials.items():
            print(f"{key}: {value}")
        return credentials
    else:
        print("❌ Signup failed")
        return None

if __name__ == "__main__":
    asyncio.run(run_twilio_signup())