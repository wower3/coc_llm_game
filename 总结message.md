# LangChain JavaScript Messages 中文总结文档

## 概述
Messages（消息）是LangChain中模型上下文的基本单位。它们代表模型的输入和输出，携带对话状态所需的內容和元数据。消息对象包含三个主要组成部分：
- **Role（角色）** - 标识消息类型（如system、user）
- **Content（内容）** - 表示消息的实际内容（文本、图像、音频、文档等）
- **Metadata（元数据）** - 可选字段，如响应信息、消息ID和令牌使用情况

## 基本用法

### 文本提示（Text Prompts）
适用于简单生成任务，不需要保留对话历史：
```javascript
const response = await model.invoke("Write a haiku about spring");
```

适用场景：
- 单一、独立的请求
- 不需要对话历史
- 希望代码尽可能简单

### 消息提示（Message Prompts）
通过传递消息对象列表来与模型交互：
```javascript
import { SystemMessage, HumanMessage, AIMessage } from "langchain";

const messages = [
  new SystemMessage("You are a poetry expert"),
  new HumanMessage("Write a haiku about spring"),
  new AIMessage("Cherry blossoms bloom..."),
];

const response = await model.invoke(messages);
```

适用场景：
- 管理多轮对话
- 处理多模态内容（图像、音频、文件）
- 包含系统指令

### 字典格式（Dictionary Format）
也可以使用OpenAI聊天完成格式直接指定消息：
```javascript
const messages = [
  { role: "system", content: "You are a poetry expert" },
  { role: "user", content: "Write a haiku about spring" },
  { role: "assistant", content: "Cherry blossoms bloom..." },
];

const response = await model.invoke(messages);
```

## 消息类型

### 系统消息（System Message）
SystemMessage代表一组初始指令，用于设定模型的行为。可以用来设置语调、定义模型角色和建立响应指南。

#### 基本指令
```javascript
import { SystemMessage, HumanMessage, AIMessage } from "langchain";

const systemMsg = new SystemMessage("You are a helpful coding assistant.");
const messages = [
  systemMsg,
  new HumanMessage("How do I create a REST API?"),
];

const response = await model.invoke(messages);
```

#### 详细角色设定
```javascript
const systemMsg = new SystemMessage(`
  You are a senior TypeScript developer with expertise in web frameworks.
  Always provide code examples and explain your reasoning.
  Be concise but thorough in your explanations.
`);

const messages = [
  systemMsg,
  new HumanMessage("How do I create a REST API?"),
];

const response = await model.invoke(messages);
```

### 人类消息（Human Message）
HumanMessage代表用户输入和交互，可以包含文本、图像、音频、文件等多模态内容。

#### 文本内容
```javascript
// 消息对象方式
const response = await model.invoke([
  new HumanMessage("What is machine learning?")
]);

// 字符串快捷方式
const response = await model.invoke("What is machine learning?");
```

#### 消息元数据
```javascript
const humanMsg = new HumanMessage({
  content: "Hello!",
  name: "alice",
  id: "msg_123",
});
```

### AI消息（AIMessage）
AIMessage代表模型调用的输出，可以包含多模态数据、工具调用和提供程序特定的元数据。

```javascript
const response = await model.invoke("Explain AI");
console.log(typeof response); // AIMessage
```

#### 属性说明
- `text`: 消息的文本内容
- `content`: 消息的原始内容
- `content_blocks`: 标准化的内容块
- `tool_calls`: 模型进行的工具调用（如果没有调用工具则为空）
- `id`: 消息的唯一标识符
- `usage_metadata`: 使用元数据，包含令牌计数等信息
- `response_metadata`: 响应元数据

#### 插入历史消息
有时需要手动创建AIMessage对象并插入到消息历史中：
```javascript
import { AIMessage, SystemMessage, HumanMessage } from "langchain";

const aiMsg = new AIMessage("I'd be happy to help you with that question!");
const messages = [
  new SystemMessage("You are a helpful assistant"),
  new HumanMessage("Can you help me?"),
  aiMsg, // 插入仿佛来自模型的消息
  new HumanMessage("Great! What's 2+2?")
];

const response = await model.invoke(messages);
```

