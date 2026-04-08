# AI语音问答助手

基于 FastAPI + Bootstrap 的前后端分离 AI 语音问答 Web 应用，支持实时语音对话、流式输出和自动降级。

## 功能特性

- **实时语音对话** - WebSocket 实现低延迟通信
- **语音识别** - 硅基流动 API（TeleSpeechASR）
- **语音合成** - 小米 MiMo-V2-TTS（流式输出）+ 浏览器 WebSpeech API 降级
- **AI 对话** - 支持任意 OpenAI 兼容 API（OpenAI/智谱GLM/阿里通义/DeepSeek 等）
- **流式输出** - AI 回答和 TTS 均支持流式，边生成边播放
- **自动降级** - MiMo TTS 超时自动切换到浏览器语音合成
- **对话历史** - 支持多轮对话上下文管理
- **文本输入** - 备用文字输入模式

## 技术栈

**后端：**
- FastAPI - 高性能异步 Web 框架
- WebSocket - 实时双向通信
- ThreadPoolExecutor + Queue - 同步生成器异步化
- OpenAI API - AI 对话
- SiliconFlow API - 语音识别
- MiMo API - 流式语音合成

**前端：**
- Bootstrap 5 - 响应式 UI
- WebSocket API - 实时通信
- Web Audio API - 流式音频播放
- Web Speech API - 浏览器语音合成降级

## 项目结构

```
ai-voice-qa/
├── backend/
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 配置管理
│   ├── requirements.txt        # Python 依赖
│   ├── routers/
│   │   ├── chat.py             # REST API（聊天、TTS）
│   │   └── ws.py               # WebSocket（语音对话）
│   ├── services/
│   │   ├── ai_service.py       # AI 对话服务（流式）
│   │   ├── asr_service.py      # 语音识别服务
│   │   ├── tts_service.py      # TTS 服务（流式 + 重试）
│   │   └── session_service.py  # 会话管理
│   └── models/
│       └── schemas.py          # Pydantic 数据模型
├── frontend/
│   ├── index.html              # 主页面
│   ├── css/style.css           # 样式（蓝白配色）
│   └── js/
│       ├── app.js              # 主逻辑（音频播放 + WebSpeech）
│       ├── audio.js            # 录音管理
│       └── websocket.js        # WebSocket 管理
├── start.bat                   # 一键启动脚本（Windows）
└── README.md
```

## 快速开始

### 前置要求

- Python 3.8+
- 现代浏览器（Chrome/Edge/Firefox）
- 麦克风设备

### 1. 克隆项目

```bash
git clone https://github.com/your-username/ai-voice-qa.git
cd ai-voice-qa
```

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 配置环境变量

在 `backend/` 目录创建 `.env` 文件：

```env
# AI 对话 API（必填）
OPENAI_API_KEY=your-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# 语音识别（必填）
SILICONFLOW_API_KEY=your-siliconflow-key
SILICONFLOW_ASR_MODEL=TeleAI/TeleSpeechASR

# 语音合成（可选，默认使用浏览器 WebSpeech）
TTS_PROVIDER=mimo
MIMO_API_KEY=your-mimo-key
MIMO_TTS_MODEL=mimo-v2-tts
MIMO_VOICE=mimo_default
MIMO_AUDIO_FORMAT=wav

# 服务器配置
FRONTEND_ORIGIN=http://localhost:8080
```

### 4. 启动服务

**方式一：一键启动（Windows）**

双击 `start.bat`，自动启动前后端服务并打开浏览器。

**方式二：手动启动**

