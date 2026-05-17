"""
dialogs.py — Hộp thoại (popup) thêm và chỉnh sửa giao dịch

Class:
  TransactionDialog : cửa sổ popup dùng cho cả thêm mới lẫn chỉnh sửa
"""

import customtkinter as ctk
from datetime import date
from config import C
from widgets import label, btn, entry


class TransactionDialog(ctk.CTkToplevel):
    """
    Popup nhập liệu giao dịch.
    - Nếu edit_row=None  → chế độ THÊM MỚI
    - Nếu edit_row=<row> → chế độ CHỈNH SỬA (điền sẵn dữ liệu)
    """

    # Danh mục mặc định theo loại giao dịch
    INCOME_CATS  = ["Lương", "Thưởng", "Đầu tư", "Kinh doanh", "Khác"]
    EXPENSE_CATS = ["Ăn uống", "Di chuyển", "Nhà ở", "Giải trí",
                    "Sức khỏe", "Mua sắm", "Giáo dục", "Tiện ích", "Khác"]

    def __init__(self, parent, db, on_save, edit_row=None):
        """
        parent   : cửa sổ cha
        db       : đối tượng Database
        on_save  : hàm callback gọi sau khi lưu thành công
        edit_row : sqlite3.Row cần chỉnh sửa (None nếu thêm mới)
        """
        super().__init__(parent)
        self.db       = db
        self.on_save  = on_save
        self.edit_row = edit_row

        self.title("✏️ Chỉnh sửa" if edit_row else "➕ Thêm giao dịch")
        self.geometry("420x500")
        self.configure(fg_color=C["bg"])
        self.resizable(False, False)
        self.grab_set()   # Khóa focus vào popup này

        self._build()

        # Nếu đang sửa thì điền dữ liệu cũ vào form
        if edit_row:
            self._fill(edit_row)

    # ── Dựng giao diện ────────────────────────────────────
    def _build(self):
        pad = {"padx": 24, "pady": 6}

        label(self, "💳  Giao dịch mới", 16, "bold").pack(**pad, pady=(20, 4))

        # --- Chọn loại: Thu nhập / Chi tiêu ---
        self.type_var = ctk.StringVar(value="expense")
        tf = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=10)
        tf.pack(fill="x", **pad)
        for t, color in [("income", "#2DD4BF"), ("expense", "#FF6584")]:
            lbl_text = "💹 Thu nhập" if t == "income" else "💸 Chi tiêu"
            ctk.CTkRadioButton(
                tf, text=lbl_text,
                variable=self.type_var, value=t,
                fg_color=color, hover_color=color,
                font=ctk.CTkFont("Segoe UI", 13),
                command=self._refresh_cats   # Cập nhật danh mục khi đổi loại
            ).pack(side="left", padx=16, pady=10)

        # --- Danh mục ---
        label(self, "Danh mục").pack(anchor="w", **pad)
        self.cat_var  = ctk.StringVar(value=self.EXPENSE_CATS[0])
        self.cat_menu = ctk.CTkOptionMenu(
            self, variable=self.cat_var,
            values=self.EXPENSE_CATS,
            fg_color=C["entry_bg"],
            button_color=C["accent"],
            font=ctk.CTkFont("Segoe UI", 13)
        )
        self.cat_menu.pack(fill="x", **pad)

        # --- Số tiền ---
        label(self, "Số tiền (VNĐ)").pack(anchor="w", **pad)
        self.amt_entry = entry(self, "0", width=370)
        self.amt_entry.pack(fill="x", **pad)

        # --- Ghi chú ---
        label(self, "Ghi chú").pack(anchor="w", **pad)
        self.note_entry = entry(self, "Không bắt buộc", width=370)
        self.note_entry.pack(fill="x", **pad)

        # --- Ngày ---
        label(self, "Ngày (YYYY-MM-DD)").pack(anchor="w", **pad)
        self.date_entry = entry(self, str(date.today()), width=370)
        self.date_entry.insert(0, str(date.today()))
        self.date_entry.pack(fill="x", **pad)

        # --- Nút Lưu / Hủy ---
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(pady=16)
        btn(bf, "💾 Lưu",  self._save,    width=150).pack(side="left", padx=8)
        btn(bf, "✕ Hủy",  self.destroy,
            fg=C["card"], hover="#2A2F42", width=100).pack(side="left")

    # ── Cập nhật danh sách danh mục khi đổi loại ─────────
    def _refresh_cats(self):
        cats = self.INCOME_CATS if self.type_var.get() == "income" else self.EXPENSE_CATS
        self.cat_menu.configure(values=cats)
        self.cat_var.set(cats[0])

    # ── Điền dữ liệu cũ vào form (chế độ sửa) ────────────
    def _fill(self, row):
        self.type_var.set(row["type"])
        self._refresh_cats()
        self.cat_var.set(row["category"])

        self.amt_entry.delete(0, "end")
        self.amt_entry.insert(0, str(row["amount"]))

        self.note_entry.delete(0, "end")
        self.note_entry.insert(0, row["note"] or "")

        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, row["date"])

    # ── Xử lý khi bấm Lưu ────────────────────────────────
    def _save(self):
        # Validate số tiền
        try:
            amt = float(self.amt_entry.get().replace(",", ""))
            assert amt > 0
        except (ValueError, AssertionError):
            return   # Không làm gì nếu nhập sai

        d    = self.date_entry.get().strip() or str(date.today())
        note = self.note_entry.get().strip()

        if self.edit_row:
            # Cập nhật giao dịch đã có
            self.db.update_transaction(
                self.edit_row["id"], self.type_var.get(),
                self.cat_var.get(), amt, note, d
            )
        else:
            # Thêm giao dịch mới
            self.db.add_transaction(
                self.type_var.get(), self.cat_var.get(), amt, note, d
            )

        self.on_save()   # Gọi callback để refresh trang
        self.destroy()   # Đóng popup