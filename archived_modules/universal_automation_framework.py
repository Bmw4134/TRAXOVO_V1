"""
Universal Automation Framework
Easy-to-use workflow automation with simple configuration
"""

import asyncio
import json
import os
from typing import Dict, List, Any, Optional
from playwright.async_api import async_playwright
from dataclasses import dataclass
import yaml

@dataclass
class AutomationStep:
    """Single automation step configuration"""
    action: str  # click, fill, navigate, wait, extract, etc.
    selector: str = ""
    value: str = ""
    timeout: int = 30000
    description: str = ""
    optional: bool = False

@dataclass
class AutomationWorkflow:
    """Complete workflow configuration"""
    name: str
    description: str
    start_url: str
    steps: List[AutomationStep]
    output_variables: List[str] = None
    headless: bool = False
    
class UniversalAutomationEngine:
    """User-friendly automation engine for any workflow"""
    
    def __init__(self):
        self.results = {}
        self.browser = None
        self.page = None
        
    async def run_workflow(self, workflow: AutomationWorkflow) -> Dict[str, Any]:
        """Execute a complete automation workflow"""
        async with async_playwright() as p:
            self.browser = await p.chromium.launch(headless=workflow.headless)
            self.page = await self.browser.new_page()
            
            try:
                print(f"🚀 Starting workflow: {workflow.name}")
                print(f"📝 {workflow.description}")
                
                # Navigate to starting URL
                await self.page.goto(workflow.start_url)
                await self.page.wait_for_load_state('networkidle')
                
                # Execute each step
                for i, step in enumerate(workflow.steps, 1):
                    print(f"Step {i}: {step.description or step.action}")
                    success = await self._execute_step(step)
                    
                    if not success and not step.optional:
                        print(f"❌ Required step failed: {step.description}")
                        break
                        
                # Extract output variables if specified
                if workflow.output_variables:
                    await self._extract_outputs(workflow.output_variables)
                
                print("✅ Workflow completed successfully")
                return self.results
                
            except Exception as e:
                print(f"❌ Workflow failed: {e}")
                return {"error": str(e)}
                
            finally:
                await self.browser.close()
    
    async def _execute_step(self, step: AutomationStep) -> bool:
        """Execute a single automation step"""
        try:
            if step.action == "click":
                await self.page.click(step.selector, timeout=step.timeout)
                
            elif step.action == "fill":
                await self.page.fill(step.selector, step.value, timeout=step.timeout)
                
            elif step.action == "navigate":
                await self.page.goto(step.value)
                await self.page.wait_for_load_state('networkidle')
                
            elif step.action == "wait":
                await self.page.wait_for_selector(step.selector, timeout=step.timeout)
                
            elif step.action == "wait_url":
                await self.page.wait_for_url(step.value, timeout=step.timeout)
                
            elif step.action == "extract":
                element = await self.page.query_selector(step.selector)
                if element:
                    text = await element.inner_text()
                    self.results[step.value] = text.strip()
                    
            elif step.action == "extract_attribute":
                element = await self.page.query_selector(step.selector)
                if element:
                    attr_value = await element.get_attribute(step.value)
                    self.results[f"{step.selector}_{step.value}"] = attr_value
                    
            elif step.action == "sleep":
                await asyncio.sleep(int(step.value))
                
            elif step.action == "screenshot":
                await self.page.screenshot(path=step.value)
                
            return True
            
        except Exception as e:
            if step.optional:
                print(f"⚠️ Optional step failed: {e}")
                return True
            else:
                print(f"❌ Step failed: {e}")
                return False
    
    async def _extract_outputs(self, variables: List[str]):
        """Extract specified output variables"""
        for var in variables:
            if var not in self.results:
                # Try common selectors for the variable
                selectors = [
                    f'[data-testid="{var}"]',
                    f'#{var}',
                    f'.{var}',
                    f'[name="{var}"]'
                ]
                
                for selector in selectors:
                    try:
                        element = await self.page.query_selector(selector)
                        if element:
                            self.results[var] = await element.inner_text()
                            break
                    except:
                        continue

