"""
page_transactions.py — Trang Giao dịch

Chức năng:
  - Hiển thị toàn bộ danh sách giao dịch (Read)
  - Tìm kiếm real-time theo tên/ghi chú
  - Lọc theo loại: Tất cả / Thu nhập / Chi tiêu
  - Thêm giao dịch mới (Create)
  - Chỉnh sửa giao dịch đã chọn (Update)
  - Xóa giao dịch đã chọn (Delete)
"""

import customtkinter as ctk
from config import C
from widgets import btn
from dialogs import TransactionDialog


class TransactionsPage(ctk.CTkFrame):

    def __init__(self, parent, db):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.selected_id  = None   # ID dòng đang được chọn
        self._selected_row = None  # Dữ liệu dòng đang được chọn
        self._build()

    # ── Dựng giao diện ────────────────────────────────────
    def _build(self):
        self._build_toolbar()
        self._build_table_header()
        self._build_scroll_area()

    def _build_toolbar(self):
        """Thanh công cụ: tìm kiếm + filter + nút CRUD."""
        tb = ctk.CTkFrame(self, fg_color="transparent")
        tb.pack(fill="x", pady=(0, 8))

        # Ô tìm kiếm — trace tự động gọi refresh() khi gõ
        self.search_var = ctk.StringVar()
        ctk.CTkEntry(
            tb, textvariable=self.search_var,
            placeholder_text="🔍 Tìm kiếm...",
            width=220, height=36, corner_radius=8,
            fg_color=C["card"], border_color=C["border"],
            font=ctk.CTkFont("Segoe UI", 13)
        ).pack(side="left", padx=(0, 8))
        self.search_var.trace_add("write", lambda *_: self.refresh())

        # Radio filter theo loại
        self.type_var = ctk.StringVar(value="all")
        for val, txt in [("all", "Tất cả"), ("income", "Thu nhập"), ("expense", "Chi tiêu")]:
            ctk.CTkRadioButton(
                tb, text=txt, variable=self.type_var, value=val,
                font=ctk.CTkFont("Segoe UI", 12),
                command=self.refresh
            ).pack(side="left", padx=6)

        # Nút CRUD bên phải
        btn(tb, "➕ Thêm",  self._add,    width=110).pack(side="right", padx=4)
        btn(tb, "✏️ Sửa",   self._edit,   fg=C["yellow"],  hover="#FFE066", width=100).pack(side="right", padx=4)
        btn(tb, "🗑 Xóa",   self._delete, fg=C["expense"], hover="#FF8FA0", width=100).pack(side="right", padx=4)

    def _build_table_header(self):
        """Dòng tiêu đề cột của bảng."""
        cols   = ["ID", "Ngày", "Loại", "Danh mục", "Số tiền", "Ghi chú"]
        widths = [40, 100, 80, 130, 130, 240]

        hf = ctk.CTkFrame(self, fg_color=C["border"], corner_radius=8)
        hf.pack(fill="x")
        for h, w in zip(cols, widths):
            ctk.CTkLabel(
                hf, text=h, width=w,
                font=ctk.CTkFont("Segoe UI", 11, "bold"),
                text_color=C["muted"]
            ).pack(side="left", padx=4, pady=6)

    def _build_scroll_area(self):
        """Vùng cuộn chứa các dòng dữ liệu."""
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.scroll.pack(fill="both", expand=True, pady=4)

    # ── Refresh: vẽ lại danh sách ────────────────────────
    def refresh(self):
        # Xóa tất cả dòng cũ
        for w in self.scroll.winfo_children():
            w.destroy()
        self.selected_id = None

        rows   = self.db.get_transactions(
            search=self.search_var.get(),
            type_filter=self.type_var.get()
        )
        widths = [40, 100, 80, 130, 130, 240]

        for row in rows:
            rf = ctk.CTkFrame(self.scroll, fg_color=C["card"], corner_radius=6)
            rf.pack(fill="x", pady=2)
            # Click vào dòng để chọn
            rf.bind("<Button-1>", lambda e, r=row, f=rf: self._select(r, f))

            color = C["income"] if row["type"] == "income" else C["expense"]
            vals  = [str(row["id"]), row["date"], row["type"].upper(),
                     row["category"], f"₫{row['amount']:,.0f}", row["note"] or "—"]

            for i, (v, w) in enumerate(zip(vals, widths)):
                if i == 2:
                    tc = color                    # Cột "Loại" hiển thị màu loại
                elif i == 4:
                    tc = C["income"] if row["type"] == "income" else C["expense"]
                else:
                    tc = C["text"]

                lbl = ctk.CTkLabel(rf, text=v, width=w,
                                   font=ctk.CTkFont("Segoe UI", 12),
                                   text_color=tc, anchor="w")
                lbl.pack(side="left", padx=6, pady=6)
                lbl.bind("<Button-1>", lambda e, r=row, f=rf: self._select(r, f))

    # ── Chọn dòng (highlight) ─────────────────────────────
    def _select(self, row, frame):
        # Bỏ highlight tất cả dòng
        for w in self.scroll.winfo_children():
            w.configure(fg_color=C["card"])
        # Highlight dòng được chọn
        frame.configure(fg_color=C["border"])
        self.selected_id   = row["id"]
        self._selected_row = row

    # ── CRUD handlers ─────────────────────────────────────
    def _add(self):
        TransactionDialog(self, self.db, self.refresh)

    def _edit(self):
        if not self.selected_id:
            return   # Chưa chọn dòng nào
        TransactionDialog(self, self.db, self.refresh, self._selected_row)

    def _delete(self):
        if not self.selected_id:
            return
        # Yêu cầu người dùng xác nhận bằng cách gõ 'xoa'
        dlg = ctk.CTkInputDialog(
            text=f"Nhập 'xoa' để xác nhận xóa ID {self.selected_id}:",
            title="Xác nhận xóa"
        )
        if dlg.get_input() == "xoa":
            self.db.delete_transaction(self.selected_id)
            self.refresh()