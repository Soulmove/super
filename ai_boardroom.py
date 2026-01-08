import os
import json
import time
from datetime import datetime
from google import genai
from google.genai import types

import archive_manager
from personas_config import SYSTEM_PROMPT_SOVEREIGN

# ================= 🔧 配置区域 =================
if os.environ.get("GITHUB_ACTIONS"):
    print("☁️ 检测到云端环境：禁用代理，使用直连...")
else:
    print("🏠 检测到本地环境：启用代理 17890...")
    PROXY_PORT = "17890"
    os.environ["HTTP_PROXY"] = f"http://127.0.0.1:{PROXY_PORT}"
    os.environ["HTTPS_PROXY"] = f"http://127.0.0.1:{PROXY_PORT}"

# 使用性能较好的模型进行决策分析
MODEL_NAME = "gemini-2.0-flash-exp"

# 板块文件配置
FILES_CONFIG = {
    "finance": { "in": "data_finance.json", "name": "财经/市场", "key_env": "KEY_FINANCE" },
    "global": { "in": "data_global.json",  "name": "国际/宏观", "key_env": "KEY_GLOBAL" },
    "tech": { "in": "data_tech.json",    "name": "科技/AI",   "key_env": "KEY_TECH" },
    "general": { "in": "data_general.json", "name": "综合/娱乐", "key_env": "KEY_GENERAL" }
}

def get_client(key_env):
    """
    初始化 AI 客户端，按优先级尝试不同的 API Key
    """
    # 1. 尝试板块对应的专属 Key
    api_key = os.environ.get(key_env)
    
    # 2. 如果没找到，尝试常见的几个通用环境变量
    if not api_key:
        possible_keys = ["GOOGLE_API_KEY", "KEY_1", "KEY_2", "KEY_3", "KEY_4", "KEY_5", "KEY_6", "KEY_7", "KEY_8"]
        for k in possible_keys:
            val = os.environ.get(k)
            if val:
                api_key = val
                break
    
    if not api_key:
        return None
    return genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})

def load_data_titles(filepath, limit=100):
    """
    从 JSON 文件中加载标题列表，用于 AI 分析
    """
    if not os.path.exists(filepath): return []
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    titles = []
    count = 0
    for platform in data:
        items = platform.get('items', [])
        for item in items:
            title = item.get('title', '').strip()
            if title:
                titles.append(f"- {title}")
                count += 1
            if count >= limit: break
    return titles

def generate_boardroom_report(sector_name, titles):
    """
    召唤董事会 AI 进行激辩并生成战略裁决报告
    """
    client = get_client(FILES_CONFIG.get(sector_name, {}).get("key_env", "GOOGLE_API_KEY"))
    if not client:
        print(f"❌ 找不到用于 {sector_name} 板块的 API Key")
        return None

    # 构建任务提示词 (Prompt)
    # 我们要求模型分析整个新闻流，选出核心信号，进行分身辩论，最后由董事长给出裁决
    news_feed = "\n".join(titles)
    
    prompt = f"""
    {SYSTEM_PROMPT_SOVEREIGN}

    ---
    **当前任务 (Mission)**
    你现在正在主持【{sector_name}】板块的董事会战略分析会议。
    日期: {datetime.now().strftime("%Y-%m-%d")}

    **输入情报 (Incoming Intel)**:
    {news_feed}

    **执行指令**:
    1.  **Step 1: 信号筛选**: 从上述情报中，筛选出 **Top 5** 最具战略价值、最值得讨论的“关键信号”（可以将相似新闻合并）。
    2.  **Step 2: 董事会辩论**: 针对每个关键信号，激活 3-4 个分身进行犀利点评。
    3.  **Step 3: 董事长裁决**: 针对每个信号给出最终裁决。
    4.  **Step 4: 生成报告**: 将结果汇总为一份 **Markdown 格式** 的战略报告。

    **输出格式要求 (Markdown)**:
    报告标题必须是：`# 🏛️ Sovereign 战略裁决报告：{sector_name}分部`
    
    结构如下：
    
    # 🏛️ Sovereign 战略裁决报告：{sector_name}分部
    > 📅 日期：YYYY-MM-DD | 🧠 核心模型：Sovereign-v1 | 🛡️ 密级：机密

    ## 🚨 Alpha Signals (关键信号裁决)

    ### 1. [信号标题]
    **💬 董事会激辩**
    *   **[分身A]**：观点...
    *   **[分身B]**：观点...
    
    **👨‍⚖️ 董事长裁决 (The Verdict)**
    *   **👁️ 真相层**：...
    *   **⏳ 时间差**：...
    *   **⚔️ 行动建议**：
        *   🔴 **激进 (High Risk)**：...
        *   🔵 **保守 (Low Risk)**：...

    (重复 1-5 个信号...)

    ---
    ## 📉 风险与黑天鹅预警
    *   ...

    ## 📝 董事长最终结语
    (一段话总结今天的市场/局势，充满哲理和洞察力)
    """

    try:
        print(f"🧠 {sector_name}: 正在召开虚拟董事会会议 (AI 生成中)...")
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=1.0, # 保持较高的随机性以确保辩论的精彩程度
            )
        )
        return response.text
    except Exception as e:
        print(f"❌ 生成 {sector_name} 报告时发生错误: {e}")
        return None

def run_boardroom():
    """
    董事会运行主逻辑：归档旧数据 -> 生成各版块报告 -> 更新前端索引
    """
    print("🚀 Sovereign AI Boardroom 正在启动...")
    archive_manager.init_dirs()
    
    # 1. 首先归档原始数据
    raw_files = [cfg['in'] for cfg in FILES_CONFIG.values()]
    archive_manager.archive_daily_data(raw_files)
    
    # 2. 遍历处理每个板块
    for key, config in FILES_CONFIG.items():
        titles = load_data_titles(config['in'])
        if not titles:
            print(f"⚠️ 跳过 {key}: 未找到对应数据文件。")
            continue
            
        report_content = generate_boardroom_report(key, titles)
        if report_content:
            # 清理 Markdown 代码块包裹符
            if report_content.startswith("```markdown"):
                report_content = report_content.replace("```markdown", "", 1)
            if report_content.startswith("```"):
                report_content = report_content.replace("```", "", 1)
            if report_content.endswith("```"):
                report_content = report_content[:-3]
                
            # 保存报告并存档
            report_path = archive_manager.save_report(key, report_content)
            print(f"✅ 报告已保存: {report_path}")
            
        time.sleep(5) # 防止触发 API 频率限制

    # 3. 更新历史记录索引，供前端调用数据
    archive_manager.update_history_index()
    print("📅 历史索引已更新，系统运行完毕。")

if __name__ == "__main__":
    run_boardroom()
