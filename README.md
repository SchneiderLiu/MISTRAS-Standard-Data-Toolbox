# MISTRAS Standard Data Toolbox

基于 PyQt5 + [qfluentwidgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) 的声发射（Acoustic Emission）数据处理图形化工具。

直接从 Mistras / Physical Acoustics 的 `.DTA` 二进制文件中读取 AE hit 数据，提供滤波、可视化和导出功能，无需依赖 AEwin 软件。

---

## 功能模块

| 模块 | 功能 |
|---|---|
| **DTA 导入导出** | 读取 PAC AEwin .DTA 文件，预览 hit 特征表，导出为 CSV |
| **数据滤波** | 按振幅下限、时间范围、通道多选过滤噪声信号 |
| **绘图** | 振铃计数 + 累计曲线（双轴）、振幅分布直方图、3D 空间分布 |

## 快速开始

### 环境要求

- Python 3.9+
- Windows 10 / 11

### 安装

```bash
# 克隆仓库
git clone https://github.com/your-username/MISTRAS_Standard_Data_Toolbox.git
cd MISTRAS_Standard_Data_Toolbox

# 安装依赖
pip install -r requirements.txt
```

### 运行

```bash
python main.py
```

### 打包为 exe

```bash
pip install pyinstaller
pyinstaller --onedir --windowed --icon favicon.ico --name "MISTRAS_Toolbox" main.py
```

打包后的 exe 位于 `dist/MISTRAS_Toolbox/` 目录下。

---

## 使用流程

```
.DTA 文件 → 模块1: 导入预览 → 导出 CSV
                      ↓ 共享数据
                  模块2: 滤波 → 导出 CSV
                      ↓ 共享数据
                  模块3: 绘图 → 保存 PNG/PDF/SVG
```

三个模块之间通过共享数据通道自动传递，读取 .DTA 后切换到其他模块即可直接使用，无需重复加载。

## 数据列说明

| 中文列名 | 原始字段 | 含义 | 单位 |
|---|---|---|---|
| 相对时间 | SSSSSSS.mmmuuun | 距测试开始时间 | 秒 |
| 通道 | CH | 传感器通道号 | — |
| 上升时间 | RISE | 信号上升时间 | μs |
| 振铃计数 | PCNTS | 振铃计数（阈值穿越次数） | — |
| 持续计数 | COUN | 持续计数 | — |
| 能量 | ENER | 能量 | — |
| 持续时间 | DURATION | 信号持续时间 | μs |
| 振幅 | AMP | 峰值振幅 | dB |
| 平均信号电平 | ASL | 平均信号电平 | dB |
| 阈值 | THR | 触发阈值 | dB |
| 平均频率 | A-FRQ | 平均频率 | kHz |
| 均方根电压 | RMS | 均方根电压 | V |
| 信号强度 | SIG STRENGTH | 信号强度 | pV·s |
| 绝对能量 | ABS-ENERGY | 绝对能量 | aJ |

## 技术栈

- **PyQt5** — Qt 界面框架
- **qfluentwidgets** — Fluent Design 风格组件库
- **matplotlib** — 数据可视化
- **pandas / numpy** — 数据处理
- **MistrasDTA** — .DTA 文件解析引擎

## 许可证

MIT
