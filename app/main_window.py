#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口 — 基于 FluentWindow 的导航界面。
所有三个模块的 UI 均在此文件中实现。
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.ticker as ticker
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFileDialog, QListWidget, QListWidgetItem, QCheckBox,
    QAbstractItemView, QTableWidgetItem, QGroupBox)
from PyQt5.QtGui import QFont

from qfluentwidgets import (
    FluentWindow, FluentIcon, NavigationItemPosition,
    PushButton, PrimaryPushButton, TableWidget, SpinBox,
    DoubleSpinBox, ComboBox, ListWidget,
    InfoBar, TitleLabel, BodyLabel, setTheme, Theme,
    isDarkTheme, setThemeColor, MessageBox)

from app.dta_reader import read_dta, export_csv as dta_export_csv


# ── 全局共享数据 ──────────────────────────────────
class SharedData:
    df = None
    source = ""

_shared = SharedData()


# ── 工具函数 ──────────────────────────────────────
def _col(df, keyword):
    cols = [c for c in df.columns if keyword in c]
    return cols[0] if cols else None


def _fill_table(table, df, max_rows=100):
    table.clear()
    cols = list(df.columns)
    table.setColumnCount(len(cols))
    table.setHorizontalHeaderLabels(cols)
    rows = min(len(df), max_rows)
    table.setRowCount(rows)
    for r in range(rows):
        for c, col in enumerate(cols):
            val = df.iloc[r, c]
            text = f"{val:.4f}" if isinstance(val, float) else str(val)
            item = QTableWidgetItem(text)
            table.setItem(r, c, item)
    table.resizeColumnsToContents()


# ══════════════════════════════════════════════════
#  模块1: DTA 导入导出
# ══════════════════════════════════════════════════

class _ReadThread(QThread):
    finished = pyqtSignal(object, object, str)
    error = pyqtSignal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        try:
            df, wfm = read_dta(self.path)
            self.finished.emit(df, wfm, self.path)
        except Exception as e:
            self.error.emit(str(e))


class ImportPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("import_page")
        self._df = None
        self._source = ""
        self._build_ui()

    def _build_ui(self):
        lo = QVBoxLayout(self)
        lo.setSpacing(12)

        lo.addWidget(TitleLabel("DTA 导入导出"))
        lo.addWidget(BodyLabel("读取 PAC AEwin .DTA 文件，预览并导出为 CSV。"))

        # 文件选择
        row1 = QHBoxLayout()
        self.btn_sel = PushButton(FluentIcon.FOLDER, "选择 .DTA 文件")
        self.btn_sel.clicked.connect(self._select)
        row1.addWidget(self.btn_sel)
        self.lbl_file = BodyLabel("未选择文件")
        row1.addWidget(self.lbl_file, 1)
        self.btn_read = PushButton(FluentIcon.PLAY, "读取")
        self.btn_read.setEnabled(False)
        self.btn_read.clicked.connect(self._read)
        row1.addWidget(self.btn_read)
        lo.addLayout(row1)

        # 预览表格
        self.table = TableWidget(self)
        self.table.setAlternatingRowColors(True)
        self.table.setBorderVisible(True)
        lo.addWidget(self.table, 1)

        # 导出行
        row2 = QHBoxLayout()
        self.lbl_info = BodyLabel("请先读取 .DTA 文件")
        row2.addWidget(self.lbl_info, 1)
        self.cb_amp = QCheckBox("振幅 ≥")
        self.spin_amp = SpinBox()
        self.spin_amp.setRange(40, 90)
        self.spin_amp.setValue(45)
        self.spin_amp.setSuffix(" dB")
        self.spin_amp.setVisible(False)
        self.cb_amp.toggled.connect(self.spin_amp.setVisible)
        row2.addWidget(self.cb_amp)
        row2.addWidget(self.spin_amp)
        self.btn_exp = PrimaryPushButton(FluentIcon.SAVE, "导出 CSV")
        self.btn_exp.setEnabled(False)
        self.btn_exp.clicked.connect(self._export)
        row2.addWidget(self.btn_exp)
        lo.addLayout(row2)

    def _select(self):
        fp, _ = QFileDialog.getOpenFileName(
            self, "选择 .DTA 文件", "", "DTA 文件 (*.dta *.DTA);;所有文件 (*)")
        if fp:
            self._path = fp
            self.lbl_file.setText(Path(fp).name)
            self.btn_read.setEnabled(True)
            self.btn_exp.setEnabled(False)

    def _read(self):
        if not hasattr(self, '_path'):
            return
        self.btn_read.setEnabled(False)
        self.btn_sel.setEnabled(False)
        self.lbl_info.setText("正在读取...")
        self._thread = _ReadThread(self._path)
        self._thread.finished.connect(self._on_done)
        self._thread.error.connect(lambda e: InfoBar.error("读取失败", e, parent=self))
        self._thread.start()

    def _on_done(self, df, wfm, fp):
        try:
            self._thread = None
            self.btn_read.setEnabled(True)
            self.btn_sel.setEnabled(True)
            if df is None or len(df) == 0:
                self.lbl_info.setText("未读取到 hit 数据")
                return
            self._df = df
            self._source = Path(fp).name
            _shared.df = df
            _shared.source = self._source
            _fill_table(self.table, df)
            amp = _col(df, "振幅")
            a = f" | 振幅 {df[amp].min():.0f}-{df[amp].max():.0f} dB" if amp else ""
            self.lbl_info.setText(
                f"{len(df)} hits | {df['通道 CH'].nunique()} 通道"
                f" | {df['相对时间(秒) Relative_Time_S'].min():.1f}-"
                f"{df['相对时间(秒) Relative_Time_S'].max():.1f}s{a}")
            self.btn_exp.setEnabled(True)
        except Exception as e:
            import traceback; traceback.print_exc()
            InfoBar.error("处理失败", str(e), parent=self)
            self.btn_read.setEnabled(True)
            self.btn_sel.setEnabled(True)

    def _export(self):
        if self._df is None:
            return
        name = Path(self._source).stem + ".csv"
        fp, _ = QFileDialog.getSaveFileName(self, "导出 CSV", name, "CSV (*.csv)")
        if not fp:
            return
        n = dta_export_csv(
            self._df, fp,
            amp_min=self.spin_amp.value() if self.cb_amp.isChecked() else 0)
        InfoBar.success("导出成功", f"{n} 条记录 → {Path(fp).name}", parent=self)


# ══════════════════════════════════════════════════
#  模块2: 数据滤波
# ══════════════════════════════════════════════════

class FilterPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("filter_page")
        self._df = None
        self._orig = None
        self._activated = False
        self._build_ui()

    def _build_ui(self):
        lo = QVBoxLayout(self)
        lo.setSpacing(12)

        lo.addWidget(TitleLabel("数据滤波"))
        lo.addWidget(BodyLabel("按振幅、时间范围、通道过滤数据。"))

        # 数据来源
        r1 = QHBoxLayout()
        self.btn_load = PushButton(FluentIcon.DOCUMENT, "加载 CSV")
        self.btn_load.clicked.connect(self._load)
        r1.addWidget(self.btn_load)
        self.btn_use = PushButton(FluentIcon.SHARE, "使用主窗口数据")
        self.btn_use.clicked.connect(self._use_shared)
        r1.addWidget(self.btn_use)
        self.lbl_src = BodyLabel("未加载")
        r1.addWidget(self.lbl_src, 1)
        lo.addLayout(r1)

        # 滤波参数
        g = QGroupBox("滤波参数")
        gb = QHBoxLayout(g)

        vb = QVBoxLayout()
        vb.addWidget(BodyLabel("振幅 ≥"))
        self.spin_amp = SpinBox()
        self.spin_amp.setRange(40, 90)
        self.spin_amp.setValue(45)
        self.spin_amp.setSuffix(" dB")
        vb.addWidget(self.spin_amp)
        gb.addLayout(vb)

        vb2 = QVBoxLayout()
        vb2.addWidget(BodyLabel("时间范围"))
        hr = QHBoxLayout()
        self.spin_tmin = DoubleSpinBox()
        self.spin_tmin.setRange(0, 99999)
        self.spin_tmin.setDecimals(1)
        hr.addWidget(self.spin_tmin)
        hr.addWidget(BodyLabel("~"))
        self.spin_tmax = DoubleSpinBox()
        self.spin_tmax.setRange(0, 99999)
        self.spin_tmax.setDecimals(1)
        self.spin_tmax.setValue(99999)
        hr.addWidget(self.spin_tmax)
        vb2.addLayout(hr)
        gb.addLayout(vb2)

        vb3 = QVBoxLayout()
        vb3.addWidget(BodyLabel("通道 (多选)"))
        self.ch_list = ListWidget()
        self.ch_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.ch_list.setMaximumHeight(72)
        vb3.addWidget(self.ch_list)
        gb.addLayout(vb3)

        self.btn_apply = PrimaryPushButton(FluentIcon.ACCEPT, "应用滤波")
        self.btn_apply.setEnabled(False)
        self.btn_apply.clicked.connect(self._apply)
        gb.addWidget(self.btn_apply)
        self.btn_reset = PushButton(FluentIcon.CANCEL, "重置")
        self.btn_reset.setEnabled(False)
        self.btn_reset.clicked.connect(self._reset)
        gb.addWidget(self.btn_reset)
        lo.addWidget(g)

        # 预览
        self.lbl_info = BodyLabel("")
        lo.addWidget(self.lbl_info)
        self.table = TableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setBorderVisible(True)
        lo.addWidget(self.table, 1)

        # 导出
        r2 = QHBoxLayout()
        r2.addStretch()
        self.btn_exp = PrimaryPushButton(FluentIcon.SAVE, "导出滤波后 CSV")
        self.btn_exp.setEnabled(False)
        self.btn_exp.clicked.connect(self._export)
        r2.addWidget(self.btn_exp)
        lo.addLayout(r2)

    def activate(self):
        if _shared.df is not None and self._df is None:
            self._load_df(_shared.df.copy(), _shared.source)

    def _load(self):
        fp, _ = QFileDialog.getOpenFileName(self, "加载 CSV", "", "CSV (*.csv)")
        if not fp:
            return
        try:
            df = pd.read_csv(fp, encoding="utf-8-sig")
            self._load_df(df, Path(fp).name)
        except Exception as e:
            InfoBar.error("加载失败", str(e), parent=self)

    def _use_shared(self):
        if _shared.df is None:
            InfoBar.warning("无数据", "请先在模块1中读取 .DTA", parent=self)
            return
        self._load_df(_shared.df.copy(), _shared.source)

    def _load_df(self, df, src):
        self._df = df
        self._orig = df.copy()
        self.lbl_src.setText(src)
        self._activated = True
        self._update_channels()
        self._set_trange()
        self.btn_apply.setEnabled(True)
        _fill_table(self.table, df)
        self.lbl_info.setText(f"原始: {len(df)} hits")

    def _update_channels(self):
        self.ch_list.clear()
        c = _col(self._df, "通道")
        if c:
            for ch in sorted(self._df[c].unique()):
                item = QListWidgetItem(str(ch))
                item.setSelected(True)
                self.ch_list.addItem(item)

    def _set_trange(self):
        c = _col(self._df, "相对时间")
        if c:
            lo, hi = float(self._df[c].min()), float(self._df[c].max())
            self.spin_tmin.setValue(lo)
            self.spin_tmax.setValue(hi)
            self.spin_tmin.setRange(lo, hi)
            self.spin_tmax.setRange(lo, hi)

    def _apply(self):
        if self._df is None:
            return
        df = self._orig.copy()
        before = len(df)
        a = _col(df, "振幅")
        if a:
            df = df[df[a] >= self.spin_amp.value()]
        t = _col(df, "相对时间")
        if t:
            df = df[(df[t] >= self.spin_tmin.value()) & (df[t] <= self.spin_tmax.value())]
        c = _col(df, "通道")
        sel = [int(self.ch_list.item(i).text()) for i in range(self.ch_list.count())
               if self.ch_list.item(i).isSelected()]
        if c and sel:
            df = df[df[c].isin(sel)]
        self._df = df
        _fill_table(self.table, df)
        self.lbl_info.setText(f"原始 {before} | 滤波后 {len(df)} (移除 {before - len(df)})")
        self.btn_exp.setEnabled(True)
        self.btn_reset.setEnabled(True)

    def _reset(self):
        if self._orig is not None:
            self._df = self._orig.copy()
            _fill_table(self.table, self._df)
            self.lbl_info.setText(f"已重置, 原始 {len(self._df)} hits")
            self.btn_exp.setEnabled(False)
            self.btn_reset.setEnabled(False)

    def _export(self):
        if self._df is None:
            return
        fp, _ = QFileDialog.getSaveFileName(self, "导出 CSV", "filtered.csv", "CSV (*.csv)")
        if fp:
            self._df.to_csv(fp, index=False, encoding="utf-8-sig")
            InfoBar.success("导出成功", f"{len(self._df)} 条记录", parent=self)


