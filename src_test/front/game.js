const { createApp } = Vue;

// API 配置
const API_BASE_URL = 'http://localhost:5780/api';
const AUTH_BASE_URL = 'http://localhost:5780/auth';

const App = {
    data() {
        return {
            // API 配置
            apiBaseUrl: API_BASE_URL,
            playerId: '',
            playerIdInput: '',
            isLoading: false,
            errorMsg: '',

            // 登录状态
            isLoggedIn: false,
            playerFound: false,
            authToken: null,

            // 对话服务状态
            chatOnline: false,
            chatLoading: false,
            chatEnabled: false,
            isWaitingAI: false,

            // 日志相关
            logsVisible: false,
            logs: [],

            // 面板宽度
            leftPanelWidth: 290,
            rightPanelWidth: 300,
            optionsPanelHeight: 200,
            isResizing: false,
            resizeType: null,

            // 折叠面板状态
            sections: {
                attrs: true,    // 基础属性默认展开
                skills: true    // 技能列表默认展开
            },

            // 当前章节和场景
            currentChapter: '第一章',
            currentScene: '场景1',
            currentSceneName: '主线程',
            sceneDepth: 0,  // 场景深度
            availableScenes: [],  // 可用的场景选择列表

            // 玩家输入
            playerInput: '',

            // 物品栏标签
            inventoryTab: 'weapons',

            // 角色数据（从数据库加载）
            character: {
                name: '加载中...',
                sex: 'Male',
                age: 0,
                str: 0,
                con: 0,
                siz: 0,
                dex: 0,
                app: 0,
                int: 0,
                pow: 0,
                edu: 0,
                hp: 0,
                maxHp: 0,
                san: 0,
                maxSan: 99,
                mp: 0,
                maxMp: 0,
                luck: 0
            },

            // 技能列表（从数据库加载，数值>10的技能）
            mainSkills: [],

            // 武器列表
            weapons: [
                {
                    name: '徒手格斗',
                    type: '格斗:斗殴',
                    damage: '1D3',
                    range: '——'
                },
                {
                    name: '.45自动手枪',
                    type: '射击:手枪',
                    damage: '1D10+2',
                    range: '15码'
                }
            ],

            // 道具列表
            items: [
                { name: '手电筒', desc: '可以照亮黑暗区域' },
                { name: '笔记本', desc: '记录调查线索' },
                { name: '放大镜', desc: '检查细节时有帮助' },
                { name: '急救包', desc: '可进行急救，恢复1D3 HP' }
            ],

            // 线索列表
            clues: [
                { name: '墓地传闻', desc: '当地居民说墓地晚上有奇怪的声音' }
            ],

            // 对话消息
            messages: [
                {
                    type: 'system',
                    content: '—— 游戏开始 ——'
                }
            ],

            // 当前可选选项
            options: [
                { id: 1, text: '询问附近的居民关于墓地的传闻', action: 'askResidents' },
                { id: 2, text: '查看墓地周边环境', action: 'exploreCemetery' },
                { id: 3, text: '前往图书馆调查历史资料', action: 'goLibrary' },
                { id: 4, text: '去警察局了解情况', action: 'goPolice' }
            ]
        };
    },

    methods: {
        // 切换折叠面板
        toggleSection(section) {
            this.sections[section] = !this.sections[section];
        },

        // 开始拖动
        startResize(type, event) {
            this.isResizing = true;
            this.resizeType = type;
            document.addEventListener('mousemove', this.doResize);
            document.addEventListener('mouseup', this.stopResize);
            event.preventDefault();
        },

        // 拖动中
        doResize(event) {
            if (!this.isResizing) return;

            if (this.resizeType === 'left') {
                const newWidth = event.clientX;
                if (newWidth >= 200 && newWidth <= 500) {
                    this.leftPanelWidth = newWidth;
                }
            } else if (this.resizeType === 'right') {
                const newWidth = window.innerWidth - event.clientX;
                if (newWidth >= 200 && newWidth <= 500) {
                    this.rightPanelWidth = newWidth;
                }
            } else if (this.resizeType === 'vertical') {
                const rightPanel = document.querySelector('.right-panel');
                if (rightPanel) {
                    const rect = rightPanel.getBoundingClientRect();
                    const newHeight = rect.bottom - event.clientY;
                    if (newHeight >= 100 && newHeight <= 400) {
                        this.optionsPanelHeight = newHeight;
                    }
                }
            }
        },

        // 停止拖动
        stopResize() {
            this.isResizing = false;
            this.resizeType = null;
            document.removeEventListener('mousemove', this.doResize);
            document.removeEventListener('mouseup', this.stopResize);
        },

        // 查询调查员
        async searchPlayer() {
            if (!this.playerIdInput.trim()) {
                this.errorMsg = '请输入调查员ID';
                return;
            }
            this.errorMsg = '';
            this.playerFound = false;
            this.playerId = this.playerIdInput.trim();
            const success = await this.loadPlayerData();
            if (success) {
                await this.loadSkillsData();
                this.playerFound = true;
            }
        },

        // 刷新当前调查员信息
        async refreshPlayer() {
            if (!this.playerId) {
                this.errorMsg = '请先查询调查员';
                return;
            }
            this.errorMsg = '';
            await this.loadPlayerData();
            await this.loadSkillsData();
        },

        // 登录
        async loginPlayer() {
            if (!this.playerId) {
                this.errorMsg = '请先查询调查员';
                return;
            }
            this.isLoading = true;
            try {
                const response = await fetch(`${AUTH_BASE_URL}/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ player_id: this.playerId })
                });
                const result = await response.json();
                if (result.success) {
                    this.authToken = result.token;
                    this.isLoggedIn = true;
                    this.playerFound = false;
                    localStorage.setItem('authToken', result.token);
                    localStorage.setItem('playerId', this.playerId);
                }
            } catch (error) {
                this.errorMsg = '登录失败: ' + error.message;
            }
            this.isLoading = false;
        },

        // 退出登录
        logoutPlayer() {
            this.isLoggedIn = false;
            this.authToken = null;
            this.playerFound = false;
            this.playerId = '';
            this.playerIdInput = '';
            localStorage.removeItem('authToken');
            localStorage.removeItem('playerId');
            // 重置角色数据
            this.character = {
                name: '未登录', sex: 'Male', age: 0,
                str: 0, con: 0, siz: 0, dex: 0, app: 0,
                int: 0, pow: 0, edu: 0, hp: 0, maxHp: 0,
                san: 0, maxSan: 99, mp: 0, maxMp: 0, luck: 0
            };
            this.mainSkills = [];
        },

        // 检查对话服务状态
        async checkChatStatus() {
            try {
                const online = await ChatModule.checkStatus();
                this.chatOnline = online;
                // 服务在线则自动启用对话功能并初始化Agent
                if (online && !this.chatEnabled) {
                    const initResult = await ChatModule.initAgent();
                    if (initResult.success) {
                        this.chatEnabled = true;
                        ChatModule.enable();
                    }
                } else if (!online) {
                    this.chatEnabled = false;
                    ChatModule.disable();
                }
            } catch (error) {
                this.chatOnline = false;
                this.chatEnabled = false;
            }
        },

        // 重置所有记忆
        async resetAllMemory() {
            if (!confirm('确定要重置所有记忆吗？这将清除所有对话历史。')) {
                return;
            }
            this.chatLoading = true;
            try {
                const result = await ChatModule.resetAllMemory();
                if (result.success) {
                    this.messages = [{ type: 'system', content: '—— 记忆已重置 ——' }];
                    this.currentSceneName = '主线程';
                    this.sceneDepth = 0;
                    // 刷新场景列表（重置后所有场景恢复可进入）
                    await this.refreshAvailableScenes();
                    alert('所有记忆已重置');
                } else {
                    alert('重置失败: ' + (result.error || result.detail || '未知错误'));
                }
            } catch (error) {
                alert('重置失败: ' + error.message);
            }
            this.chatLoading = false;
        },

        // 显示日志弹窗
        async showLogs() {
            this.logsVisible = true;
            await this.refreshLogs();
        },

        // 刷新日志
        async refreshLogs() {
            const result = await ChatModule.getLogs();
            if (result.success) {
                this.logs = result.logs || [];
            }
        },

        // 清空日志
        async clearLogs() {
            await ChatModule.clearLogs();
            await this.refreshLogs();
        },

        // 刷新可用场景列表
        async refreshAvailableScenes() {
            const result = await ChatModule.getAvailableScenes();
            if (result.success) {
                this.availableScenes = result.available_scenes || [];
            } else {
                this.availableScenes = [];
            }
        },

        // 进入新场景
        async enterScene(scene) {
            // 添加玩家选择的消息
            this.messages.push({
                type: 'player',
                sender: '【' + this.character.name + '】',
                content: '（进入场景：' + scene + '）'
            });

            const result = await ChatModule.enterNewScene(scene);
            if (result.success) {
                // 刷新场景信息
                await this.refreshSceneInfo();
                // 使用后端返回的最新场景列表
                this.availableScenes = result.available_scenes || [];
                // 添加系统消息
                this.messages.push({
                    type: 'system',
                    content: '—— ' + result.message + ' ——'
                });

                // 自动发送"继续"消息获取场景描述（流式传输）
                await this.sendToAI('我已进入当前场景');
            } else {
                this.messages.push({
                    type: 'system',
                    content: '进入场景失败: ' + (result.error || '未知错误')
                });
            }
        },

        // 退出当前场景
        async exitScene() {
            if (this.sceneDepth === 0) {
                alert('当前不在任何场景中');
                return;
            }

            // 添加玩家选择的消息
            this.messages.push({
                type: 'player',
                sender: '【' + this.character.name + '】',
                content: '（退出当前场景）'
            });

            const result = await ChatModule.exitCurrentScene();
            if (result.success) {
                // 刷新场景信息
                await this.refreshSceneInfo();
                // 使用后端返回的最新场景列表（退出场景不影响次数统计）
                this.availableScenes = result.available_scenes || [];
                // 添加系统消息
                this.messages.push({
                    type: 'system',
                    content: '—— ' + result.message + ' ——'
                });

                // 自动发送"继续"消息获取场景描述（流式传输）
                await this.sendToAI('我已从其他场景退回当前场景');
            } else {
                this.messages.push({
                    type: 'system',
                    content: '退出场景失败: ' + (result.error || '未知错误')
                });
            }
        },

        // 刷新场景信息
        async refreshSceneInfo() {
            const result = await ChatModule.getSceneInfo();
            if (result.success) {
                this.currentSceneName = result.scene_name || '主线程';
                this.sceneDepth = result.scene_depth || 0;
            }
        },

        // 从API加载玩家数据
        async loadPlayerData() {
            this.isLoading = true;
            this.errorMsg = '';
            let success = false;
            try {
                const response = await fetch(`${this.apiBaseUrl}/player/${this.playerId}`);
                const result = await response.json();

                if (result.success) {
                    const data = result.data;
                    this.character = {
                        name: data.name,
                        sex: data.sex,
                        age: data.age,
                        str: data.strength,
                        con: data.constitution,
                        siz: data.size,
                        dex: data.dexterity,
                        app: data.appearance,
                        int: data.intelligence,
                        pow: data.willpower,
                        edu: data.education,
                        hp: data.hit_points,
                        maxHp: data.max_hp,
                        san: data.sanity,
                        maxSan: data.max_san,
                        mp: data.magic_points,
                        maxMp: data.max_mp,
                        luck: data.luck
                    };
                    success = true;
                } else {
                    this.errorMsg = result.error || '未找到该调查员';
                }
            } catch (error) {
                console.error('加载玩家数据失败:', error);
                this.errorMsg = '网络错误，请检查API服务是否启动';
            }
            this.isLoading = false;
            return success;
        },

        // 从API加载技能数据
        async loadSkillsData() {
            try {
                const response = await fetch(`${this.apiBaseUrl}/skills/${this.playerId}`);
                const result = await response.json();

                if (result.success) {
                    this.mainSkills = result.data;
                }
            } catch (error) {
                console.error('加载技能数据失败:', error);
            }
        },

        // 发送消息
        async sendMessage() {
            // 对话进行中时禁止发送新消息
            if (this.isWaitingAI) return;
            if (!this.playerInput.trim()) return;

            // 添加玩家消息
            this.messages.push({
                type: 'player',
                sender: '【' + this.character.name + '】',
                content: this.playerInput
            });

            const userInput = this.playerInput;
            this.playerInput = '';

            // 滚动到底部
            this.$nextTick(() => {
                this.scrollToBottom();
            });

            // 如果对话功能已启用，发送到AI
            if (this.chatEnabled && this.chatOnline) {
                await this.sendToAI(userInput);
            } else {
                // 原有的处理逻辑
                this.processPlayerInput(userInput);
            }
        },

        // 发送消息到AI（流式输出）
        async sendToAI(message) {
            this.isWaitingAI = true;

            // 先添加一个空的 AI 消息占位符
            const aiMessageIndex = this.messages.length;
            this.messages.push({
                type: 'narrator',
                sender: '【游戏主持人】',
                content: ''
            });

            this.$nextTick(() => {
                this.scrollToBottom();
            });

            const self = this;
            await ChatModule.sendMessage(
                message,
                // onToken: 每收到一个 token 时更新消息
                (token) => {
                    self.messages[aiMessageIndex].content += token;
                    self.$nextTick(() => {
                        self.scrollToBottom();
                    });
                },
                // onComplete: 完成时的回调
                async (fullResponse) => {
                    self.isWaitingAI = false;
                    // 对话完成后刷新用户状态
                    if (self.isLoggedIn) {
                        self.loadPlayerData();
                        self.loadSkillsData();
                    }
                    // 刷新场景信息
                    await self.refreshSceneInfo();
                    // 刷新可用场景列表
                    await self.refreshAvailableScenes();
                    self.$nextTick(() => {
                        self.scrollToBottom();
                    });
                },
                // onError: 错误时的回调
                (error) => {
                    self.messages[aiMessageIndex].content = 'AI回复失败: ' + error;
                    self.messages[aiMessageIndex].type = 'system';
                    self.isWaitingAI = false;
                }
            );
        },

        // 处理玩家输入
        processPlayerInput(input) {
            // 这里可以接入后端AI进行处理
            // 目前只是简单的示例响应
            setTimeout(() => {
                this.messages.push({
                    type: 'narrator',
                    sender: '【旁白】',
                    content: '你的行动已被记录。守密人正在思考...'
                });
                this.scrollToBottom();
            }, 500);
        },

        // 选择选项
        selectOption(option) {
            // 添加玩家选择的消息
            this.messages.push({
                type: 'player',
                sender: '【' + this.character.name + '】',
                content: '（选择了：' + option.text + '）'
            });

            // 根据选项执行不同的行动
            this.executeAction(option.action);

            // 滚动到底部
            this.$nextTick(() => {
                this.scrollToBottom();
            });
        },

        // 执行行动
        executeAction(action) {
            switch (action) {
                case 'askResidents':
                    this.askResidents();
                    break;
                case 'exploreCemetery':
                    this.exploreCemetery();
                    break;
                case 'goLibrary':
                    this.goLibrary();
                    break;
                case 'goPolice':
                    this.goPolice();
                    break;
                default:
                    break;
            }
        },

        // 询问居民
        askResidents() {
            setTimeout(() => {
                this.messages.push({
                    type: 'narrator',
                    sender: '【旁白】',
                    content: '你在墓地附近找到了一位正在修剪草坪的老人。他看起来对这片墓地非常熟悉。'
                });

                setTimeout(() => {
                    this.messages.push({
                        type: 'npc',
                        sender: '【老园丁 汤姆】',
                        content: '"啊，你也是来问那些怪事的吧？最近确实不太平静。我在这里工作了三十年，从没见过这样的事情。每到月圆之夜，金博尔家的墓碑附近就会传来奇怪的声音..."'
                    });

                    // 添加新线索
                    this.clues.push({
                        name: '金博尔家墓碑',
                        desc: '老园丁提到金博尔家的墓碑附近有异常'
                    });

                    // 更新选项
                    this.options = [
                        { id: 1, text: '询问金博尔家的历史', action: 'askKimball' },
                        { id: 2, text: '请老人带你去看那块墓碑', action: 'visitTombstone' },
                        { id: 3, text: '返回继续调查其他地方', action: 'returnMain' }
                    ];

                    this.scrollToBottom();
                }, 1000);

                this.scrollToBottom();
            }, 500);
        },

        // 查看墓地周边
        exploreCemetery() {
            // 进行侦查检定
            const roll = this.rollD100();
            const skill = 60; // 侦查技能

            setTimeout(() => {
                this.messages.push({
                    type: 'dice-roll',
                    content: `🎲 侦查检定: ${roll} / ${skill} - ${roll <= skill ? '成功！' : '失败'}`
                });

                setTimeout(() => {
                    if (roll <= skill) {
                        this.messages.push({
                            type: 'narrator',
                            sender: '【旁白】',
                            content: '你仔细观察墓地周围的环境。在一块较新的墓碑旁，你发现了一些奇怪的痕迹——泥土似乎被翻动过，而且有一些不寻常的脚印。这些脚印看起来不像是普通人留下的...'
                        });

                        this.clues.push({
                            name: '奇怪的脚印',
                            desc: '墓地中发现的不寻常脚印，形状怪异'
                        });
                    } else {
                        this.messages.push({
                            type: 'narrator',
                            sender: '【旁白】',
                            content: '你在墓地中四处查看，但没有发现什么特别的东西。也许需要更仔细地搜索，或者从其他途径获取信息。'
                        });
                    }
                    this.scrollToBottom();
                }, 800);

                this.scrollToBottom();
            }, 500);
        },

        // 前往图书馆
        goLibrary() {
            setTimeout(() => {
                this.currentScene = '场景2';
                this.currentSceneName = '阿诺兹堡公共图书馆';

                this.messages.push({
                    type: 'system',
                    content: '—— 场景转换：图书馆 ——'
                });

                this.messages.push({
                    type: 'narrator',
                    sender: '【旁白】',
                    content: '你来到了阿诺兹堡公共图书馆。这是一座维多利亚风格的建筑，里面收藏着大量关于当地历史的资料。图书管理员是一位戴着厚厚眼镜的中年女性，她正在整理书架。'
                });

                this.options = [
                    { id: 1, text: '查阅当地历史档案', action: 'searchArchives' },
                    { id: 2, text: '询问图书管理员', action: 'askLibrarian' },
                    { id: 3, text: '查找关于墓地的旧报纸', action: 'searchNewspaper' }
                ];

                this.scrollToBottom();
            }, 500);
        },

        // 去警察局
        goPolice() {
            setTimeout(() => {
                this.currentScene = '场景3';
                this.currentSceneName = '阿诺兹堡警察局';

                this.messages.push({
                    type: 'system',
                    content: '—— 场景转换：警察局 ——'
                });

                this.messages.push({
                    type: 'narrator',
                    sender: '【旁白】',
                    content: '你走进了阿诺兹堡警察局。这是一座朴素的砖石建筑，里面只有几名警员在值班。一位看起来疲惫的警长坐在办公桌后面，正在处理文件。'
                });

                this.messages.push({
                    type: 'npc',
                    sender: '【警长 麦克唐纳】',
                    content: '"又一个来问墓地的事的？听着，我们已经派人去查过了，什么都没发现。可能只是一些野生动物，或者是那些无聊的年轻人在恶作剧。"'
                });

                this.options = [
                    { id: 1, text: '询问是否有相关报案记录', action: 'askRecords' },
                    { id: 2, text: '尝试说服警长认真对待此事', action: 'persuadeChief' },
                    { id: 3, text: '离开警察局', action: 'returnMain' }
                ];

                this.scrollToBottom();
            }, 500);
        },

        // 掷D100
        rollD100() {
            return Math.floor(Math.random() * 100) + 1;
        },

        // 掷骰子
        rollDice() {
            const roll = this.rollD100();
            this.messages.push({
                type: 'dice-roll',
                content: `🎲 D100 掷骰结果: ${roll}`
            });
            this.scrollToBottom();
        },

        // 滚动到底部
        scrollToBottom() {
            const container = this.$refs.dialogueContent;
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        },

        // 显示角色卡
        showCharacterSheet() {
            alert('角色卡功能开发中...');
        },

        // 显示规则
        showRules() {
            alert('规则查询功能开发中...');
        },

        // 存档
        saveGame() {
            const saveData = {
                character: this.character,
                messages: this.messages,
                clues: this.clues,
                items: this.items,
                currentChapter: this.currentChapter,
                currentScene: this.currentScene,
                currentSceneName: this.currentSceneName,
                options: this.options
            };
            localStorage.setItem('cocGameSave', JSON.stringify(saveData));
            alert('游戏已保存！');
        },

        // 读档
        loadGame() {
            const saveData = localStorage.getItem('cocGameSave');
            if (saveData) {
                const data = JSON.parse(saveData);
                this.character = data.character;
                this.messages = data.messages;
                this.clues = data.clues;
                this.items = data.items;
                this.currentChapter = data.currentChapter;
                this.currentScene = data.currentScene;
                this.currentSceneName = data.currentSceneName;
                this.options = data.options;
                alert('游戏已读取！');
                this.$nextTick(() => {
                    this.scrollToBottom();
                });
            } else {
                alert('没有找到存档！');
            }
        }
    },

    mounted() {
        // 检查对话服务状态
        this.checkChatStatus();

        // 定时检查对话服务状态（每10秒）
        setInterval(() => {
            this.checkChatStatus();
        }, 10000);

        // 恢复登录状态
        const savedToken = localStorage.getItem('authToken');
        const savedPlayerId = localStorage.getItem('playerId');
        if (savedToken && savedPlayerId) {
            this.authToken = savedToken;
            this.playerId = savedPlayerId;
            this.isLoggedIn = true;
            this.loadPlayerData();
            this.loadSkillsData();
        }

        // 滚动到底部
        this.$nextTick(() => {
            this.scrollToBottom();
        });
    }
};

createApp(App).mount('#app');
