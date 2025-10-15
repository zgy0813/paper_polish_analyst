# AI模型配置指南

## 🔧 支持的人工智能提供商

本系统支持多种AI API提供商，包括：
- **OpenAI** (GPT-4, GPT-3.5-turbo)
- **DeepSeek** (deepseek-chat)

## ⚙️ 配置方法

### 方法1: 环境变量 (推荐)

创建 `.env` 文件在项目根目录：

```bash
# 选择AI提供商
AI_PROVIDER=deepseek

# DeepSeek配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 通用配置
AI_MAX_TOKENS=4000
AI_TEMPERATURE=0.3
```

### 方法2: 系统环境变量

```bash
export AI_PROVIDER=deepseek
export DEEPSEEK_API_KEY=your_deepseek_api_key_here
export DEEPSEEK_MODEL=deepseek-chat
export DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
export AI_MAX_TOKENS=4000
export AI_TEMPERATURE=0.3
```

## 📋 配置参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `AI_PROVIDER` | AI提供商 | `deepseek` |
| `DEEPSEEK_API_KEY` | DeepSeek API密钥 | 必填 |
| `DEEPSEEK_MODEL` | 模型名称 | `deepseek-chat` |
| `DEEPSEEK_BASE_URL` | API基础URL | `https://api.deepseek.com/v1` |
| `OPENAI_API_KEY` | OpenAI API密钥 | 必填 |
| `OPENAI_MODEL` | 模型名称 | `gpt-4` |
| `OPENAI_BASE_URL` | API基础URL | `https://api.openai.com/v1` |
| `AI_MAX_TOKENS` | 最大生成token数 | `4000` |
| `AI_TEMPERATURE` | 生成随机性 | `0.3` |

### AI提供商选择
- `AI_PROVIDER=openai` - 使用OpenAI API
- `AI_PROVIDER=deepseek` - 使用DeepSeek API

### DeepSeek配置
- `DEEPSEEK_API_KEY` - DeepSeek API密钥
- `DEEPSEEK_MODEL` - 模型名称 (推荐: `deepseek-chat`)
- `DEEPSEEK_BASE_URL` - API基础URL (默认: `https://api.deepseek.com/v1`)

### OpenAI配置
- `OPENAI_API_KEY` - OpenAI API密钥
- `OPENAI_MODEL` - 模型名称 (推荐: `gpt-4`)
- `OPENAI_BASE_URL` - API基础URL (默认: `https://api.openai.com/v1`)

### 通用配置
- `AI_MAX_TOKENS` - 最大生成token数 (默认: 4000)
- `AI_TEMPERATURE` - 生成随机性 (0.0-1.0, 默认: 0.3)

## 🚀 快速配置指南

### DeepSeek配置 (推荐)

