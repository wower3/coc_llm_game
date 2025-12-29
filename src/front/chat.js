/**
 * COC 对话模块
 * 独立的前端模块，用于与 chat_api.py (端口5002) 通信
 * 与已有功能完全隔离
 */

const ChatModule = {
    // 配置
    CHAT_API_URL: 'http://localhost:5782/chat',
    LAUNCHER_URL: 'http://localhost:5781/launcher',

    // 状态
    chatOnline: false,
    chatLoading: false,
    chatEnabled: false,  // 对话功能是否启用
    isWaitingResponse: false,  // 是否正在等待AI回复

    /**
     * 检查对话服务状态
     * @returns {Promise<boolean>}
     */
    async checkStatus() {
        try {
            const response = await fetch(`${this.CHAT_API_URL}/health`, {
                method: 'GET',
                signal: AbortSignal.timeout(3000)
            });
            const result = await response.json();
            this.chatOnline = result.success && result.agent_ready;
            return this.chatOnline;
        } catch (error) {
            this.chatOnline = false;
            return false;
        }
    },

    /**
     * 初始化 Agent
     * @returns {Promise<{success: boolean, message?: string, error?: string}>}
     */
    async initAgent() {
        this.chatLoading = true;
        try {
            console.log('[ChatModule] 正在初始化Agent, URL:', `${this.CHAT_API_URL}/init`);
            const response = await fetch(`${this.CHAT_API_URL}/init`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            console.log('[ChatModule] 响应状态:', response.status);
            const result = await response.json();
            console.log('[ChatModule] 响应内容:', result);
            if (result.success) {
                this.chatOnline = true;
            }
            return result;
        } catch (error) {
            console.error('[ChatModule] initAgent错误:', error);
            return { success: false, error: '无法连接到对话服务: ' + error.message };
        } finally {
            this.chatLoading = false;
        }
    },

    /**
     * 发送消息到 Agent（流式输出）
     * @param {string} message - 用户消息
     * @param {function} onToken - 每收到一个token时的回调函数
     * @param {function} onComplete - 完成时的回调函数
     * @param {function} onError - 错误时的回调函数
     * @returns {Promise<void>}
     */
    async sendMessage(message, onToken, onComplete, onError) {
        if (!message || !message.trim()) {
            onError && onError('消息不能为空');
            return;
        }

        if (!this.chatOnline) {
            onError && onError('对话服务未连接');
            return;
        }

        this.isWaitingResponse = true;
        try {
            const response = await fetch(`${this.CHAT_API_URL}/send`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message.trim() })
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullResponse = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                // 解析 SSE 格式: "data: xxx\n\n"
                const lines = chunk.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const content = line.slice(6);
                        if (content === '[DONE]') {
                            onComplete && onComplete(fullResponse);
                        } else if (content.startsWith('[ERROR]')) {
                            onError && onError(content.slice(8));
                        } else {
                            fullResponse += content;
                            onToken && onToken(content);
                        }
                    }
                }
            }
        } catch (error) {
            onError && onError('发送消息失败: ' + error.message);
        } finally {
            this.isWaitingResponse = false;
        }
    },

    /**
     * 重置所有记忆（包括所有线程的历史）
     * @returns {Promise<{success: boolean, message?: string, error?: string}>}
     */
    async resetAllMemory() {
        this.chatLoading = true;
        try {
            const response = await fetch(`${this.CHAT_API_URL}/reset-all`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const result = await response.json();
            return result;
        } catch (error) {
            return { success: false, error: '重置记忆失败: ' + error.message };
        } finally {
            this.chatLoading = false;
        }
    },

    /**
     * 获取场景信息
     * @returns {Promise<{success: boolean, scene_path?: string, scene_depth?: number, in_scene?: boolean, error?: string}>}
     */
    async getSceneInfo() {
        try {
            const response = await fetch(`${this.CHAT_API_URL}/scene`, {
                method: 'GET'
            });
            return await response.json();
        } catch (error) {
            return { success: false, error: '获取场景信息失败' };
        }
    },

    /**
     * 启用对话功能
     */
    enable() {
        this.chatEnabled = true;
    },

    /**
     * 禁用对话功能
     */
    disable() {
        this.chatEnabled = false;
    },

    /**
     * 切换对话功能状态
     * @returns {boolean} 新的状态
     */
    toggle() {
        this.chatEnabled = !this.chatEnabled;
        return this.chatEnabled;
    },

    /**
     * 获取系统日志
     * @returns {Promise<{success: boolean, logs?: array, error?: string}>}
     */
    async getLogs() {
        try {
            const response = await fetch(`${this.CHAT_API_URL}/logs`);
            return await response.json();
        } catch (error) {
            return { success: false, error: '获取日志失败' };
        }
    },

    /**
     * 清空系统日志
     * @returns {Promise<{success: boolean, error?: string}>}
     */
    async clearLogs() {
        try {
            const response = await fetch(`${this.CHAT_API_URL}/logs/clear`, {
                method: 'POST'
            });
            return await response.json();
        } catch (error) {
            return { success: false, error: '清空日志失败' };
        }
    },

    /**
     * 启动对话服务
     * @returns {Promise<{success: boolean, message?: string, error?: string}>}
     */
    async startService() {
        try {
            console.log('[ChatModule] 正在启动服务, URL:', `${this.LAUNCHER_URL}/start`);
            const response = await fetch(`${this.LAUNCHER_URL}/start`, {
                method: 'POST'
            });
            console.log('[ChatModule] startService响应状态:', response.status);
            const result = await response.json();
            console.log('[ChatModule] startService响应内容:', result);
            return result;
        } catch (error) {
            console.error('[ChatModule] startService错误:', error);
            return { success: false, error: '无法连接管理服务: ' + error.message };
        }
    },

    /**
     * 停止对话服务
     * @returns {Promise<{success: boolean, message?: string, error?: string}>}
     */
    async stopService() {
        try {
            const response = await fetch(`${this.LAUNCHER_URL}/stop`, {
                method: 'POST'
            });
            return await response.json();
        } catch (error) {
            return { success: false, error: '无法连接管理服务' };
        }
    }
};

// 导出模块（兼容不同环境）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChatModule;
}
