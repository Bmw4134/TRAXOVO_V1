#!/usr/bin/env node

/**
 * Infinity Sync Injector - Node.js App Patch Launcher
 * Voice-triggered logic listener with backend command parser
 */

const fs = require('fs');
const path = require('path');
const { spawn, exec } = require('child_process');

class AppPatchLauncher {
    constructor() {
        this.directivesFile = 'nexus_directives.json';
        this.isRunning = false;
        this.voiceListener = null;
        this.setupCommands();
    }

    setupCommands() {
        this.commands = {
            'self-heal': {
                description: 'Automatically detect and fix system issues',
                action: () => this.executeVoiceCommand('nexus self heal')
            },
            'upgrade-dashboard': {
                description: 'Upgrade dashboard with latest features',
                action: () => this.executeVoiceCommand('upgrade dashboard')
            },
            'shrink-file-size': {
                description: 'Optimize file sizes and clean up storage',
                action: () => this.executeVoiceCommand('shrink file size')
            },
            'trade-execution': {
                description: 'Execute trading operations through Nexus',
                action: (symbol, action, quantity) => this.executeVoiceCommand(`${action} ${quantity} shares of ${symbol}`)
            },
            'platform-overview': {
                description: 'Display comprehensive platform overview',
                action: () => this.executeVoiceCommand('platform overview')
            },
            'status': {
                description: 'Show system status and active processes',
                action: () => this.showStatus()
            },
            'help': {
                description: 'Show available commands',
                action: () => this.showHelp()
            }
        };
    }

    async start() {
        console.log('🚀 Infinity Sync Injector - App Patch Launcher Starting...');
        console.log('📡 Voice-triggered logic listener initializing...');
        
        this.isRunning = true;
        
        // Ensure Python backend is running
        await this.ensureBackendRunning();
        
        // Initialize voice command processor
        this.initializeVoiceProcessor();
        
        // Start command listener
        this.startCommandListener();
        
        console.log('✅ Infinity Sync Injector is now active');
        console.log('🎤 Voice commands are ready');
        console.log('💬 Type "help" for available commands or speak naturally');
        console.log('---');
    }

    async ensureBackendRunning() {
        return new Promise((resolve) => {
            exec('curl -s http://localhost:5000/api/infinity/commands', (error, stdout, stderr) => {
                if (error) {
                    console.log('⚠️  Backend not responding, attempting to start...');
                    this.startPythonBackend();
                } else {
                    console.log('✅ Backend is running and responsive');
                }
                resolve();
            });
        });
    }

    startPythonBackend() {
        const pythonProcess = spawn('python', ['main.py'], {
            stdio: 'inherit',
            detached: false
        });

        pythonProcess.on('spawn', () => {
            console.log('✅ Python backend started');
        });

        pythonProcess.on('error', (error) => {
            console.log('❌ Error starting Python backend:', error.message);
        });
    }

    initializeVoiceProcessor() {
        // Initialize voice command processing system
        console.log('🔧 Initializing voice command processor...');
        
        // Set up voice command patterns
        this.voicePatterns = [
            /nexus\s+(self\s+heal|repair)/i,
            /upgrade\s+dashboard/i,
            /(shrink|optimize)\s+(file\s+size|storage)/i,
            /(buy|sell)\s+(\d+)\s+(shares?\s+of\s+)?([A-Z]{3,5})/i,
            /platform\s+(overview|status)/i,
            /(execute|make)\s+trade/i
        ];
        
        console.log('✅ Voice processor initialized');
    }