1. **获取API密钥**:
   - 访问 [DeepSeek官网](https://platform.deepseek.com/)
   - 注册账号并获取API密钥

2. **创建配置文件**:
   ```bash
   # 创建.env文件
   cat > .env << EOF
   AI_PROVIDER=deepseek
   DEEPSEEK_API_KEY=your_actual_deepseek_api_key
   DEEPSEEK_MODEL=deepseek-chat
   DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
   AI_MAX_TOKENS=4000
   AI_TEMPERATURE=0.3
   EOF
   ```

3. **验证配置**:
   ```bash
   source .venv/bin/activate
   python main.py status
   ```

4. **测试功能**:
   ```bash
   # 测试质量评分
   python main.py score --text "This is a test paper for DeepSeek API."
   
   # 启动Web界面
   streamlit run app.py
   ```

### OpenAI配置

1. **获取API密钥**:
   - 访问 [OpenAI官网](https://platform.openai.com/)
   - 注册账号并获取API密钥

2. **创建配置文件**:
   ```bash
   # 创建.env文件
   cat > .env << EOF
   AI_PROVIDER=openai
   OPENAI_API_KEY=your_actual_openai_api_key
   OPENAI_MODEL=gpt-4
   OPENAI_BASE_URL=https://api.openai.com/v1
   AI_MAX_TOKENS=4000
   AI_TEMPERATURE=0.3
   EOF
   ```

## 🔄 切换AI提供商

### 切换到OpenAI
```bash
# 修改.env文件
sed -i 's/AI_PROVIDER=deepseek/AI_PROVIDER=openai/' .env
sed -i 's/DEEPSEEK_API_KEY=/OPENAI_API_KEY=/' .env
sed -i 's/DEEPSEEK_MODEL=/OPENAI_MODEL=gpt-4/' .env
sed -i 's/DEEPSEEK_BASE_URL=/OPENAI_BASE_URL=https:\/\/api.openai.com\/v1/' .env
```

### 切换回DeepSeek
```bash
# 修改.env文件
sed -i 's/AI_PROVIDER=openai/AI_PROVIDER=deepseek/' .env
sed -i 's/OPENAI_API_KEY=/DEEPSEEK_API_KEY=/' .env
sed -i 's/OPENAI_MODEL=/DEEPSEEK_MODEL=deepseek-chat/' .env
sed -i 's/OPENAI_BASE_URL=/DEEPSEEK_BASE_URL=https:\/\/api.deepseek.com\/v1/' .env
```

## 🔍 验证配置

运行以下命令检查配置是否正确：

```bash
source .venv/bin/activate
python main.py status
```

如果配置正确，您会看到：
```
✅ 使用 DEEPSEEK API
   模型: deepseek-chat
   Base URL: https://api.deepseek.com/v1
```

或者：
```
✅ 使用 OPENAI API
   模型: gpt-4
   Base URL: https://api.openai.com/v1
```

## 🛠️ 故障排除

### 常见问题

1. **API密钥无效**:
   - 检查API密钥是否正确
   - 确认账户有足够的余额
   - 验证密钥是否已激活

2. **网络连接问题**:
   - 检查网络连接
   - 确认API URL是否正确
   - 检查防火墙设置

3. **模型不可用**:
   - 确认模型名称正确
   - 检查API提供商是否支持该模型
   - 验证账户权限

4. **Token限制**:
   - 检查max_tokens设置是否合理
   - 确认账户token配额是否充足

### 测试连接

```bash
# 检查系统状态
python main.py status

# 测试质量评分
python main.py score --text "Test paper content"

# 如果成功，说明API配置正确
```

## 💡 使用建议

### 性能对比

| 特性 | DeepSeek | OpenAI |
|------|----------|---------|
| **性价比** | ⭐⭐⭐⭐⭐ 更高 | ⭐⭐⭐ 较低 |
| **质量** | ⭐⭐⭐⭐ 很好 | ⭐⭐⭐⭐⭐ 优秀 |
| **速度** | ⭐⭐⭐⭐⭐ 更快 | ⭐⭐⭐ 一般 |
| **稳定性** | ⭐⭐⭐⭐ 很好 | ⭐⭐⭐⭐⭐ 优秀 |
| **中文支持** | ⭐⭐⭐⭐⭐ 优秀 | ⭐⭐⭐⭐ 很好 |

### 推荐配置

#### DeepSeek配置 (性价比高，推荐)
```bash
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_key
DEEPSEEK_MODEL=deepseek-chat
AI_MAX_TOKENS=4000
AI_TEMPERATURE=0.3
```

#### OpenAI配置 (质量更高)
```bash
AI_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4
AI_MAX_TOKENS=4000
AI_TEMPERATURE=0.3
```

## 🎯 使用场景推荐

### 选择DeepSeek的场景
- 预算有限，需要高性价比
- 对中文处理要求较高
- 需要快速响应
- 日常使用和实验

### 选择OpenAI的场景
- 对质量要求极高
- 需要最稳定的服务
- 处理复杂学术内容
- 正式论文润色

---

配置完成后，您就可以享受智能论文润色的强大功能了！🎉

**推荐**: 首次使用建议选择DeepSeek，性价比更高，中文支持更好。