#### 工具调用
当模型进行工具调用时，这些调用会包含在AIMessage中：
```javascript
const modelWithTools = model.bindTools([getWeather]);
const response = await modelWithTools.invoke("What's the weather in Paris?");

for (const toolCall of response.tool_calls) {
  console.log(`Tool: ${toolCall.name}`);
  console.log(`Args: ${toolCall.args}`);
  console.log(`ID: ${toolCall.id}`);
}
```

#### 令牌使用情况
AIMessage可以在其`usage_metadata`字段中保存令牌计数和其他使用元数据：
```javascript
import { initChatModel } from "langchain";

const model = await initChatModel("gpt-5-nano");
const response = await model.invoke("Hello!");

console.log(response.usage_metadata);
// {
//   "output_tokens": 304,
//   "input_tokens": 8,
//   "total_tokens": 312,
//   "input_token_details": { "cache_read": 0 },
//   "output_token_details": { "reasoning": 256 }
// }
```

### 工具消息（Tool Message）
对于支持工具调用的模型，AI消息可以包含工具调用。工具消息用于将单个工具执行的结果传回给模型。

```javascript
import { AIMessage, ToolMessage } from "langchain";

const aiMessage = new AIMessage({
  content: [],
  tool_calls: [{
    name: "get_weather",
    args: { location: "San Francisco" },
    id: "call_123"
  }]
});

const toolMessage = new ToolMessage({
  content: "Sunny, 72°F",
  tool_call_id: "call_123"
});

const messages = [
  new HumanMessage("What's the weather in San Francisco?"),
  aiMessage,      // 模型的工具调用
  toolMessage,    // 工具执行结果
];

const response = await model.invoke(messages); // 模型处理结果
```

工具消息属性：
- `content`（必需）：工具调用的字符串化输出
- `tool_call_id`（必需）：响应的工具调用ID，必须与AIMessage中的工具调用ID匹配
- `name`（必需）：被调用的工具名称
- `artifact`：不发送给模型但可以编程访问的附加数据

## 消息内容

消息的内容可以视为发送给模型的数据负载。消息有一个松散类型的`content`属性，支持字符串和无类型对象列表（如字典），这允许直接在LangChain聊天模型中支持提供程序原生结构，如多模态内容和其他数据。

LangChain聊天模型接受以下格式的消息内容：
- 字符串
- 提供程序原生格式的内容块列表
- LangChain标准内容块列表

### 多模态输入示例
```javascript
import { HumanMessage } from "langchain";

// 字符串内容
const humanMessage = new HumanMessage("Hello, how are you?");

// 提供程序原生格式（如OpenAI）
const humanMessage = new HumanMessage({
  content: [
    { type: "text", text: "Hello, how are you?" },
    { type: "image_url", image_url: { url: "https://example.com/image.jpg" } },
  ]
});

// 标准内容块列表
const humanMessage = new HumanMessage({
  contentBlocks: [
    { type: "text", text: "Hello, how are you?" },
    { type: "image", url: "https://example.com/image.jpg" },
  ]
});
```

### 标准内容块
LangChain为消息内容提供了跨提供程序的标准表示。消息对象实现了`contentBlocks`属性，该属性会延迟解析`content`属性为标准的类型安全表示。

例如，从ChatAnthropic或ChatOpenAI生成的消息将包括思考或推理块，但可以延迟解析为一致的`ReasoningContentBlock`表示。

### 多模态支持
多模态性指的是处理不同形式数据的能力，如文本、音频、图像和视频。LangChain包含这些数据的标准类型，可在提供程序间使用。聊天模型可以接受多模态数据作为输入并生成多模态数据作为输出。

## 使用聊天模型
聊天模型接受消息对象序列作为输入，并返回AIMessage作为输出。交互通常是无状态的，因此简单的对话循环涉及使用不断增长的消息列表调用模型。