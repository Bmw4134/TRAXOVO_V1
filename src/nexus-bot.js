/**
 * NEXUS Bot - Primary Headless Browser Handler
 * AI-to-AI communication loop with DOM injection and response harvesting
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const axios = require('axios');

class NexusBot {
    constructor(config) {
        this.config = config;
        this.browser = null;
        this.pages = {};
        this.sessions = {};
        this.logs = [];
        this.activeLoops = new Map();
    }

    async initialize() {
        console.log('[NEXUS] Initializing headless browser handler...');
        
        this.browser = await puppeteer.launch({
            headless: 'new',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        });

        await this.createLogDirectory();
        console.log('[NEXUS] Browser initialized successfully');
        return true;
    }

    async createLogDirectory() {
        const logDir = path.join(__dirname, '../logs');
        if (!fs.existsSync(logDir)) {
            fs.mkdirSync(logDir, { recursive: true });
        }
    }

    async startAICommLoop(sessionId, initialPrompt) {
        console.log(`[NEXUS] Starting AI communication loop: ${sessionId}`);
        
        const loopSession = {
            id: sessionId,
            status: 'active',
            startTime: new Date(),
            messages: [],
            responses: [],
            currentAgent: 'chatgpt'
        };

        this.activeLoops.set(sessionId, loopSession);

        try {
            // Step 1: Send to ChatGPT
            const chatgptResponse = await this.sendToChatGPT(initialPrompt, sessionId);
            loopSession.responses.push({
                agent: 'chatgpt',
                response: chatgptResponse,
                timestamp: new Date()
            });

            // Step 2: Send ChatGPT response to Perplexity
            const perplexityResponse = await this.sendToPerplexity(chatgptResponse.content, sessionId);
            loopSession.responses.push({
                agent: 'perplexity',
                response: perplexityResponse,
                timestamp: new Date()
            });

            // Step 3: Send combined response to Replit Agent
            const replitResponse = await this.sendToReplitAgent({
                chatgpt_response: chatgptResponse.content,
                perplexity_response: perplexityResponse.content,
                session_id: sessionId
            });
            loopSession.responses.push({
                agent: 'replit',
                response: replitResponse,
                timestamp: new Date()
            });

            loopSession.status = 'completed';
            await this.saveSessionLog(loopSession);

            return {
                success: true,
                sessionId: sessionId,
                responses: loopSession.responses,
                loopDuration: new Date() - loopSession.startTime
            };

        } catch (error) {
            console.error(`[NEXUS] AI loop error: ${error.message}`);
            loopSession.status = 'error';
            loopSession.error = error.message;
            await this.saveSessionLog(loopSession);
            
            // Trigger DAVE_LAYER fallback
            await this.triggerDaveLayer(sessionId, error);
            
            return {
                success: false,
                sessionId: sessionId,
                error: error.message,
                fallback: 'dave_layer_activated'
            };
        }
    }

    async sendToChatGPT(prompt, sessionId) {
        console.log(`[NEXUS] Sending to ChatGPT: ${sessionId}`);
        
        const startTime = Date.now();
        
        try {
            const response = await axios.post('https://api.openai.com/v1/chat/completions', {
                model: 'gpt-4o',
                messages: [
                    {
                        role: 'system',
                        content: 'You are part of the NEXUS AI relay network. Provide comprehensive responses that will be passed to other AI agents in the chain.'
                    },
                    {
                        role: 'user',
                        content: prompt
                    }
                ],
                max_tokens: 1000,
                temperature: 0.7
            }, {
                headers: {
                    'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
                    'Content-Type': 'application/json'
                }
            });

            const responseTime = Date.now() - startTime;
            
            this.logPerformance('chatgpt', responseTime, 'success');
            
            return {
                content: response.data.choices[0].message.content,
                responseTime: responseTime,
                tokens: response.data.usage.total_tokens
            };

        } catch (error) {
            const responseTime = Date.now() - startTime;
            this.logPerformance('chatgpt', responseTime, 'error');
            throw new Error(`ChatGPT API error: ${error.message}`);
        }
    }

    async sendToPerplexity(prompt, sessionId) {
        console.log(`[NEXUS] Sending to Perplexity: ${sessionId}`);
        
        const startTime = Date.now();
        
        try {
            const response = await axios.post('https://api.perplexity.ai/chat/completions', {
                model: 'llama-3.1-sonar-small-128k-online',
                messages: [
                    {
                        role: 'system',
                        content: 'You are part of the NEXUS AI relay network. Analyze and expand on the provided information with real-time search capabilities.'
                    },
                    {
                        role: 'user',
                        content: prompt
                    }
                ],
                max_tokens: 1000,
                temperature: 0.2,
                search_domain_filter: ['perplexity.ai'],
                return_images: false,
                return_related_questions: false
            }, {
                headers: {
                    'Authorization': `Bearer ${process.env.PERPLEXITY_API_KEY}`,
                    'Content-Type': 'application/json'
                }
            });

            const responseTime = Date.now() - startTime;
            
            this.logPerformance('perplexity', responseTime, 'success');
            
            return {
                content: response.data.choices[0].message.content,
                responseTime: responseTime,
                citations: response.data.citations || []
            };

        } catch (error) {
            const responseTime = Date.now() - startTime;
            this.logPerformance('perplexity', responseTime, 'error');
            
            // If Perplexity fails, return a processed version of the ChatGPT response
            return {
                content: `Processed analysis: ${prompt}`,
                responseTime: responseTime,
                fallback: true,
                error: error.message
            };
        }
    }

    async sendToReplitAgent(payload) {
        console.log(`[NEXUS] Sending to Replit Agent: ${payload.session_id}`);
        
        const startTime = Date.now();
        
        try {
            const response = await axios.post('http://localhost:5000/api/nexus_infinity/solve', {
                problem: `Process and analyze this AI relay chain response`,
                context: {
                    chatgpt_response: payload.chatgpt_response,
                    perplexity_response: payload.perplexity_response,
                    session_id: payload.session_id,
                    relay_chain: true
                }
            }, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const responseTime = Date.now() - startTime;
            
            this.logPerformance('replit', responseTime, 'success');
            
            return {
                content: response.data,
                responseTime: responseTime,
                local_processing: true
            };

        } catch (error) {
            const responseTime = Date.now() - startTime;
            this.logPerformance('replit', responseTime, 'error');
            throw new Error(`Replit Agent error: ${error.message}`);
        }
    }

    logPerformance(agent, responseTime, status) {
        const logEntry = {
            agent: agent,
            responseTime: responseTime,
            status: status,
            timestamp: new Date().toISOString()
        };
        
        this.logs.push(logEntry);
        console.log(`[NEXUS] ${agent.toUpperCase()} - ${responseTime}ms - ${status.toUpperCase()}`);
    }

    async saveSessionLog(session) {
        const logFile = path.join(__dirname, '../logs', `session_${session.id}.json`);
        
        const logData = {
            ...session,
            performanceLogs: this.logs.filter(log => 
                log.timestamp >= session.startTime.toISOString()
            )
        };
        
        fs.writeFileSync(logFile, JSON.stringify(logData, null, 2));
        console.log(`[NEXUS] Session log saved: ${logFile}`);
    }

    async triggerDaveLayer(sessionId, error) {
        console.log(`[NEXUS] Triggering DAVE_LAYER for session: ${sessionId}`);
        
        try {
            await axios.post('http://localhost:5000/api/dave_mode/activate', {
                session_id: sessionId,
                error: error.message,
                triggered_by: 'nexus_bot'
            });
            
            console.log('[NEXUS] DAVE_LAYER activated successfully');
        } catch (daveError) {
            console.error(`[NEXUS] DAVE_LAYER activation failed: ${daveError.message}`);
        }
    }

    async getSessionStatus(sessionId) {
        return this.activeLoops.get(sessionId) || null;
    }

    async getAllSessions() {
        return Array.from(this.activeLoops.values());
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
            console.log('[NEXUS] Browser cleanup completed');
        }
    }
}

module.exports = NexusBot;