终端 1 - 启动后端：
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 9000 --reload
```

终端 2 - 启动前端：
```bash
cd frontend
python -m http.server 8080
```

### 5. 访问应用

打开浏览器访问：http://localhost:8080

## 环境变量说明

| 变量 | 默认值 | 说明 |
|------|--------|------|
| **AI 对话** |||
| OPENAI_API_KEY | 无（必填） | OpenAI 兼容 API 密钥 |
| OPENAI_API_BASE | https://api.openai.com/v1 | API 地址 |
| OPENAI_MODEL | gpt-3.5-turbo | 模型名称 |
| **语音识别** |||
| SILICONFLOW_API_KEY | 无（必填） | 硅基流动 API 密钥 |
| SILICONFLOW_ASR_MODEL | TeleAI/TeleSpeechASR | 语音识别模型 |
| **语音合成** |||
| TTS_PROVIDER | webspeech | 语音合成方式：`webspeech` / `mimo` |
| MIMO_API_KEY | 无 | 小米 MiMo API 密钥（TTS=mimo 时必填） |
| MIMO_TTS_MODEL | mimo-v2-tts | MiMo TTS 模型 |
| MIMO_VOICE | mimo_default | MiMo 音色 |
| MIMO_AUDIO_FORMAT | wav | 音频格式 |
| **服务器** |||
| FRONTEND_ORIGIN | http://localhost:8080 | 前端地址（CORS） |

## 架构设计

### 流式输出架构

```
用户语音 → ASR识别 → AI流式生成 → TTS流式合成 → 浏览器播放
   ↓           ↓           ↓              ↓
  Websocket  SiliconFlow  OpenAI API    MiMo API
                               ↓
                          [超时降级]
                               ↓
                        WebSpeech API
```

### TTS 自动降级机制

1. **MiMo TTS 流式合成**（默认）
   - 首次尝试：5秒超时
   - 成功：流式播放音频块
   - 失败/超时：触发降级

2. **WebSpeech API 降级**
   - 浏览器内置语音合成
   - 无需网络请求
   - 支持暂停/继续

### 线程池 + 队列模式

解决同步生成器在异步 WebSocket 中的阻塞问题：

```python
def _tts_worker(tts, text, queue):
    for chunk in tts.synthesize_stream(text):
        queue.put(chunk)
    queue.put(None)

# 异步消费
loop.run_in_executor(executor, _tts_worker, tts, text, queue)
chunk = await loop.run_in_executor(None, queue.get)
```

## API 文档

启动后端后访问：http://localhost:9000/docs

### REST API

- `POST /api/chat` - 文本对话
- `POST /api/tts` - 文本转语音（非流式）
- `POST /api/tts/stream` - 文本转语音（流式）
- `GET /api/history/{session_id}` - 获取对话历史

### WebSocket

- `ws://localhost:9000/ws/audio/{session_id}` - 语音对话

**消息类型：**

```javascript
// 发送
AudioBlob  // 二进制音频数据

// 接收
{"type": "text_start", "user_text": "...", "tts_provider": "mimo"}
{"type": "text_delta", "text": "..."}
{"type": "text_end"}
{"type": "tts_fallback", "text": "..."}  // TTS 降级信号
AudioChunk  // 二进制音频数据
{"type": "audio_end"}
{"type": "error", "error": "..."}
```

## 支持的 AI 平台

通过 `OPENAI_API_BASE` 配置，支持：

- OpenAI (`https://api.openai.com/v1`)
- 智谱 GLM (`https://open.bigmodel.cn/api/paas/v4`)
- 阿里通义 (`https://dashscope.aliyuncs.com/compatible-mode/v1`)
- DeepSeek (`https://api.deepseek.com/v1`)
- SiliconFlow (`https://api.siliconflow.cn/v1`)
- LocalAI / Ollama 等本地模型

## 性能优化

- **流式输出**：AI 和 TTS 均支持，首字节延迟 < 1 秒
- **线程池**：4 个 worker 处理 TTS 任务
- **超时控制**：API 超时 5 秒，快速降级
- **自动重试**：TTS 失败自动重试（已移除，直接降级更快）

## 故障排查

### 麦克风无法访问

确保浏览器有麦克风权限，HTTPS 或 localhost 环境下才能访问麦克风。

### TTS 无声音

1. 检查浏览器控制台是否有错误
2. 检查后端日志中 TTS 相关输出
3. MiMo API 超时会自动降级到 WebSpeech

### WebSocket 连接失败

确保后端运行在正确端口（默认 9000），前端 `websocket.js` 中配置正确。

## 开发

### 运行测试

```bash
cd backend
pip install -r requirements-dev.txt
pytest tests/ -v
```

### 代码风格

- 后端：PEP 8
- 前端：ES6+

## 许可证

MIT License

## 致谢

- [FastAPI](https://fastapi.tiangolo.com/)
- [Bootstrap](https://getbootstrap.com/)
- [SiliconFlow](https://siliconflow.cn/) - 语音识别
- [MiMo](https://xiaomimimo.com/) - 语音合成