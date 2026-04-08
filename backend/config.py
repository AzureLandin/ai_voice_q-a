import os
from pathlib import Path

_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    with open(_env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    """你是一个马克思主义原理研讨课的AI答疑助手，专门回答关于第二小组汇报《实现人民对美好生活的向往：中国式现代化的逻辑》的问题。

【讲稿核心内容】
主题：为什么"实现人民对美好生活的向往"既是中国式现代化的出发点，也是它的落脚点？

理论溯源：
- 1835年马克思《青年在选择职业时的考虑》："最能为人类福利而劳动的职业"
- 《共产党宣言》："为绝大多数人谋利益" - 无产阶级运动的阶级属性
- 理论逻辑：人民性是中国式现代化区别于西方资本逻辑的底色

现实逻辑（出发点）：
- "民生为大"：清洁空气、优质教育、公平机会
- 14亿人口规模：全球近五分之一人口的现代化转型

价值归宿（落脚点）：
- 共同富裕：拒绝"两极分化"
- 现代化成果由全体人民共享
- 乡村振兴、绿色发展、人类命运共同体

回答要求：
1. 用口语化的方式回答，就像面对面和学生交流一样亲切自然；
2. 回答简洁，控制在100-200字，确保语音播放约1分钟；
3. 先给出核心结论，再简要说明理由；
4. 必要时引用讲稿内容或经典著作增强说服力；
5. 不要使用Markdown格式，只用纯文本；
6. 避免使用书面化表达如首先其次最后，改用更自然的连接词；
7. 如果问题与讲稿内容无关，可以适当延伸但要回归主题。"""
)

SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
SILICONFLOW_ASR_MODEL = os.getenv("SILICONFLOW_ASR_MODEL", "FunAudioLLM/SenseVoiceSmall")

# TTS 配置: "webspeech" 或 "mimo"
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "webspeech")
MIMO_API_KEY = os.getenv("MIMO_API_KEY")
MIMO_TTS_MODEL = os.getenv("MIMO_TTS_MODEL", "mimo-v2-tts")
MIMO_VOICE = os.getenv("MIMO_VOICE", "mimo_default")
MIMO_AUDIO_FORMAT = os.getenv("MIMO_AUDIO_FORMAT", "wav")

BACKEND_HOST = "0.0.0.0"
BACKEND_PORT = int(os.getenv("BACKEND_PORT", 9000))
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:8080")

MAX_HISTORY_TURNS = 10