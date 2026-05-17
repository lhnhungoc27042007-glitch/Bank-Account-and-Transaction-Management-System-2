"""
page_statistics.py — Trang Thống kê

Biểu đồ:
  - Bar chart ngang: Thu nhập theo danh mục (tất cả thời gian)
  - Bar chart ngang: Chi tiêu theo danh mục (tất cả thời gian)
  - Bar chart nhóm: So sánh thu/chi theo 8 tháng gần nhất
"""

import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config import C
from widgets import card, label


class StatisticsPage(ctk.CTkFrame):

    def __init__(self, parent, db):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self._build()

    # ── Dựng layout lưới 2 cột ────────────────────────────
    def _build(self):
        self.columnconfigure((0, 1), weight=1)
        self.rowconfigure((0, 1), weight=1)

        self.f1 = card(self); self.f1.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")
        self.f2 = card(self); self.f2.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")
        self.f3 = card(self); self.f3.grid(row=1, column=0, columnspan=2, padx=6, pady=6, sticky="nsew")

    # ── Refresh: xóa cũ và vẽ lại ────────────────────────
    def refresh(self):
        for f in [self.f1, self.f2, self.f3]:
            for w in f.winfo_children():
                w.destroy()
        self._draw_income_by_category()
        self._draw_expense_by_category()
        self._draw_monthly_comparison()

    # ── Bar chart: thu nhập theo danh mục ────────────────
    def _draw_income_by_category(self):
        label(self.f1, "💹 Thu nhập theo danh mục", 13, "bold").pack(anchor="w", padx=12, pady=(10, 0))
        rows = self.db.by_category("income")
        if not rows:
            label(self.f1, "Chưa có dữ liệu", 11, color=C["muted"]).pack(expand=True)
            return
        self._draw_hbar(self.f1,
                        cats=[r["category"] for r in rows],
                        vals=[r["total"]    for r in rows],
                        color=C["income"])

    # ── Bar chart: chi tiêu theo danh mục ────────────────
    def _draw_expense_by_category(self):
        label(self.f2, "💸 Chi tiêu theo danh mục", 13, "bold").pack(anchor="w", padx=12, pady=(10, 0))
        rows = self.db.by_category("expense")
        if not rows:
            label(self.f2, "Chưa có dữ liệu", 11, color=C["muted"]).pack(expand=True)
            return
        self._draw_hbar(self.f2,
                        cats=[r["category"] for r in rows],
                        vals=[r["total"]    for r in rows],
                        color=C["expense"])

    # ── Hàm vẽ bar chart ngang (dùng chung) ──────────────
    def _draw_hbar(self, parent, cats, vals, color):
        fig = Figure(figsize=(3.8, 2.6), dpi=96)
        fig.patch.set_facecolor(C["card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(C["card"])

        y    = range(len(cats))
        bars = ax.barh(list(y), vals, color=color, alpha=0.85, height=0.55)

        ax.set_yticks(list(y))
        ax.set_yticklabels(cats, color=C["text"], fontsize=9)
        ax.tick_params(colors=C["muted"], labelsize=8)
        ax.xaxis.set_tick_params(labelcolor=C["muted"])
        for spine in ax.spines.values():
            spine.set_edgecolor(C["border"])

        # Hiện số tiền bên phải mỗi bar
        for bar, val in zip(bars, vals):
            ax.text(bar.get_width() * 1.01,
                    bar.get_y() + bar.get_height() / 2,
                    f"₫{val:,.0f}",
                    va="center", fontsize=7, color=C["muted"])

        fig.tight_layout(pad=1)

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)

    # ── Bar chart nhóm: so sánh theo tháng ───────────────
    def _draw_monthly_comparison(self):
        label(self.f3, "📊 So sánh thu chi theo tháng", 13, "bold").pack(anchor="w", padx=12, pady=(10, 0))
        rows = self.db.monthly_trend(8)

        if not rows:
            label(self.f3, "Chưa có dữ liệu", 11, color=C["muted"]).pack(expand=True)
            return

        months   = [r["m"]       for r in rows]
        incomes  = [r["income"]  for r in rows]
        expenses = [r["expense"] for r in rows]

        x = range(len(months))
        w = 0.38   # Độ rộng mỗi cột trong nhóm

        fig = Figure(figsize=(7, 2.6), dpi=96)
        fig.patch.set_facecolor(C["card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(C["card"])

        # Thu nhập (lệch trái) và chi tiêu (lệch phải)
        ax.bar([i - w / 2 for i in x], incomes,  width=w, color=C["income"],  alpha=0.85, label="Thu nhập")
        ax.bar([i + w / 2 for i in x], expenses, width=w, color=C["expense"], alpha=0.85, label="Chi tiêu")

        ax.set_xticks(list(x))
        ax.set_xticklabels(months, fontsize=8, color=C["muted"])
        ax.tick_params(colors=C["muted"], labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor(C["border"])
        ax.legend(fontsize=8, facecolor=C["panel"], labelcolor=C["text"], edgecolor=C["border"])
        fig.tight_layout(pad=1)

        canvas = FigureCanvasTkAgg(fig, master=self.f3)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=(0, 8))