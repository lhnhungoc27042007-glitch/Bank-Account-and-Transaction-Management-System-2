"""
config.py — Cấu hình màu sắc và đường dẫn toàn cục
"""

import os

# ── Đường dẫn database ─────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "finova.db")

# ── Bảng màu (Color Palette) ───────────────────────────────
C = {
    "bg":        "#0D0F14",   # Nền chính
    "panel":     "#141720",   # Sidebar
    "card":      "#1C2030",   # Thẻ card
    "border":    "#252A3A",   # Viền
    "accent":    "#6C63FF",   # Màu nhấn tím
    "accent2":   "#FF6584",   # Màu nhấn hồng
    "green":     "#2DD4BF",   # Xanh lá
    "yellow":    "#FFD166",   # Vàng
    "text":      "#E8EAF0",   # Chữ chính
    "muted":     "#6B7280",   # Chữ mờ
    "income":    "#2DD4BF",   # Màu thu nhập
    "expense":   "#FF6584",   # Màu chi tiêu
    "entry_bg":  "#1C2030",   # Nền ô nhập liệu
}