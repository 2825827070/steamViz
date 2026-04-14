# SteamViz - Steam游戏数据分析器

一款基于 PyQt5 的 Steam 游戏数据可视化分析工具，支持官方渠道的数据获取与可视化。

## 功能特性

### 数据获取
- **Steam 官方 API**: 获取游戏详情、评分、评论
- **SteamSpy API**: 批量获取游戏统计数据
- **按名搜索**: 支持按游戏名称搜索同步数据
- **增量更新**: 避免重复爬取已同步数据

### 数据可视化
- **数据概览**: 仪表盘展示游戏总数、平均价格、好评率等核心指标
- **游戏列表**: 完整的游戏数据库浏览和搜索
- **用户评价**: 查看游戏评论详情
- **数据管理**: 数据同步控制面板

### 主题支持
- **深色模式**: 默认暗色主题，护眼舒适
- **浅色模式**: 明亮主题，清晰易读
- **一键切换**: 顶部工具栏快速切换

## 安装说明

### 环境要求
- Windows 10/11 操作系统
- Python 3.8 或更高版本
- 网络连接（用于数据爬取）

### 开发环境安装

#### 1. 克隆或下载项目
```bash
git clone https://github.com/2825827070/steamViz
cd SteamViz
```

#### 2. 创建虚拟环境（推荐）
```bash
# Windows
python -m venv steam_viz_env
steam_viz_env\Scripts\activate

# 或使用 conda
conda create -n steamviz python=3.12
conda activate steamviz
```

#### 3. 安装依赖
```bash
pip install -r requirements.txt
```

**依赖包清单：**
- PyQt5 >= 5.15 - GUI 框架
- pandas >= 1.5 - 数据处理
- numpy >= 1.21 - 数值计算
- requests >= 2.28 - 网络请求
- matplotlib >= 3.5 - 图表绘制

### 打包版本安装

项目提供了打包好的可执行文件可以直接运行，数据基于sqlite存储在 `data/steam_games.db` 文件中。

## 使用说明

### 启动程序

#### 开发环境
```bash
python main.py
```

#### 打包版本
dist文件夹内直接双击运行 `SteamViz.exe`

### 界面导航

程序主界面包含以下功能模块：

1. **数据概览** - 可视化仪表盘
   - 游戏总数统计
   - 平均价格分析
   - 好评率分布
   - 总评价数统计

2. **游戏列表** - 数据浏览
   - 完整游戏数据库
   - 支持搜索和筛选
   - 排序功能（好评数、价格等）

3. **用户评价** - 评论数据
   - 查看游戏用户评论
   - 评论情感分析
   - 多语言支持

4. **数据管理** - 爬虫控制
   - 批量同步数据
   - 搜索特定游戏
   - 数据清理功能
   - 同步日志查看

### 主题切换

点击窗口右上角的 **☀/🌙** 按钮可在深色/浅色主题间切换。

### 窗口控制

- **最小化**: 点击标题栏的「⎯」按钮
- **最大化/还原**: 点击标题栏的「⬜」按钮 或 双击标题栏
- **关闭**: 点击标题栏的「✕」按钮 或 Alt+F4

## 项目结构

```
SteamViz/
├── main.py                  # 程序入口
├── requirements.txt         # Python 依赖
├── steam_viz.spec          # PyInstaller 打包配置
├── data/                   # 数据目录
│   ├── steam_games.db      # SQLite 数据库
│   └── debug.log           # 运行日志
├── src/                    # 源代码
│   ├── __init__.py
│   ├── ui/                 # UI 界面模块
│   │   ├── main_window.py  # 主窗口
│   │   ├── visual_hub.py   # 可视化页面
│   │   ├── data_page.py    # 数据管理页面
│   │   ├── styles.py       # 主题样式
│   │   └── ...
│   ├── data/               # 数据模块
│   │   ├── database.py     # SQLite 数据库操作
│   │   └── crawler.py      # Steam 数据爬虫
│   └── charts/             # 图表模块
│       ├── matplotlib_widget.py
│       └── echarts_widget.py
├── icon/                   # 图标资源
└── build/                  # 打包输出目录
```


## 日志查看

程序运行日志保存在 `data/debug.log`，可用于排查问题。

## 开源协议

本项目仅供学习和研究使用。

## 技术栈

- **GUI 框架**: PyQt5
- **数据存储**: SQLite3
- **网络请求**: requests
- **数据处理**: pandas, numpy
- **数据可视化**: matplotlib
- **打包工具**: PyInstaller
