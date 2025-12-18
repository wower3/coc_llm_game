# LangChain JavaScript Messages 中文总结文档

## 概述
Messages（消息）是LangChain中模型上下文的基本单位。它们代表模型的输入和输出，携带对话状态所需的內容和元数据。消息对象包含三个主要组成部分：
- **Role（角色）** - 标识消息类型（如system、user）
- **Content（内容）** - 表示消息的实际内容（文本、图像、音频、文档等）
- **Metadata（元数据）** - 可选字段，如响应信息、消息ID和令牌使用情况

LangChain提供了一种标准消息类型，可在所有模型提供程序间使用，确保无论调用哪种模型都能保持一致的行为。

## 基本用法
最简单的使用消息的方式是创建消息对象，并在调用模型时传递它们。

```javascript
import { initChatModel, HumanMessage, SystemMessage } from "langchain";

const model = await initChatModel("gpt-5-nano");
const systemMsg = new SystemMessage("You are a helpful assistant.");
const humanMsg = new HumanMessage("Hello, how are you?");
const messages = [systemMsg, humanMsg];
const response = await model.invoke(messages); // 返回 AIMessage
```

### 文本提示（Text Prompts）
文本提示是字符串 - 适合不需要保留对话历史的简单生成任务。

```javascript
const response = await model.invoke("Write a haiku about spring");
```

使用文本提示的场景：
- 单一、独立的请求
- 不需要对话历史
- 希望代码尽可能简单

### 消息提示（Message Prompts）
或者，您可以通过提供消息对象列表向模型传递消息列表。

```javascript
import { SystemMessage, HumanMessage, AIMessage } from "langchain";

const messages = [
  new SystemMessage("You are a poetry expert"),
  new HumanMessage("Write a haiku about spring"),
  new AIMessage("Cherry blossoms bloom..."),
];

const response = await model.invoke(messages);
```

使用消息提示的场景：
- 管理多轮对话
- 处理多模态内容（图像、音频、文件）
- 包含系统指令

### 字典格式（Dictionary Format）
您也可以使用OpenAI聊天完成格式直接指定消息：

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
SystemMessage代表一组初始指令，用于设定模型的行为。您可以使用系统消息来设置语调、定义模型角色和建立响应指南。

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
import { SystemMessage, HumanMessage } from "langchain";

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
HumanMessage代表用户输入和交互。它们可以包含文本、图像、音频、文件以及任何数量的多模态内容。

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
AIMessage代表模型调用的输出。它们可以包括多模态数据、工具调用和提供程序特定的元数据，您可以稍后访问。

```javascript
const response = await model.invoke("Explain AI");
console.log(typeof response); // AIMessage
```

AIMessage对象在调用模型时由模型返回，其中包含响应中的所有相关元数据。提供程序对不同类型的消息进行权衡/语境化不同，这意味着有时手动创建一个新的AIMessage对象并将其插入消息历史中，就像它来自模型一样是有帮助的。

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

#### 属性
| 属性 | 类型 | 描述 |
|------|------|------|
| `text` | `string` | 消息的文本内容 |
| `content` | `string | ContentBlock[]` | 消息的原始内容 |
| `content_blocks` | `ContentBlock.Standard[]` | 消息的标准内容块（参见内容） |
| `tool_calls` | `ToolCall[] | None` | 模型进行的工具调用。如果没有调用工具则为空 |
| `id` | `string` | 消息的唯一标识符（由LangChain自动生成或在提供程序响应中返回） |
| `usage_metadata` | `UsageMetadata | None` | 消息的使用元数据，在可用时包含令牌计数 |
| `response_metadata` | `ResponseMetadata | None` | 消息的响应元数据 |

#### 工具调用
当模型进行工具调用时，它们会包含在AIMessage中：

```javascript
const modelWithTools = model.bindTools([getWeather]);
const response = await modelWithTools.invoke("What's the weather in Paris?");

for (const toolCall of response.tool_calls) {
  console.log(`Tool: ${toolCall.name}`);
  console.log(`Args: ${toolCall.args}`);
  console.log(`ID: ${toolCall.id}`);
}
```

