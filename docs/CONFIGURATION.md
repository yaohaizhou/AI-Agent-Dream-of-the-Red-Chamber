# 配置说明

## 环境变量配置

### 1. 创建 .env 文件

在项目根目录下创建 `config/.env` 文件：

```bash
# 在项目根目录执行
touch config/.env
```

### 2. 配置内容

在 `.env` 文件中添加以下配置：

```env
# OpenAI API配置
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1

# 项目配置
DEBUG_MODE=false
LOG_LEVEL=INFO
```

### 3. 如何获取 OpenAI API Key

1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 登录您的账户
3. 进入 API Keys 页面
4. 创建新的 API Key
5. 复制生成的 Key 并粘贴到 `.env` 文件中

### 4. 替代配置方式

如果无法创建 `.env` 文件，您也可以：

#### 方法1：系统环境变量
```bash
export OPENAI_API_KEY="sk-your-key-here"
export OPENAI_BASE_URL="https://api.openai.com/v1"
```

#### 方法2：直接在 settings.yaml 中配置
```yaml
adk:
  api_key: "sk-your-key-here"
  base_url: "https://api.openai.com/v1"
```

### 5. 验证配置

运行以下命令验证配置是否正确：

```bash
python src/cli/main.py status
```

如果看到类似以下输出，说明配置成功：
```
✅ 已加载配置文件: /path/to/config/.env
✅ 已读取 OPENAI_API_KEY
✅ 已读取 OPENAI_BASE_URL
```

### 6. 安全注意事项

⚠️ **重要安全提醒**：

1. **不要将 `.env` 文件提交到版本控制系统**
2. **不要与他人分享您的 API Key**
3. **定期轮换 API Key**
4. **监控 API 使用情况和费用**

### 7. 故障排除

#### 问题：`未找到 OPENAI_API_KEY 环境变量`
**解决方案**：
1. 检查 `.env` 文件是否存在
2. 检查文件路径是否正确
3. 检查变量名是否拼写正确
4. 尝试重启终端或 IDE

#### 问题：`API 调用失败`
**解决方案**：
1. 验证 API Key 是否有效
2. 检查网络连接
3. 确认 API 余额充足
4. 检查 Base URL 是否正确

### 8. 高级配置

#### 自定义模型配置
```yaml
model:
  model_name: "gpt-5"
  temperature: 0.8
  max_length: 100000
```

#### 质量评估配置
```yaml
quality:
  style_weight: 0.3
  character_weight: 0.3
  plot_weight: 0.25
  literary_weight: 0.15
  min_score_threshold: 7.0
```

### 9. 使用 GPT-5 以外的模型

如果您想使用其他兼容 OpenAI API 的服务：

```env
# 使用其他服务提供商
OPENAI_BASE_URL=https://your-custom-api-endpoint.com/v1
OPENAI_API_KEY=your-custom-api-key
```

支持的服务包括：
- OpenAI
- Azure OpenAI
- 其他兼容 OpenAI API 的服务
