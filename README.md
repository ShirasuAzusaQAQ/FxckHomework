# FxxkHomework

一个本地 Python 小软件，用于编辑学生假期作业文档（`.docx`）：

- 用户提供答案时：按答案填入作业文档
- 用户未提供答案时：自动调用 AI（通过 API Key）生成答案并填入

## 功能说明

- 支持 `.docx` 作业文档
- 支持两种填写方式：
  - 模板占位符替换（如 `{{Q1}}`、`{{1}}`）
  - 识别题号后在题目后追加 `答案：...`
- 支持从文本框或文件导入答案
- 缺失答案时可自动调用 AI 解题
- 提供图形界面（Tkinter）和命令行（CLI）

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 启动图形界面

```bash
python3 main.py
```

## 命令行用法

```bash
python3 main.py \
  --input homework.docx \
  --output homework_filled.docx \
  --answers-file answers.txt \
  --auto-solve-missing \
  --api-key sk-xxx \
  --model gpt-4.1-mini
```

### `answers.txt` 示例

支持以下任一格式（可混用）：

```txt
1=答案一
2: 答案二
3. 答案三
题4：答案四
```

也支持 JSON 文件：

```json
{
  "1": "答案一",
  "2": "答案二"
}
```

## 文档模板建议（更稳定）

如果你能控制作业模板，推荐使用占位符：

- `第1题：...... {{Q1}}`
- `第2题：...... {{Q2}}`

这样程序会直接替换占位符，格式更稳定。

## AI 接口说明

默认按 OpenAI 兼容接口调用：

- Base URL 默认：`https://api.openai.com/v1`
- Endpoint：`/chat/completions`

如果你使用的是其他兼容服务（如代理/中转），可以在界面或参数里改 `Base URL`。

## 注意事项

- 当前版本主要针对文字题、简答题、填空题
- 对复杂公式、图片题、手写扫描件不适用
- 若文档没有明显题号或占位符，程序会尽量匹配，但可能需要手动调整模板

