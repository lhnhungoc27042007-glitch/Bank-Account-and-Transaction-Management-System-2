"""
page_budget.py — Trang Ngân sách

Chức năng:
  - Đặt hạn mức chi tiêu hàng tháng cho từng danh mục
  - Hiển thị progress bar cho từng danh mục
  - Đổi màu cảnh báo khi gần / vượt hạn mức
  - Xóa ngân sách
"""

import customtkinter as ctk
from datetime import datetime

from config import C
from widgets import card, label, btn, entry


class BudgetPage(ctk.CTkFrame):

    def __init__(self, parent, db):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self._build()

    # ── Dựng giao diện ────────────────────────────────────
    def _build(self):
        # Thanh nhập ngân sách mới
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 12))

        label(top, "📦 Danh mục", 12, color=C["muted"]).pack(side="left")
        self.cat_entry = entry(top, "Tên danh mục...", width=180)
        self.cat_entry.pack(side="left", padx=(4, 8))

        label(top, "Hạn mức (₫)", 12, color=C["muted"]).pack(side="left")
        self.lim_entry = entry(top, "500000", width=140)
        self.lim_entry.pack(side="left", padx=(4, 8))

        btn(top, "💾 Đặt ngân sách", self._save, width=160).pack(side="left", padx=4)

        # Vùng cuộn hiển thị các card ngân sách
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

    # ── Lưu ngân sách mới / cập nhật ─────────────────────
    def _save(self):
        cat = self.cat_entry.get().strip()
        try:
            lim = float(self.lim_entry.get().replace(",", ""))
        except ValueError:
            return

        if cat and lim > 0:
            self.db.set_budget(cat, lim)
            self.cat_entry.delete(0, "end")
            self.lim_entry.delete(0, "end")
            self.refresh()

    # ── Refresh: vẽ lại danh sách ngân sách ──────────────
    def refresh(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        month   = datetime.now().strftime("%Y-%m")
        budgets = self.db.get_budgets()

        for b in budgets:
            # Tính số đã chi trong tháng cho danh mục này
            rows  = self.db.by_category("expense", month)
            spent = next((r["total"] for r in rows if r["category"] == b["category"]), 0)
            pct   = min(spent / b["monthly_limit"], 1.0)   # Tỉ lệ 0.0 → 1.0

            # Chọn màu theo mức độ (xanh → vàng → đỏ)
            if pct >= 0.9:
                color = C["expense"]   # Đỏ: sắp/đã vượt
            elif pct >= 0.7:
                color = C["yellow"]    # Vàng: cảnh báo
            else:
                color = C["income"]    # Xanh: an toàn

            self._render_budget_card(b, spent, pct, color)

    # ── Vẽ một card ngân sách ─────────────────────────────
    def _render_budget_card(self, b, spent, pct, color):
        f = card(self.scroll)
        f.pack(fill="x", pady=5, padx=4)

        # Dòng tiêu đề: tên danh mục + số tiền
        header = ctk.CTkFrame(f, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(12, 4))
        label(header, b["category"], 13, "bold").pack(side="left")
        label(header,
              f"₫{spent:,.0f} / ₫{b['monthly_limit']:,.0f}",
              12, color=color).pack(side="right")

        # Progress bar
        pb = ctk.CTkProgressBar(f, height=8, corner_radius=4,
                                fg_color=C["border"], progress_color=color)
        pb.pack(fill="x", padx=14, pady=(0, 6))
        pb.set(pct)

        # Phần trăm đã dùng
        ctk.CTkLabel(f, text=f"{pct * 100:.0f}% đã dùng",
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["muted"]).pack(anchor="e", padx=14, pady=(0, 8))

        # Nút xóa (góc trên phải)
        def _del(bid=b["id"]):
            self.db.delete_budget(bid)
            self.refresh()

        ctk.CTkButton(
            f, text="🗑", width=32, height=24,
            fg_color="transparent", hover_color=C["border"],
            command=_del
        ).place(relx=1, rely=0, anchor="ne", x=-8, y=8)