"""
page_dashboard.py — Trang Tổng quan (Dashboard)

Hiển thị:
  - 3 StatCard: Thu nhập / Chi tiêu / Số dư tháng này
  - Line chart xu hướng 6 tháng
  - Pie chart chi tiêu theo danh mục
  - Bảng 5 giao dịch gần nhất
"""

import customtkinter as ctk
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

from config import C
from widgets import card, label, StatCard


class DashboardPage(ctk.CTkFrame):

    def __init__(self, parent, db):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self._build()

    # ── Dựng layout ───────────────────────────────────────
    def _build(self):
        self.columnconfigure((0, 1, 2), weight=1, uniform="col")

        # Hàng 0: 3 stat cards
        self.card_in  = StatCard(self, "Thu nhập", "₫0", "💹", C["income"],  width=220)
        self.card_out = StatCard(self, "Chi tiêu",  "₫0", "💸", C["expense"], width=220)
        self.card_bal = StatCard(self, "Số dư",     "₫0", "💰", C["yellow"],  width=220)
        self.card_in .grid(row=0, column=0, padx=8, pady=8, sticky="ew")
        self.card_out.grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        self.card_bal.grid(row=0, column=2, padx=8, pady=8, sticky="ew")

        # Hàng 1: biểu đồ đường (trái) + biểu đồ tròn (phải)
        left  = card(self)
        right = card(self)
        left .grid(row=1, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")
        right.grid(row=1, column=2,               padx=8, pady=8, sticky="nsew")
        self.rowconfigure(1, weight=1)

        label(left,  "📈 Xu hướng 6 tháng",         13, "bold").pack(anchor="w", padx=14, pady=(12, 0))
        label(right, "🥧 Chi tiêu theo danh mục",    13, "bold").pack(anchor="w", padx=14, pady=(12, 0))

        self.trend_frame = ctk.CTkFrame(left,  fg_color="transparent")
        self.trend_frame.pack(fill="both", expand=True, padx=4, pady=4)

        self.pie_frame = ctk.CTkFrame(right, fg_color="transparent")
        self.pie_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # Hàng 2: giao dịch gần đây
        rec = card(self)
        rec.grid(row=2, column=0, columnspan=3, padx=8, pady=8, sticky="ew")
        label(rec, "🕐 Giao dịch gần đây", 13, "bold").pack(anchor="w", padx=14, pady=(12, 4))
        self.recent_frame = ctk.CTkFrame(rec, fg_color="transparent")
        self.recent_frame.pack(fill="x", padx=8, pady=(0, 12))

    # ── Refresh tất cả dữ liệu ────────────────────────────
    def refresh(self):
        month = datetime.now().strftime("%Y-%m")
        inc, exp = self.db.summary(month)
        bal = inc - exp

        self.card_in .update(f"₫{inc:,.0f}")
        self.card_out.update(f"₫{exp:,.0f}")
        self.card_bal.update(f"₫{bal:,.0f}")

        self._draw_trend()
        self._draw_pie()
        self._draw_recent()

    # ── Biểu đồ đường xu hướng ────────────────────────────
    def _draw_trend(self):
        for w in self.trend_frame.winfo_children():
            w.destroy()

        rows = self.db.monthly_trend(6)
        if not rows:
            return

        months   = [r["m"]       for r in rows]
        incomes  = [r["income"]  for r in rows]
        expenses = [r["expense"] for r in rows]

        fig = Figure(figsize=(5, 2.6), dpi=96)
        fig.patch.set_facecolor(C["card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(C["card"])

        x = range(len(months))
        ax.plot(x, incomes,  color=C["income"],  lw=2.5, marker="o", ms=5, label="Thu nhập")
        ax.plot(x, expenses, color=C["expense"], lw=2.5, marker="o", ms=5, label="Chi tiêu")
        ax.fill_between(x, incomes,  alpha=0.12, color=C["income"])
        ax.fill_between(x, expenses, alpha=0.12, color=C["expense"])

        ax.set_xticks(list(x))
        ax.set_xticklabels(months, fontsize=8, color=C["muted"])
        ax.tick_params(colors=C["muted"], labelsize=8)
        ax.yaxis.set_tick_params(labelcolor=C["muted"])
        for spine in ax.spines.values():
            spine.set_edgecolor(C["border"])
        ax.legend(fontsize=8, facecolor=C["panel"], labelcolor=C["text"], edgecolor=C["border"])
        fig.tight_layout(pad=1)

        canvas = FigureCanvasTkAgg(fig, master=self.trend_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ── Biểu đồ tròn chi tiêu theo danh mục ──────────────
    def _draw_pie(self):
        for w in self.pie_frame.winfo_children():
            w.destroy()

        month = datetime.now().strftime("%Y-%m")
        rows  = self.db.by_category("expense", month)

        if not rows:
            label(self.pie_frame, "Chưa có dữ liệu", 12, color=C["muted"]).pack(expand=True)
            return

        cats    = [r["category"] for r in rows]
        vals    = [r["total"]    for r in rows]
        palette = ["#6C63FF", "#FF6584", "#2DD4BF", "#FFD166",
                   "#F472B6", "#34D399", "#FB923C", "#60A5FA"]

        fig = Figure(figsize=(2.8, 2.8), dpi=96)
        fig.patch.set_facecolor(C["card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(C["card"])

        ax.pie(vals,
               colors=palette[:len(cats)],
               wedgeprops=dict(width=0.55, edgecolor=C["card"], linewidth=2),
               startangle=90)

        patches = [
            mpatches.Patch(color=palette[i % len(palette)], label=cats[i])
            for i in range(len(cats))
        ]
        ax.legend(handles=patches, fontsize=7,
                  facecolor=C["panel"], labelcolor=C["text"], edgecolor=C["border"],
                  loc="lower center", bbox_to_anchor=(0.5, -0.25), ncol=2)
        fig.tight_layout(pad=0.5)

        canvas = FigureCanvasTkAgg(fig, master=self.pie_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ── Bảng 5 giao dịch gần nhất ────────────────────────
    def _draw_recent(self):
        for w in self.recent_frame.winfo_children():
            w.destroy()

        rows    = self.db.get_transactions()[:5]
        headers = ["Ngày", "Loại", "Danh mục", "Số tiền", "Ghi chú"]
        widths  = [100, 80, 120, 130, 200]

        # Header row
        hf = ctk.CTkFrame(self.recent_frame, fg_color=C["border"], corner_radius=6)
        hf.pack(fill="x")
        for h, w in zip(headers, widths):
            ctk.CTkLabel(hf, text=h, width=w,
                         font=ctk.CTkFont("Segoe UI", 11, "bold"),
                         text_color=C["muted"]).pack(side="left", padx=4, pady=4)

        # Data rows
        for row in rows:
            color = C["income"] if row["type"] == "income" else C["expense"]
            vals  = [row["date"], row["type"].upper(), row["category"],
                     f"₫{row['amount']:,.0f}", row["note"] or "—"]

            rf = ctk.CTkFrame(self.recent_frame, fg_color="transparent")
            rf.pack(fill="x")
            for i, (v, w) in enumerate(zip(vals, widths)):
                if i == 1:
                    tc = color
                elif i == 3:
                    tc = C["income"] if row["type"] == "income" else C["expense"]
                else:
                    tc = C["text"]
                ctk.CTkLabel(rf, text=v, width=w,
                             font=ctk.CTkFont("Segoe UI", 11),
                             text_color=tc).pack(side="left", padx=4, pady=3)