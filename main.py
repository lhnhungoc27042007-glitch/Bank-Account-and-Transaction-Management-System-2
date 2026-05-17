"""
main.py — Điểm khởi động ứng dụng FINOVA

Chịu trách nhiệm:
  - Khởi tạo cửa sổ chính (FinovaApp)
  - Dựng Sidebar điều hướng
  - Quản lý việc chuyển trang
"""

import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")   # Bắt buộc trước khi import matplotlib.pyplot

from datetime import datetime

from config import C
from database import Database
from widgets import btn
from dialogs import TransactionDialog
from page_dashboard    import DashboardPage
from page_transactions import TransactionsPage
from page_budget       import BudgetPage
from page_statistics   import StatisticsPage


class FinovaApp(ctk.CTk):
    """Cửa sổ chính của ứng dụng."""

    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("FINOVA — Quản lý Tài chính Cá nhân")
        self.geometry("1140x700")
        self.minsize(900, 600)
        self.configure(fg_color=C["bg"])

        self.db = Database()   # Kết nối SQLite
        self._build()
        self._show("dashboard")   # Mở trang mặc định

    # ══════════════════════════════════════════════════════
    #  Dựng giao diện chính
    # ══════════════════════════════════════════════════════
    def _build(self):
        self._build_sidebar()
        self._build_content_area()

    # ── Sidebar bên trái ──────────────────────────────────
    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, fg_color=C["panel"], width=210, corner_radius=0)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)   # Giữ cố định chiều rộng 210px

        # Logo + tên app
        lf = ctk.CTkFrame(sb, fg_color="transparent")
        lf.pack(fill="x", pady=(20, 4))
        ctk.CTkLabel(lf, text="💎", font=ctk.CTkFont(size=32)).pack()
        ctk.CTkLabel(lf, text="FINOVA",
                     font=ctk.CTkFont("Segoe UI", 22, "bold"),
                     text_color=C["accent"]).pack()
        ctk.CTkLabel(lf, text="Tài chính cá nhân",
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["muted"]).pack(pady=(0, 16))

        ctk.CTkFrame(sb, fg_color=C["border"], height=1).pack(fill="x", padx=12, pady=4)

        # Các nút điều hướng
        self._nav_btns = {}
        nav_items = [
            ("dashboard",    "🏠  Tổng quan"),
            ("transactions", "📋  Giao dịch"),
            ("budget",       "📦  Ngân sách"),
            ("statistics",   "📊  Thống kê"),
        ]
        for key, text in nav_items:
            b = ctk.CTkButton(
                sb, text=text, width=186, height=42,
                anchor="w",
                font=ctk.CTkFont("Segoe UI", 13),
                fg_color="transparent",
                hover_color=C["card"],
                text_color=C["text"],
                corner_radius=8,
                command=lambda k=key: self._show(k)
            )
            b.pack(padx=10, pady=3)
            self._nav_btns[key] = b

        ctk.CTkFrame(sb, fg_color=C["border"], height=1).pack(fill="x", padx=12, pady=12)

        # Nút thêm nhanh
        btn(sb, "➕ Thêm giao dịch",
            lambda: TransactionDialog(self, self.db, self._refresh_current),
            width=186).pack(padx=10, pady=4)

        # Thông tin project ở cuối sidebar
        ctk.CTkLabel(
            sb, text="Python Programming\nCourse Final Project",
            font=ctk.CTkFont("Segoe UI", 9),
            text_color=C["muted"], justify="center"
        ).pack(side="bottom", pady=16)

    # ── Khu vực nội dung bên phải ─────────────────────────
    def _build_content_area(self):
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(side="left", fill="both", expand=True, padx=16, pady=12)

        # Header: tiêu đề trang + ngày hôm nay
        hf = ctk.CTkFrame(self.content, fg_color="transparent")
        hf.pack(fill="x", pady=(0, 12))
        self.page_title = ctk.CTkLabel(
            hf, text="Tổng quan",
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
            text_color=C["text"]
        )
        self.page_title.pack(side="left")
        ctk.CTkLabel(
            hf, text=datetime.now().strftime("📅 %d/%m/%Y"),
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=C["muted"]
        ).pack(side="right", pady=4)

        # Khởi tạo tất cả các trang (ẩn cho đến khi được gọi)
        self.pages = {
            "dashboard":    DashboardPage(self.content, self.db),
            "transactions": TransactionsPage(self.content, self.db),
            "budget":       BudgetPage(self.content, self.db),
            "statistics":   StatisticsPage(self.content, self.db),
        }

    # ══════════════════════════════════════════════════════
    #  Điều hướng
    # ══════════════════════════════════════════════════════
    def _show(self, key: str):
        """Ẩn tất cả trang, hiện trang được chọn, refresh dữ liệu."""
        titles = {
            "dashboard":    "🏠  Tổng quan",
            "transactions": "📋  Giao dịch",
            "budget":       "📦  Ngân sách",
            "statistics":   "📊  Thống kê",
        }

        # Ẩn tất cả trang
        for p in self.pages.values():
            p.pack_forget()

        # Hiện trang được chọn
        self.pages[key].pack(fill="both", expand=True)
        self.page_title.configure(text=titles[key])

        # Cập nhật màu nút sidebar (active = tím, còn lại = trong suốt)
        for k, b in self._nav_btns.items():
            b.configure(fg_color=C["accent"] if k == key else "transparent")

        # Refresh dữ liệu trang
        self.pages[key].refresh()

    def _refresh_current(self):
        """Refresh trang đang hiện — dùng cho nút 'Thêm nhanh' ở sidebar."""
        current = next(
            k for k, p in self.pages.items()
            if p.winfo_manager() == "pack"
        )
        self.pages[current].refresh()


# ── Chạy ứng dụng ─────────────────────────────────────────
if __name__ == "__main__":
    app = FinovaApp()
    app.mainloop()