    startCommandListener() {
        const readline = require('readline');
        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout,
            prompt: 'Infinity> '
        });

        rl.prompt();

        rl.on('line', async (input) => {
            const command = input.trim().toLowerCase();
            
            if (command === 'exit' || command === 'quit') {
                console.log('👋 Infinity Sync Injector shutting down...');
                this.isRunning = false;
                rl.close();
                process.exit(0);
            }
            
            await this.processCommand(input.trim());
            rl.prompt();
        });

        rl.on('close', () => {
            console.log('👋 Goodbye!');
            process.exit(0);
        });
    }

    async processCommand(input) {
        // Check for direct commands first
        if (this.commands[input]) {
            await this.commands[input].action();
            return;
        }

        // Process as voice command
        await this.executeVoiceCommand(input);
    }

    async executeVoiceCommand(voiceInput) {
        try {
            console.log(`🎤 Processing: "${voiceInput}"`);
            
            const response = await this.makeAPICall('/api/infinity/voice-command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    voice_input: voiceInput
                })
            });

            if (response.success) {
                this.displayDirectiveResult(response.directive_result);
                this.logDirective(response.directive_result);
            } else {
                console.log('❌ Command failed:', response.error);
            }
        } catch (error) {
            console.log('❌ Error processing command:', error.message);
        }
    }

    displayDirectiveResult(result) {
        console.log('---');
        
        if (result.success) {
            console.log(`✅ Command executed successfully`);
            console.log(`📋 Directive ID: ${result.directive_id}`);
            console.log(`⚡ Command: ${result.command}`);
            
            if (result.execution_time) {
                console.log(`⏱️  Execution time: ${result.execution_time.toFixed(2)}s`);
            }
            
            if (result.result) {
                console.log('📊 Result:', JSON.stringify(result.result, null, 2));
            }
        } else {
            console.log(`❌ Command failed: ${result.error}`);
            if (result.directive_id) {
                console.log(`📋 Directive ID: ${result.directive_id}`);
            }
        }
        
        console.log('---');
    }

    logDirective(directive) {
        // Additional logging to console for immediate feedback
        const timestamp = new Date().toLocaleString();
        console.log(`📝 Logged directive at ${timestamp}`);
    }

    async makeAPICall(endpoint, options = {}) {
        const https = require('https');
        const http = require('http');
        
        return new Promise((resolve, reject) => {
            const url = `http://localhost:5000${endpoint}`;
            const protocol = url.startsWith('https:') ? https : http;
            
            const requestOptions = {
                method: options.method || 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Cookie': 'session=demo_session', // Demo session for testing
                    ...options.headers
                }
            };

            const req = protocol.request(url, requestOptions, (res) => {
                let data = '';
                
                res.on('data', (chunk) => {
                    data += chunk;
                });
                
                res.on('end', () => {
                    try {
                        const response = JSON.parse(data);
                        resolve(response);
                    } catch (error) {
                        reject(new Error('Invalid JSON response'));
                    }
                });
            });

            req.on('error', (error) => {
                reject(error);
            });

            if (options.body) {
                req.write(options.body);
            }

            req.end();
        });
    }

    async showStatus() {
        try {
            console.log('📊 System Status Check...');
            
            const [commandsResponse, directivesResponse] = await Promise.all([
                this.makeAPICall('/api/infinity/commands'),
                this.makeAPICall('/api/infinity/directives?limit=5')
            ]);

            console.log('---');
            console.log('🎤 Voice Commands Available:', commandsResponse.commands?.total_commands || 0);
            console.log('📋 Recent Directives:', directivesResponse.directives?.length || 0);
            
            if (directivesResponse.directives && directivesResponse.directives.length > 0) {
                console.log('\n📝 Last 5 Directives:');
                directivesResponse.directives.forEach((directive, index) => {
                    const timestamp = new Date(directive.timestamp).toLocaleTimeString();
                    console.log(`  ${index + 1}. ${directive.command} (${directive.status}) - ${timestamp}`);
                });
            }
            
            console.log('---');
        } catch (error) {
            console.log('❌ Status check failed:', error.message);
        }
    }

    showHelp() {
        console.log('---');
        console.log('🎤 Infinity Sync Injector - Voice Commands:');
        console.log('');
        
        console.log('Direct Commands:');
        Object.entries(this.commands).forEach(([cmd, config]) => {
            console.log(`  ${cmd.padEnd(20)} - ${config.description}`);
        });
        
        console.log('');
        console.log('Voice Commands (speak naturally):');
        console.log('  "nexus self heal"           - Automatically fix system issues');
        console.log('  "upgrade dashboard"         - Enhance dashboard features');
        console.log('  "shrink file size"          - Optimize storage and cleanup');
        console.log('  "buy 100 shares of AAPL"    - Execute stock trades');
        console.log('  "platform overview"         - Show system status');
        console.log('');
        console.log('Navigation:');
        console.log('  exit/quit                   - Shutdown Infinity Sync');
        console.log('---');
    }
}

// Main execution
if (require.main === module) {
    const launcher = new AppPatchLauncher();
    
    // Handle graceful shutdown
    process.on('SIGINT', () => {
        console.log('\n🛑 Received interrupt signal');
        console.log('👋 Infinity Sync Injector shutting down...');
        process.exit(0);
    });
    
    process.on('uncaughtException', (error) => {
        console.error('❌ Uncaught Exception:', error);
        process.exit(1);
    });
    
    // Start the application
    launcher.start().catch((error) => {
        console.error('❌ Failed to start Infinity Sync Injector:', error);
        process.exit(1);
    });
}

module.exports = AppPatchLauncher;