class WorkflowBuilder:
    """Helper class to build workflows easily"""
    
    @staticmethod
    def create_twilio_signup() -> AutomationWorkflow:
        """Pre-built Twilio signup workflow"""
        return AutomationWorkflow(
            name="Twilio Account Creation",
            description="Automated Twilio account signup with credential extraction",
            start_url="https://www.twilio.com/try-twilio",
            headless=False,  # Visible for phone verification
            steps=[
                AutomationStep("fill", 'input[name="email"]', "bwatson@ragleinc.com", description="Enter email"),
                AutomationStep("fill", 'input[name="password"]', "Traxovo_2025!", description="Enter password"),
                AutomationStep("fill", 'input[name="firstName"]', "Brett", description="Enter first name"),
                AutomationStep("fill", 'input[name="lastName"]', "Watson", description="Enter last name"),
                AutomationStep("click", 'button[type="submit"]', description="Submit signup form"),
                AutomationStep("wait_url", "**/console**", timeout=300000, description="Wait for phone verification"),
                AutomationStep("extract", '[data-test="account-sid"]', "TWILIO_ACCOUNT_SID", description="Extract Account SID"),
                AutomationStep("extract", '[data-test="auth-token"]', "TWILIO_AUTH_TOKEN", description="Extract Auth Token"),
                AutomationStep("navigate", "https://console.twilio.com/us1/develop/phone-numbers/manage/incoming", description="Go to phone numbers"),
                AutomationStep("extract", '[data-testid="phone-number"]', "TWILIO_PHONE_NUMBER", description="Extract phone number"),
            ],
            output_variables=["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"]
        )
    
    @staticmethod
    def create_custom_workflow(config_file: str) -> AutomationWorkflow:
        """Create workflow from YAML configuration file"""
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        steps = [
            AutomationStep(**step_config) 
            for step_config in config.get('steps', [])
        ]
        
        return AutomationWorkflow(
            name=config['name'],
            description=config['description'],
            start_url=config['start_url'],
            steps=steps,
            output_variables=config.get('output_variables', []),
            headless=config.get('headless', False)
        )

async def run_twilio_signup():
    """Run Twilio signup automation"""
    engine = UniversalAutomationEngine()
    workflow = WorkflowBuilder.create_twilio_signup()
    
    print("🔧 Starting automated Twilio account creation...")
    print("📱 You'll need to complete phone verification when prompted")
    
    results = await engine.run_workflow(workflow)
    
    if "error" not in results:
        print("\n🎉 Twilio account created successfully!")
        print("\n🔑 Your credentials:")
        for key, value in results.items():
            if key.startswith("TWILIO_"):
                print(f"{key}: {value}")
                
        # Save to environment
        save_credentials_to_env(results)
        
    return results

def save_credentials_to_env(credentials: Dict[str, str]):
    """Save credentials to .env file"""
    env_lines = []
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_lines = f.readlines()
    
    # Add new credentials
    for key, value in credentials.items():
        if key.startswith("TWILIO_") and value:
            env_lines.append(f"{key}={value}\n")
    
    with open('.env', 'w') as f:
        f.writelines(env_lines)
    
    print("💾 Credentials saved to .env file")

def create_sample_config():
    """Create a sample YAML configuration file"""
    sample_config = {
        'name': 'Sample Workflow',
        'description': 'Example automation workflow',
        'start_url': 'https://example.com',
        'headless': False,
        'steps': [
            {
                'action': 'fill',
                'selector': 'input[name="username"]',
                'value': 'your_username',
                'description': 'Enter username'
            },
            {
                'action': 'fill',
                'selector': 'input[name="password"]',
                'value': 'your_password',
                'description': 'Enter password'
            },
            {
                'action': 'click',
                'selector': 'button[type="submit"]',
                'description': 'Click login button'
            },
            {
                'action': 'wait',
                'selector': '.dashboard',
                'description': 'Wait for dashboard to load'
            },
            {
                'action': 'extract',
                'selector': '.user-name',
                'value': 'username',
                'description': 'Extract username from dashboard'
            }
        ],
        'output_variables': ['username']
    }
    
    with open('sample_workflow.yaml', 'w') as f:
        yaml.dump(sample_config, f, default_flow_style=False)
    
    print("📝 Sample configuration created: sample_workflow.yaml")

if __name__ == "__main__":
    # Run Twilio signup
    asyncio.run(run_twilio_signup())