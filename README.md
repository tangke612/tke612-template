# tke612-template
The template repository for the tke612 course on Learning Lab.
# Subtitle Translator (中英文双语字幕生成脚本)

一个用于将字幕文件（SRT 或 ASS）自动翻译为中英文对照格式的 Python 脚本。  
脚本支持自动清洗文件名以匹配 TMDB 的影视信息，仅保留剧名进行搜索。  
翻译采用 OpenAI API，输出双语字幕文件，保持时间轴与原字幕一致。

---

## ✨ 功能特性
- ✅ 自动识别并读取 `.srt` / `.ass` 文件  
- ✅ 每 100 句批量翻译，保证效率与稳定性  
- ✅ 输出 **中英文对照字幕**（如 `input_zh.srt`）  
- ✅ 保留原始时间轴与格式  
- ✅ 自动提取文件名中的剧名用于 TMDB 查询（剔除分辨率、集数、年份等无关信息）  
- ✅ 错误提示与重试机制  

---

## ⚙️ 使用方法

### 1️⃣ 安装依赖
确保已安装 Python 3.9+  
在终端执行以下命令安装依赖：
```bash
pip install openai tmdbsimple tqdm