其他结构化数据，如推理或引用，也可能出现在消息内容中。

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

有关详细信息，请参见UsageMetadata。

#### 流式传输和块
在流式传输期间，您将收到AIMessageChunk对象，这些对象可以组合成完整的消息对象。

### 工具消息（Tool Message）
对于支持工具调用的模型，AI消息可以包含工具调用。工具消息用于将单个工具执行的结果传回给模型。工具可以直接生成ToolMessage对象。

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

#### 属性
| 属性 | 类型 | 描述 |
|------|------|------|
| `content` | `string` | **必需** - 工具调用的字符串化输出 |
| `tool_call_id` | `string` | **必需** - 此消息响应的工具调用ID。必须与AIMessage中的工具调用ID匹配 |
| `name` | `string` | **必需** - 被调用的工具名称 |
| `artifact` | `dict` | 不发送给模型但可以编程访问的附加数据 |

## 消息内容

您可以将消息的内容视为发送给模型的数据负载。消息具有松散类型的`content`属性，支持字符串和无类型对象列表（如字典）。这允许直接在LangChain聊天模型中支持提供程序原生结构，如多模态内容和其他数据。

另外，LangChain为文本、推理、引用、多模态数据、服务器端工具调用和其他消息内容提供了专门的内容类型。详见下面的内容块部分。

LangChain聊天模型在content属性中接受消息内容。这可能包含：
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
LangChain为消息内容提供了跨提供程序的标准表示。消息对象实现了`contentBlocks`属性，该属性会延迟解析content属性为标准的、类型安全的表示。

例如，从ChatAnthropic或ChatOpenAI生成的消息将分别包含相应提供程序格式的思考或推理块，但可以延迟解析为一致的ReasoningContentBlock表示：

**Anthropic:**
```javascript
import { AIMessage } from "@langchain/core/messages";

const message = new AIMessage({
  content: [
    {
      "type": "thinking",
      "thinking": "...",
      "signature": "WaUjzkyp...",
    },
    {
      "type":"text",
      "text": "...",
      "id": "msg_abc123",
    },
  ],
  response_metadata: {
    model_provider: "anthropic",
  },
});

console.log(message.contentBlocks);
```

**OpenAI:**
```javascript
import { AIMessage } from "@langchain/core/messages";

const message = new AIMessage({
  content: [
    {
      "type": "reasoning",
      "id": "rs_abc123",
      "summary": [
        {"type": "summary_text", "text": "summary 1"},
        {"type": "summary_text", "text": "summary 2"},
      ],
    },
    {"type": "text", "text": "..."},
  ],
  response_metadata: {
    model_provider: "openai",
  },
});

console.log(message.contentBlocks);
```

### 多模态支持
多模态性指的是处理不同形式数据的能力，如文本、音频、图像和视频。LangChain包含这些数据的标准类型，可在提供程序间使用。聊天模型可以接受多模态数据作为输入并生成多模态数据作为输出。

### 内容块参考
内容块（在创建消息或访问contentBlocks字段时）表示为类型对象列表。列表中的每个项目必须符合以下块类型之一：

这些内容块在导入ContentBlock类型时都可以作为单独的类型访问：

```javascript
import { ContentBlock } from "langchain";

// 文本块
const textBlock: ContentBlock.Text = {
  type: "text",
  text: "Hello world",
}

// 图像块
const imageBlock: ContentBlock.Multimodal.Image = {
  type: "image",
  url: "https://example.com/image.png",
  mimeType: "image/png",
}
```

## 使用聊天模型
聊天模型接受消息对象序列作为输入，并返回AIMessage作为输出。交互通常是无状态的，因此简单的对话循环涉及使用不断增长的消息列表调用模型。

有关更多内容，请参阅以下指南：
- 用于持久化和管理对话历史的内置功能
- 管理上下文窗口的策略，包括修剪和总结消息