# ══════════════════════════════════════════════════
#  模块3: 绘图
# ══════════════════════════════════════════════════

class _PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=11, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)


class PlotPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("plot_page")
        self._df = None
        self._activated = False
        self._build_ui()

    def _build_ui(self):
        lo = QVBoxLayout(self)
        lo.setSpacing(12)
        lo.addWidget(TitleLabel("绘图"))
        lo.addWidget(BodyLabel("振铃计数、振幅分布、3D 空间分布。"))

        r1 = QHBoxLayout()
        self.btn_load = PushButton(FluentIcon.DOCUMENT, "加载 CSV")
        self.btn_load.clicked.connect(self._load)
        r1.addWidget(self.btn_load)
        self.btn_use = PushButton(FluentIcon.SHARE, "使用主窗口数据")
        self.btn_use.clicked.connect(self._use_shared)
        r1.addWidget(self.btn_use)
        r1.addWidget(BodyLabel("图表:"))
        self.cmb = ComboBox()
        self.cmb.addItems(["振铃计数 + 累计 (双轴)", "振幅分布直方图", "3D 空间分布"])
        r1.addWidget(self.cmb)
        self.btn_plot = PrimaryPushButton(FluentIcon.EDIT, "绘图")
        self.btn_plot.setEnabled(False)
        self.btn_plot.clicked.connect(self._plot)
        r1.addWidget(self.btn_plot)
        self.btn_save = PushButton(FluentIcon.SAVE, "保存")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self._save)
        r1.addWidget(self.btn_save)
        r1.addStretch()
        lo.addLayout(r1)

        self.canvas = _PlotCanvas(self)
        self.tb = NavigationToolbar(self.canvas, self)
        lo.addWidget(self.tb)
        lo.addWidget(self.canvas, 1)

    def activate(self):
        if _shared.df is not None:
            self._df = _shared.df.copy()
            self.btn_plot.setEnabled(True)

    def _load(self):
        fp, _ = QFileDialog.getOpenFileName(self, "加载 CSV", "", "CSV (*.csv)")
        if not fp:
            return
        try:
            self._df = pd.read_csv(fp, encoding="utf-8-sig")
            self.btn_plot.setEnabled(True)
            self.btn_save.setEnabled(False)
            self._activated = True
            self.canvas.fig.clear()
            self.canvas.draw()
        except Exception as e:
            InfoBar.error("加载失败", str(e), parent=self)

    def _use_shared(self):
        if _shared.df is None:
            InfoBar.warning("无数据", "请先在模块1中读取 .DTA", parent=self)
            return
        self._df = _shared.df.copy()
        self.btn_plot.setEnabled(True)
        self._activated = True

    def _plot(self):
        if self._df is None:
            return
        self.canvas.fig.clear()
        t = self.cmb.currentText()
        if "振铃" in t:
            self._ring()
        elif "振幅分布" in t:
            self._amp_hist()
        else:
            self._d3()
        self.canvas.draw()
        self.btn_save.setEnabled(True)

    def _ring(self):
        tc, pc = _col(self._df, "相对时间"), _col(self._df, "振铃计数")
        if not tc or not pc:
            self.canvas.fig.text(.5, .5, "缺少数据列", ha="center", va="center")
            return
        t = self._df[tc].values
        p = self._df[pc].values
        c = np.cumsum(p)
        a1 = self.canvas.fig.subplots()
        a2 = a1.twinx()
        bw = max(1.0, (t.max() - t.min()) / len(t) * 1.2)
        a1.bar(t, p, width=bw, color="#E15759", alpha=.85, edgecolor="white", lw=.2)
        a2.plot(t, c, color="#4C78A8", lw=2, marker="o", ms=2)
        a1.set_xlabel("时间 (秒)")
        a1.set_ylabel("振铃计数", color="#E15759")
        a2.set_ylabel("累计振铃计数", color="#4C78A8")
        a1.tick_params(axis="y", labelcolor="#E15759")
        a2.tick_params(axis="y", labelcolor="#4C78A8")
        a1.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        a2.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        a1.grid(axis="y", alpha=.3, ls="--")
        l1, lb1 = a1.get_legend_handles_labels()
        l2, lb2 = a2.get_legend_handles_labels()
        a1.legend(l1 + l2, lb1 + lb2, loc="upper left")
        self.canvas.fig.suptitle("AE 振铃计数与累计振铃计数", fontsize=13, fontweight="bold")
        self.canvas.fig.tight_layout()

    def _amp_hist(self):
        a = _col(self._df, "振幅")
        if not a:
            return
        ax = self.canvas.fig.subplots()
        amps = self._df[a].values
        bins = np.arange(amps.min() - .5, amps.max() + 1.5, 1)
        ax.hist(amps, bins=bins, color="#4C78A8", edgecolor="white", alpha=.85)
        ax.set_xlabel("振幅 (dB)")
        ax.set_ylabel("Hit 数量")
        ax.set_title("振幅分布")
        ax.grid(axis="y", alpha=.3, ls="--")
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        self.canvas.fig.tight_layout()

    def _d3(self):
        xc = _col(self._df, "X") or _col(self._df, "x")
        yc = _col(self._df, "Y") or _col(self._df, "y")
        zc = _col(self._df, "Z") or _col(self._df, "z")
        if not all([xc, yc, zc]):
            self.canvas.fig.text(.5, .5, "缺少 x, y, z 坐标列",
                                 ha="center", va="center", fontsize=12, color="gray")
            return
        ax = self.canvas.fig.add_subplot(111, projection="3d")
        x = self._df[xc].values
        y = self._df[yc].values
        z = self._df[zc].values
        pc = _col(self._df, "振铃计数")
        tc = _col(self._df, "相对时间")
        sz = 20 + self._df[pc].values / self._df[pc].max() * 180 if pc else np.full(len(x), 50)
        cm = self._df[tc].values if tc else np.zeros(len(x))
        sc = ax.scatter(x, y, z, s=sz, c=cm, cmap="viridis", alpha=.8,
                        edgecolors="white", lw=.3)
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")
        ax.set_zlabel("Z (mm)")
        ax.set_title("AE 事件 3D 空间分布")
        if tc:
            self.canvas.fig.colorbar(sc, ax=ax, shrink=.6, aspect=12).set_label("时间 (秒)")
        self.canvas.fig.tight_layout()

    def _save(self):
        fp, _ = QFileDialog.getSaveFileName(
            self, "保存图片", "ae_plot.png",
            "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)")
        if fp:
            self.canvas.fig.savefig(fp, dpi=200, bbox_inches="tight")
            InfoBar.success("保存成功", str(Path(fp).name), parent=self)


# ══════════════════════════════════════════════════
#  主窗口
# ══════════════════════════════════════════════════

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MISTRAS Standard Data Toolbox")
        self.resize(1280, 820)

        self.import_page = ImportPage(self)
        self.filter_page = FilterPage(self)
        self.plot_page = PlotPage(self)

        self.addSubInterface(self.import_page, FluentIcon.DOWNLOAD,
                             "DTA 导入导出", NavigationItemPosition.TOP)
        self.addSubInterface(self.filter_page, FluentIcon.FILTER,
                             "数据滤波", NavigationItemPosition.TOP)
        self.addSubInterface(self.plot_page, FluentIcon.EDIT,
                             "绘图", NavigationItemPosition.TOP)

        self.stackedWidget.currentChanged.connect(self._on_page_changed)

    def _on_page_changed(self, index):
        w = self.stackedWidget.widget(index)
        if w == self.filter_page:
            self.filter_page.activate()
        elif w == self.plot_page:
            self.plot_page.activate()

    # 启动后自动尝试加载共享数据
    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(200, self._deferred)

    def _deferred(self):
        self.filter_page.activate()
        self.plot_page.activate()
        self.switchTo(self.import_page)
