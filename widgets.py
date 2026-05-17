"""
widgets.py — Các widget (thành phần UI) dùng chung trong toàn bộ ứng dụng

Gồm:
  - card()      : khung chứa có bo góc
  - label()     : nhãn chữ
  - btn()       : nút bấm
  - entry()     : ô nhập liệu
  - StatCard    : thẻ hiển thị số liệu tổng quan (thu nhập, chi tiêu, số dư)
"""

import customtkinter as ctk
from config import C


# ── Hàm tạo nhanh widget cơ bản ───────────────────────────

def card(parent, **kw):
    """Tạo CTkFrame trông như một thẻ card có bo góc."""
    kw.setdefault("fg_color",     C["card"])
    kw.setdefault("corner_radius", 14)
    return ctk.CTkFrame(parent, **kw)


def label(parent, text, size=13, weight="normal", color=None, **kw):
    """Tạo CTkLabel với font Segoe UI."""
    return ctk.CTkLabel(
        parent, text=text,
        font=ctk.CTkFont(family="Segoe UI", size=size, weight=weight),
        text_color=color or C["text"],
        **kw
    )


def btn(parent, text, cmd, fg=None, hover=None, width=120, **kw):
    """Tạo CTkButton với style nhất quán."""
    return ctk.CTkButton(
        parent, text=text, command=cmd,
        width=width, height=36,
        fg_color=fg or C["accent"],
        hover_color=hover or "#8B85FF",
        font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        corner_radius=8,
        **kw
    )


def entry(parent, placeholder="", width=200, **kw):
    """Tạo CTkEntry với style nhất quán."""
    return ctk.CTkEntry(
        parent,
        placeholder_text=placeholder,
        width=width, height=38,
        corner_radius=8,
        fg_color=C["entry_bg"],
        border_color=C["border"],
        font=ctk.CTkFont("Segoe UI", 13),
        **kw
    )


# ── Widget phức tạp hơn ────────────────────────────────────

class StatCard(ctk.CTkFrame):
    """
    Thẻ hiển thị 1 chỉ số (thu nhập / chi tiêu / số dư).
    Có thanh màu bên trái, icon, tiêu đề và giá trị.
    """

    def __init__(self, parent, title, value, icon, accent, **kw):
        super().__init__(parent, fg_color=C["card"], corner_radius=14, **kw)
        self.configure(border_width=1, border_color=C["border"])

        # Thanh màu dọc bên trái
        bar = ctk.CTkFrame(self, fg_color=accent, width=4, corner_radius=4)
        bar.pack(side="left", fill="y", padx=(10, 0), pady=10)

        # Nội dung bên trong
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(side="left", padx=14, pady=12, fill="both", expand=True)

        ctk.CTkLabel(inner, text=icon,
                     font=ctk.CTkFont(size=26)).pack(anchor="w")
        ctk.CTkLabel(inner, text=title,
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=C["muted"]).pack(anchor="w")

        # Label giá trị — lưu lại để cập nhật sau 
        self.val_lbl = ctk.CTkLabel(
            inner, text=value,
            font=ctk.CTkFont("Segoe UI", 20, "bold"),
            text_color=accent
        )
        self.val_lbl.pack(anchor="w")

    def update(self, value: str):
        """Cập nhật giá trị hiển thị."""
        self.val_lbl.configure(text=value)