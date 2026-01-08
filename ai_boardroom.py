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
    # --- 🧠 智能重试机制 ---
    # 定义 Key 池：优先使用专属 Key，失败则轮询通用 Key 池
    primary_key_env = FILES_CONFIG.get(sector_name, {}).get("key_env")
    primary_key = os.environ.get(primary_key_env) if primary_key_env else None
    
    # 构建所有可用 Key 的列表
    candidate_keys = []
    if primary_key: candidate_keys.append(primary_key)
    candidate_keys.append(os.environ.get("GOOGLE_API_KEY"))
    for i in range(1, 9):
        k = os.environ.get(f"KEY_{i}")
        if k: candidate_keys.append(k)
        
    # 去重并过滤空值
    candidate_keys = list(set([k for k in candidate_keys if k]))
    
    if not candidate_keys:
        print(f"❌ 找不到用于 {sector_name} 的任何 API Key")
        return None

    # 开始尝试
    for attempt, api_key in enumerate(candidate_keys):
        try:
            print(f"🧠 {sector_name}: 正在尝试 Key [{attempt+1}/{len(candidate_keys)}] (AI 生成中)...")
            
            client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
            
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=1.0, 
                )
            )
            return response.text
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print(f"⚠️ Key [{attempt+1}] 额度耗尽 (429)，正在切换下一个...")
                time.sleep(2) # 稍微冷却切换
                continue
            else:
                # 其他错误直接抛出
                print(f"❌ 生成 {sector_name} 报告时发生非 429 错误: {e}")
                return None
    
    print(f"❌ {sector_name}: 所有可用 Key ({len(candidate_keys)} 个) 均已耗尽额度或失败。")
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
