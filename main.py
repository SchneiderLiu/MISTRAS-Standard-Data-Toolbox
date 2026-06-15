#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MISTRAS Standard Data Toolbox
============================
基于 PyQt5 + qfluentwidgets 的声发射数据处理图形化工具。

模块:
  1. DTA 导入导出 - 读取 .DTA 文件，导出为 CSV
  2. 数据滤波     - 振幅/时间/通道过滤
  3. 绘图         - 振铃计数、累计曲线、3D 分布等

启动: python main.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

from qfluentwidgets import setTheme, Theme

import matplotlib.pyplot as plt

# ── matplotlib 中文字体 ────────────────────────────
for _f in ["Microsoft YaHei", "SimHei", "DengXian"]:
    try:
        plt.rcParams["font.family"] = _f
        plt.rcParams["axes.unicode_minus"] = False
        break
    except Exception:
        continue


from app.main_window import MainWindow


def main():
    # 高 DPI 适配
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    app.setApplicationName("MISTRAS Standard Data Toolbox")
    app.setOrganizationName("AE Lab")

    # 全局中文字体
    f = QFont("Microsoft YaHei", 9)
    f.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(f)

    # 跟随系统主题
    setTheme(Theme.AUTO)

    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    from PyQt5.QtCore import Qt
    main()
