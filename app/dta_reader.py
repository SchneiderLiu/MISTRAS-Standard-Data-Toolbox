#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MistrasDTA 读取封装
====================
封装 MistrasDTA.read_bin()，提供统一的 .DTA 文件读取接口和 CSV 导出功能。
"""

from pathlib import Path
import numpy as np
import pandas as pd

from MistrasDTA import read_bin


# ── 中英对照表头 ─────────────────────────────────────────
RENAME_MAP = {
    "SSSSSSSS.mmmuuun": "相对时间(秒) Relative_Time_S",
    "CH":              "通道 CH",
    "RISE":            "上升时间(us) Rise_Time",
    "PCNTS":           "振铃计数 Ring_Counts",
    "COUN":            "持续计数 Duration_Counts",
    "ENER":            "能量 Energy",
    "DURATION":        "持续时间(us) Duration",
    "AMP":             "振幅(dB) Amplitude",
    "ASL":             "平均信号电平(dB) Avg_Signal_Level",
    "THR":             "阈值(dB) Threshold",
    "A-FRQ":           "平均频率(kHz) Avg_Frequency",
    "RMS":             "均方根电压(V) RMS",
    "R-FRQ":           "谐振频率(kHz) Resonant_Frequency",
    "I-FRQ":           "初始频率(kHz) Init_Frequency",
    "SIG STRENGTH":    "信号强度(pV-s) Signal_Strength",
    "ABS-ENERGY":      "绝对能量(aJ) Absolute_Energy",
    "FRQ-C":           "质心频率(kHz) Centroid_Frequency",
    "P-FRQ":           "峰值频率(kHz) Peak_Frequency",
    "TIMESTAMP":       "时间戳 Timestamp",
}


def read_dta(dta_path: str, skip_wfm: bool = True):
    """读取 .DTA 文件，返回 hit 数据的 pandas DataFrame 和波形信息。"""
    rec, wfm = read_bin(str(dta_path), skip_wfm=skip_wfm)

    df = None
    wfm_info = None

    if rec is not None and len(rec) > 0:
        df = pd.DataFrame(rec)
        df.rename(columns=RENAME_MAP, inplace=True)

    if wfm is not None and len(wfm) > 0:
        wfm_info = {
            "count": len(wfm),
            "channels": list(np.unique(wfm["CH"])),
        }

    return df, wfm_info


def export_csv(df: pd.DataFrame, output_path: str,
               amp_min: float = 0) -> None:
    """导出为 CSV，可选振幅下限过滤。"""
    if amp_min > 0:
        col_amp = [c for c in df.columns if "振幅" in c]
        if col_amp:
            before = len(df)
            df = df[df[col_amp[0]] >= amp_min].copy()
            after = len(df)
            print(f"  [滤波] 振幅 >= {amp_min} dB: {before} -> {after} hits "
                  f"(移除 {before - after})")

    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return len(df)


def get_amp_column(df: pd.DataFrame) -> str:
    """返回振幅列的名称。"""
    cols = [c for c in df.columns if "振幅" in c]
    return cols[0] if cols else None


def get_time_column(df: pd.DataFrame) -> str:
    """返回相对时间列的名称。"""
    cols = [c for c in df.columns if "相对时间" in c]
    return cols[0] if cols else None
