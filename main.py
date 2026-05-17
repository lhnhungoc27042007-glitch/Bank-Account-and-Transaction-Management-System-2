"""
╔══════════════════════════════════════════════════════════╗
║      FINOVA - Personal Finance Manager                   ║
║      Python Final Project | Course: Python Programming   ║
╚══════════════════════════════════════════════════════════╝
"""

import customtkinter as ctk
import sqlite3
import os
from datetime import datetime, date
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib
matplotlib.use("TkAgg")

# ── Paths ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "finova.db")

# ── Palette ────────────────────────────────────────────────
C = {
    "bg":        "#0D0F14",
    "panel":     "#141720",
    "card":      "#1C2030",
    "border":    "#252A3A",
    "accent":    "#6C63FF",
    "accent2":   "#FF6584",
    "green":     "#2DD4BF",
    "yellow":    "#FFD166",
    "text":      "#E8EAF0",
    "muted":     "#6B7280",
    "income":    "#2DD4BF",
    "expense":   "#FF6584",
    "entry_bg":  "#1C2030",
}

# ══════════════════════════════════════════════════════════
#  DATABASE LAYER
# ══════════════════════════════════════════════════════════
class Database:
    def __init__(self, path=DB_PATH):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self):
        c = self.conn.cursor()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            type        TEXT    NOT NULL CHECK(type IN ('income','expense')),
            category    TEXT    NOT NULL,
            amount      REAL    NOT NULL CHECK(amount > 0),
            note        TEXT,
            date        TEXT    NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS budgets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category    TEXT    UNIQUE NOT NULL,
            monthly_limit REAL  NOT NULL CHECK(monthly_limit > 0)
        );
        """)
        self.conn.commit()

    # ── Transactions ──────────────────────────────────────
    def add_transaction(self, type_, category, amount, note, date_):
        self.conn.execute(
            "INSERT INTO transactions (type,category,amount,note,date) VALUES(?,?,?,?,?)",
            (type_, category, amount, note, date_))
        self.conn.commit()

    def get_transactions(self, search="", type_filter="all", month=""):
        q = "SELECT * FROM transactions WHERE 1=1"
        params = []
        if search:
            q += " AND (category LIKE ? OR note LIKE ?)"
            params += [f"%{search}%", f"%{search}%"]
        if type_filter != "all":
            q += " AND type=?"
            params.append(type_filter)
        if month:
            q += " AND date LIKE ?"
            params.append(f"{month}%")
        q += " ORDER BY date DESC, id DESC"
        return self.conn.execute(q, params).fetchall()

    def update_transaction(self, id_, type_, category, amount, note, date_):
        self.conn.execute(
            "UPDATE transactions SET type=?,category=?,amount=?,note=?,date=? WHERE id=?",
            (type_, category, amount, note, date_, id_))
        self.conn.commit()

    def delete_transaction(self, id_):
        self.conn.execute("DELETE FROM transactions WHERE id=?", (id_,))
        self.conn.commit()

    # ── Summary helpers ────────────────────────────────────
    def summary(self, month=""):
        where = f"AND date LIKE '{month}%'" if month else ""
        row = self.conn.execute(f"""
            SELECT
              COALESCE(SUM(CASE WHEN type='income'  THEN amount ELSE 0 END),0) AS income,
              COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END),0) AS expense
            FROM transactions WHERE 1=1 {where}
        """).fetchone()
        return row["income"], row["expense"]

    def by_category(self, type_, month=""):
        where = f"AND date LIKE '{month}%'" if month else ""
        rows = self.conn.execute(f"""
            SELECT category, SUM(amount) as total
            FROM transactions WHERE type=? {where}
            GROUP BY category ORDER BY total DESC
        """, (type_,)).fetchall()
        return rows

    def monthly_trend(self, limit=6):
        rows = self.conn.execute("""
            SELECT strftime('%Y-%m', date) AS m,
                   SUM(CASE WHEN type='income'  THEN amount ELSE 0 END) AS income,
                   SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS expense
            FROM transactions
            GROUP BY m ORDER BY m DESC LIMIT ?
        """, (limit,)).fetchall()
        return list(reversed(rows))

    # ── Budgets ────────────────────────────────────────────
    def set_budget(self, category, limit_):
        self.conn.execute("""
            INSERT INTO budgets(category,monthly_limit) VALUES(?,?)
            ON CONFLICT(category) DO UPDATE SET monthly_limit=excluded.monthly_limit
        """, (category, limit_))
        self.conn.commit()

    def get_budgets(self):
        return self.conn.execute("SELECT * FROM budgets ORDER BY category").fetchall()

    def delete_budget(self, id_):
        self.conn.execute("DELETE FROM budgets WHERE id=?", (id_,))
        self.conn.commit()


# ══════════════════════════════════════════════════════════
#  REUSABLE WIDGETS
# ══════════════════════════════════════════════════════════
def card(parent, **kw):
    kw.setdefault("fg_color",    C["card"])
    kw.setdefault("corner_radius", 14)
    return ctk.CTkFrame(parent, **kw)

def label(parent, text, size=13, weight="normal", color=None, **kw):
    return ctk.CTkLabel(parent, text=text,
                        font=ctk.CTkFont(family="Segoe UI", size=size, weight=weight),
                        text_color=color or C["text"], **kw)

def btn(parent, text, cmd, fg=None, hover=None, width=120, **kw):
    return ctk.CTkButton(parent, text=text, command=cmd,
                         width=width, height=36,
                         fg_color=fg or C["accent"],
                         hover_color=hover or "#8B85FF",
                         font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                         corner_radius=8, **kw)

def entry(parent, placeholder="", width=200, **kw):
    return ctk.CTkEntry(parent, placeholder_text=placeholder, width=width,
                        height=38, corner_radius=8,
                        fg_color=C["entry_bg"], border_color=C["border"],
                        font=ctk.CTkFont("Segoe UI", 13), **kw)


# ══════════════════════════════════════════════════════════
#  STAT CARD
# ══════════════════════════════════════════════════════════
class StatCard(ctk.CTkFrame):
    def __init__(self, parent, title, value, icon, accent, **kw):
        super().__init__(parent, fg_color=C["card"], corner_radius=14, **kw)
        self.configure(border_width=1, border_color=C["border"])

        bar = ctk.CTkFrame(self, fg_color=accent, width=4, corner_radius=4)
        bar.pack(side="left", fill="y", padx=(10,0), pady=10)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(side="left", padx=14, pady=12, fill="both", expand=True)

        ctk.CTkLabel(inner, text=icon, font=ctk.CTkFont(size=26)).pack(anchor="w")
        ctk.CTkLabel(inner, text=title, font=ctk.CTkFont("Segoe UI",11),
                     text_color=C["muted"]).pack(anchor="w")
        self.val_lbl = ctk.CTkLabel(inner, text=value,
                                    font=ctk.CTkFont("Segoe UI",20,"bold"),
                                    text_color=accent)
        self.val_lbl.pack(anchor="w")

    def update(self, value):
        self.val_lbl.configure(text=value)


# ══════════════════════════════════════════════════════════
#  TRANSACTION DIALOG
# ══════════════════════════════════════════════════════════
class TransactionDialog(ctk.CTkToplevel):
    INCOME_CATS  = ["Lương","Thưởng","Đầu tư","Kinh doanh","Khác"]
    EXPENSE_CATS = ["Ăn uống","Di chuyển","Nhà ở","Giải trí","Sức khỏe",
                    "Mua sắm","Giáo dục","Tiện ích","Khác"]

    def __init__(self, parent, db, on_save, edit_row=None):
        super().__init__(parent)
        self.db = db
        self.on_save = on_save
        self.edit_row = edit_row
        self.title("Chỉnh sửa" if edit_row else "Thêm giao dịch")
        self.geometry("420x500")
        self.configure(fg_color=C["bg"])
        self.resizable(False, False)
        self.grab_set()
        self._build()
        if edit_row:
            self._fill(edit_row)

    def _build(self):
        pad = {"padx":24, "pady":6}

        label(self, "💳  Giao dịch mới", 16, "bold").pack(**pad, pady=(20,4))

        # Type toggle
        self.type_var = ctk.StringVar(value="expense")
        tf = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=10)
        tf.pack(fill="x", **pad)
        for t, color in [("income","#2DD4BF"),("expense","#FF6584")]:
            lbl = "💹 Thu nhập" if t=="income" else "💸 Chi tiêu"
            ctk.CTkRadioButton(tf, text=lbl, variable=self.type_var, value=t,
                               fg_color=color, hover_color=color,
                               font=ctk.CTkFont("Segoe UI",13),
                               command=self._refresh_cats).pack(side="left",padx=16,pady=10)

        label(self, "Danh mục").pack(anchor="w",**pad)
        self.cat_var = ctk.StringVar(value=self.EXPENSE_CATS[0])
        self.cat_menu = ctk.CTkOptionMenu(self, variable=self.cat_var,
                                          values=self.EXPENSE_CATS,
                                          fg_color=C["entry_bg"],
                                          button_color=C["accent"],
                                          font=ctk.CTkFont("Segoe UI",13))
        self.cat_menu.pack(fill="x",**pad)

        label(self, "Số tiền (VNĐ)").pack(anchor="w",**pad)
        self.amt_entry = entry(self, "0", width=370)
        self.amt_entry.pack(fill="x",**pad)

        label(self, "Ghi chú").pack(anchor="w",**pad)
        self.note_entry = entry(self, "Không bắt buộc", width=370)
        self.note_entry.pack(fill="x",**pad)

        label(self, "Ngày (YYYY-MM-DD)").pack(anchor="w",**pad)
        self.date_entry = entry(self, str(date.today()), width=370)
        self.date_entry.insert(0, str(date.today()))
        self.date_entry.pack(fill="x",**pad)

        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(pady=16)
        btn(bf, "💾 Lưu", self._save, width=150).pack(side="left",padx=8)
        btn(bf, "✕ Hủy", self.destroy, fg=C["card"], hover="#2A2F42", width=100).pack(side="left")

    def _refresh_cats(self):
        cats = self.INCOME_CATS if self.type_var.get()=="income" else self.EXPENSE_CATS
        self.cat_menu.configure(values=cats)
        self.cat_var.set(cats[0])

    def _fill(self, row):
        self.type_var.set(row["type"])
        self._refresh_cats()
        self.cat_var.set(row["category"])
        self.amt_entry.delete(0,"end"); self.amt_entry.insert(0, str(row["amount"]))
        self.note_entry.delete(0,"end"); self.note_entry.insert(0, row["note"] or "")
        self.date_entry.delete(0,"end"); self.date_entry.insert(0, row["date"])

    def _save(self):
        try:
            amt = float(self.amt_entry.get().replace(",",""))
            assert amt > 0
            d = self.date_entry.get().strip() or str(date.today())
        except:
            return
        note = self.note_entry.get().strip()
        if self.edit_row:
            self.db.update_transaction(self.edit_row["id"], self.type_var.get(),
                                       self.cat_var.get(), amt, note, d)
        else:
            self.db.add_transaction(self.type_var.get(), self.cat_var.get(), amt, note, d)
        self.on_save()
        self.destroy()


# ══════════════════════════════════════════════════════════
#  PAGES
# ══════════════════════════════════════════════════════════

class DashboardPage(ctk.CTkFrame):
    def __init__(self, parent, db):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self._build()

    def _build(self):
        self.columnconfigure((0,1,2), weight=1, uniform="col")

        # ── Stat Cards ─────────────────────────────────────
        self.card_in  = StatCard(self,"Thu nhập","₫0","💹",C["income"], width=220)
        self.card_out = StatCard(self,"Chi tiêu","₫0","💸",C["expense"], width=220)
        self.card_bal = StatCard(self,"Số dư","₫0","💰",C["yellow"], width=220)
        self.card_in .grid(row=0,column=0,padx=8,pady=8,sticky="ew")
        self.card_out.grid(row=0,column=1,padx=8,pady=8,sticky="ew")
        self.card_bal.grid(row=0,column=2,padx=8,pady=8,sticky="ew")

        # ── Charts row ─────────────────────────────────────
        left  = card(self)
        right = card(self)
        left .grid(row=1,column=0,columnspan=2,padx=8,pady=8,sticky="nsew")
        right.grid(row=1,column=2,padx=8,pady=8,sticky="nsew")
        self.rowconfigure(1, weight=1)

        label(left, "📈 Xu hướng 6 tháng", 13, "bold").pack(anchor="w",padx=14,pady=(12,0))
        self.trend_frame = ctk.CTkFrame(left, fg_color="transparent")
        self.trend_frame.pack(fill="both", expand=True, padx=4, pady=4)

        label(right,"🥧 Chi tiêu theo danh mục",13,"bold").pack(anchor="w",padx=14,pady=(12,0))
        self.pie_frame = ctk.CTkFrame(right, fg_color="transparent")
        self.pie_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # ── Recent ─────────────────────────────────────────
        rec = card(self)
        rec.grid(row=2,column=0,columnspan=3,padx=8,pady=8,sticky="ew")
        label(rec,"🕐 Giao dịch gần đây",13,"bold").pack(anchor="w",padx=14,pady=(12,4))
        self.recent_frame = ctk.CTkFrame(rec, fg_color="transparent")
        self.recent_frame.pack(fill="x", padx=8, pady=(0,12))

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

    def _draw_trend(self):
        for w in self.trend_frame.winfo_children(): w.destroy()
        rows = self.db.monthly_trend(6)
        if not rows: return
        months = [r["m"] for r in rows]
        incomes  = [r["income"]  for r in rows]
        expenses = [r["expense"] for r in rows]

        fig = Figure(figsize=(5,2.6), dpi=96)
        fig.patch.set_facecolor(C["card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(C["card"])
        x = range(len(months))
        ax.plot(x, incomes,  color=C["income"],  lw=2.5, marker="o", ms=5, label="Thu nhập")
        ax.plot(x, expenses, color=C["expense"], lw=2.5, marker="o", ms=5, label="Chi tiêu")
        ax.fill_between(x, incomes,  alpha=0.12, color=C["income"])
        ax.fill_between(x, expenses, alpha=0.12, color=C["expense"])
        ax.set_xticks(list(x)); ax.set_xticklabels(months, fontsize=8, color=C["muted"])
        ax.tick_params(colors=C["muted"], labelsize=8)
        for spine in ax.spines.values(): spine.set_edgecolor(C["border"])
        ax.yaxis.set_tick_params(labelcolor=C["muted"])
        ax.legend(fontsize=8, facecolor=C["panel"], labelcolor=C["text"], edgecolor=C["border"])
        fig.tight_layout(pad=1)

        canvas = FigureCanvasTkAgg(fig, master=self.trend_frame)
        canvas.draw(); canvas.get_tk_widget().pack(fill="both", expand=True)

    def _draw_pie(self):
        for w in self.pie_frame.winfo_children(): w.destroy()
        month = datetime.now().strftime("%Y-%m")
        rows = self.db.by_category("expense", month)
        if not rows:
            label(self.pie_frame,"Chưa có dữ liệu",12,color=C["muted"]).pack(expand=True)
            return
        cats = [r["category"] for r in rows]
        vals = [r["total"]    for r in rows]
        palette = ["#6C63FF","#FF6584","#2DD4BF","#FFD166","#F472B6","#34D399","#FB923C","#60A5FA"]

        fig = Figure(figsize=(2.8,2.8), dpi=96)
        fig.patch.set_facecolor(C["card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(C["card"])
        wedges, _ = ax.pie(vals, colors=palette[:len(cats)],
                           wedgeprops=dict(width=0.55, edgecolor=C["card"], linewidth=2),
                           startangle=90)
        patches = [mpatches.Patch(color=palette[i%len(palette)], label=cats[i]) for i in range(len(cats))]
        ax.legend(handles=patches, fontsize=7, facecolor=C["panel"],
                  labelcolor=C["text"], edgecolor=C["border"],
                  loc="lower center", bbox_to_anchor=(0.5,-0.25), ncol=2)
        fig.tight_layout(pad=0.5)
        canvas = FigureCanvasTkAgg(fig, master=self.pie_frame)
        canvas.draw(); canvas.get_tk_widget().pack(fill="both", expand=True)

    def _draw_recent(self):
        for w in self.recent_frame.winfo_children(): w.destroy()
        rows = self.db.get_transactions()[:5]
        headers = ["Ngày","Loại","Danh mục","Số tiền","Ghi chú"]
        widths  = [100,80,120,130,200]
        hf = ctk.CTkFrame(self.recent_frame, fg_color=C["border"], corner_radius=6)
        hf.pack(fill="x")
        for h,w in zip(headers,widths):
            ctk.CTkLabel(hf, text=h, width=w,
                         font=ctk.CTkFont("Segoe UI",11,"bold"),
                         text_color=C["muted"]).pack(side="left",padx=4,pady=4)
        for row in rows:
            rf = ctk.CTkFrame(self.recent_frame, fg_color="transparent")
            rf.pack(fill="x")
            color = C["income"] if row["type"]=="income" else C["expense"]
            vals = [row["date"], row["type"].upper(), row["category"],
                    f"₫{row['amount']:,.0f}", row["note"] or "—"]
            for i,(v,w) in enumerate(zip(vals,widths)):
                tc = color if i==1 else (C["income"] if i==3 and row["type"]=="income" else
                                         C["expense"] if i==3 else C["text"])
                ctk.CTkLabel(rf, text=v, width=w,
                             font=ctk.CTkFont("Segoe UI",11),
                             text_color=tc).pack(side="left",padx=4,pady=3)


class TransactionsPage(ctk.CTkFrame):
    def __init__(self, parent, db):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.selected_id = None
        self._build()

    def _build(self):
        # Toolbar
        tb = ctk.CTkFrame(self, fg_color="transparent")
        tb.pack(fill="x", pady=(0,8))

        self.search_var = ctk.StringVar()
        se = ctk.CTkEntry(tb, textvariable=self.search_var, placeholder_text="🔍 Tìm kiếm...",
                          width=220, height=36, corner_radius=8,
                          fg_color=C["card"], border_color=C["border"],
                          font=ctk.CTkFont("Segoe UI",13))
        se.pack(side="left", padx=(0,8))
        self.search_var.trace_add("write", lambda *_: self.refresh())

        self.type_var = ctk.StringVar(value="all")
        for val,txt in [("all","Tất cả"),("income","Thu nhập"),("expense","Chi tiêu")]:
            ctk.CTkRadioButton(tb, text=txt, variable=self.type_var, value=val,
                               font=ctk.CTkFont("Segoe UI",12),
                               command=self.refresh).pack(side="left",padx=6)

        btn(tb,"➕ Thêm",   self._add,   width=110).pack(side="right",padx=4)
        btn(tb,"✏️ Sửa",    self._edit,  fg=C["yellow"], hover="#FFE066", width=100).pack(side="right",padx=4)
        btn(tb,"🗑 Xóa",    self._delete,fg=C["expense"],hover="#FF8FA0",width=100).pack(side="right",padx=4)

        # Table header
        cols   = ["ID","Ngày","Loại","Danh mục","Số tiền","Ghi chú"]
        widths = [40,100,80,130,130,240]
        hf = ctk.CTkFrame(self, fg_color=C["border"], corner_radius=8)
        hf.pack(fill="x")
        for h,w in zip(cols,widths):
            ctk.CTkLabel(hf, text=h, width=w,
                         font=ctk.CTkFont("Segoe UI",11,"bold"),
                         text_color=C["muted"]).pack(side="left",padx=4,pady=6)

        # Scrollable rows
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.scroll.pack(fill="both", expand=True, pady=4)

    def refresh(self):
        for w in self.scroll.winfo_children(): w.destroy()
        self.selected_id = None
        rows = self.db.get_transactions(
            search=self.search_var.get(),
            type_filter=self.type_var.get())
        widths = [40,100,80,130,130,240]
        for row in rows:
            rf = ctk.CTkFrame(self.scroll, fg_color=C["card"], corner_radius=6)
            rf.pack(fill="x", pady=2)
            rf.bind("<Button-1>", lambda e,r=row,f=rf: self._select(r,f))
            color = C["income"] if row["type"]=="income" else C["expense"]
            vals = [str(row["id"]), row["date"], row["type"].upper(),
                    row["category"], f"₫{row['amount']:,.0f}", row["note"] or "—"]
            for i,(v,w) in enumerate(zip(vals,widths)):
                tc = color if i==2 else (C["income"] if i==4 and row["type"]=="income" else
                                         C["expense"] if i==4 else C["text"])
                lbl = ctk.CTkLabel(rf, text=v, width=w,
                                   font=ctk.CTkFont("Segoe UI",12),
                                   text_color=tc, anchor="w")
                lbl.pack(side="left",padx=6,pady=6)
                lbl.bind("<Button-1>", lambda e,r=row,f=rf: self._select(r,f))

    def _select(self, row, frame):
        for w in self.scroll.winfo_children():
            w.configure(fg_color=C["card"])
        frame.configure(fg_color=C["border"])
        self.selected_id = row["id"]
        self._selected_row = row

    def _add(self):
        TransactionDialog(self, self.db, self.refresh)

    def _edit(self):
        if not self.selected_id: return
        TransactionDialog(self, self.db, self.refresh, self._selected_row)

    def _delete(self):
        if not self.selected_id: return
        dlg = ctk.CTkInputDialog(text=f"Nhập 'xoa' để xác nhận xóa ID {self.selected_id}:",
                                  title="Xác nhận xóa")
        if dlg.get_input() == "xoa":
            self.db.delete_transaction(self.selected_id)
            self.refresh()


class BudgetPage(ctk.CTkFrame):
    def __init__(self, parent, db):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0,12))

        label(top,"📦 Danh mục",12,color=C["muted"]).pack(side="left")
        self.cat_entry = entry(top,"Tên danh mục...",width=180)
        self.cat_entry.pack(side="left",padx=(4,8))

        label(top,"Hạn mức (₫)",12,color=C["muted"]).pack(side="left")
        self.lim_entry = entry(top,"500000",width=140)
        self.lim_entry.pack(side="left",padx=(4,8))

        btn(top,"💾 Đặt ngân sách",self._save,width=160).pack(side="left",padx=4)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

    def _save(self):
        cat = self.cat_entry.get().strip()
        try: lim = float(self.lim_entry.get().replace(",",""))
        except: return
        if cat and lim > 0:
            self.db.set_budget(cat, lim)
            self.cat_entry.delete(0,"end")
            self.lim_entry.delete(0,"end")
            self.refresh()

    def refresh(self):
        for w in self.scroll.winfo_children(): w.destroy()
        month = datetime.now().strftime("%Y-%m")
        budgets = self.db.get_budgets()
        for b in budgets:
            rows = self.db.by_category("expense", month)
            spent = next((r["total"] for r in rows if r["category"]==b["category"]), 0)
            pct = min(spent / b["monthly_limit"], 1.0)
            color = C["expense"] if pct >= 0.9 else C["yellow"] if pct >= 0.7 else C["income"]

            f = card(self.scroll)
            f.pack(fill="x", pady=5, padx=4)
            header = ctk.CTkFrame(f, fg_color="transparent")
            header.pack(fill="x", padx=14, pady=(12,4))
            label(header, b["category"], 13, "bold").pack(side="left")
            label(header, f"₫{spent:,.0f} / ₫{b['monthly_limit']:,.0f}",
                  12, color=color).pack(side="right")

            pb = ctk.CTkProgressBar(f, height=8, corner_radius=4,
                                    fg_color=C["border"], progress_color=color)
            pb.pack(fill="x", padx=14, pady=(0,6))
            pb.set(pct)

            ctk.CTkLabel(f, text=f"{pct*100:.0f}% đã dùng",
                         font=ctk.CTkFont("Segoe UI",10),
                         text_color=C["muted"]).pack(anchor="e",padx=14,pady=(0,8))

            def _del(bid=b["id"]):
                self.db.delete_budget(bid); self.refresh()
            ctk.CTkButton(f, text="🗑", width=32, height=24,
                          fg_color="transparent", hover_color=C["border"],
                          command=_del).place(relx=1, rely=0, anchor="ne", x=-8, y=8)


class StatisticsPage(ctk.CTkFrame):
    def __init__(self, parent, db):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self._build()

    def _build(self):
        self.columnconfigure((0,1), weight=1)
        self.rowconfigure((0,1), weight=1)

        self.f1 = card(self); self.f1.grid(row=0,column=0,padx=6,pady=6,sticky="nsew")
        self.f2 = card(self); self.f2.grid(row=0,column=1,padx=6,pady=6,sticky="nsew")
        self.f3 = card(self); self.f3.grid(row=1,column=0,columnspan=2,padx=6,pady=6,sticky="nsew")

    def refresh(self):
        for f in [self.f1,self.f2,self.f3]:
            for w in f.winfo_children(): w.destroy()
        self._bar_income_cats()
        self._bar_expense_cats()
        self._monthly_bar()

    def _bar_income_cats(self):
        label(self.f1,"💹 Thu nhập theo danh mục",13,"bold").pack(anchor="w",padx=12,pady=(10,0))
        rows = self.db.by_category("income")
        if not rows:
            label(self.f1,"Chưa có dữ liệu",11,color=C["muted"]).pack(expand=True); return
        self._hbar(self.f1, [r["category"] for r in rows],
                   [r["total"] for r in rows], C["income"])

    def _bar_expense_cats(self):
        label(self.f2,"💸 Chi tiêu theo danh mục",13,"bold").pack(anchor="w",padx=12,pady=(10,0))
        rows = self.db.by_category("expense")
        if not rows:
            label(self.f2,"Chưa có dữ liệu",11,color=C["muted"]).pack(expand=True); return
        self._hbar(self.f2, [r["category"] for r in rows],
                   [r["total"] for r in rows], C["expense"])

    def _hbar(self, parent, cats, vals, color):
        fig = Figure(figsize=(3.8,2.6), dpi=96)
        fig.patch.set_facecolor(C["card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(C["card"])
        y = range(len(cats))
        bars = ax.barh(list(y), vals, color=color, alpha=0.85, height=0.55)
        ax.set_yticks(list(y)); ax.set_yticklabels(cats, color=C["text"], fontsize=9)
        ax.tick_params(colors=C["muted"], labelsize=8)
        for spine in ax.spines.values(): spine.set_edgecolor(C["border"])
        ax.xaxis.set_tick_params(labelcolor=C["muted"])
        for bar, val in zip(bars, vals):
            ax.text(bar.get_width()*1.01, bar.get_y()+bar.get_height()/2,
                    f"₫{val:,.0f}", va="center", fontsize=7, color=C["muted"])
        fig.tight_layout(pad=1)
        FigureCanvasTkAgg(fig, master=parent).get_tk_widget().pack(fill="both",expand=True,padx=4,pady=4)
        FigureCanvasTkAgg(fig, master=parent).draw()

    def _monthly_bar(self):
        label(self.f3,"📊 So sánh thu chi theo tháng",13,"bold").pack(anchor="w",padx=12,pady=(10,0))
        rows = self.db.monthly_trend(8)
        if not rows:
            label(self.f3,"Chưa có dữ liệu",11,color=C["muted"]).pack(expand=True); return
        months   = [r["m"] for r in rows]
        incomes  = [r["income"]  for r in rows]
        expenses = [r["expense"] for r in rows]
        x = range(len(months)); w = 0.38

        fig = Figure(figsize=(7,2.6), dpi=96)
        fig.patch.set_facecolor(C["card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(C["card"])
        ax.bar([i-w/2 for i in x], incomes,  width=w, color=C["income"],  alpha=0.85, label="Thu nhập")
        ax.bar([i+w/2 for i in x], expenses, width=w, color=C["expense"], alpha=0.85, label="Chi tiêu")
        ax.set_xticks(list(x)); ax.set_xticklabels(months, fontsize=8, color=C["muted"])
        ax.tick_params(colors=C["muted"], labelsize=8)
        for spine in ax.spines.values(): spine.set_edgecolor(C["border"])
        ax.legend(fontsize=8, facecolor=C["panel"], labelcolor=C["text"], edgecolor=C["border"])
        fig.tight_layout(pad=1)
        canvas = FigureCanvasTkAgg(fig, master=self.f3)
        canvas.draw(); canvas.get_tk_widget().pack(fill="both",expand=True,padx=4,pady=(0,8))


# ══════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════
class FinovaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("FINOVA — Quản lý Tài chính Cá nhân")
        self.geometry("1140x700")
        self.minsize(900,600)
        self.configure(fg_color=C["bg"])
        self.db = Database()
        self._build()
        self._show("dashboard")

    def _build(self):
        # ── Sidebar ────────────────────────────────────────
        sb = ctk.CTkFrame(self, fg_color=C["panel"], width=210, corner_radius=0)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        # Logo
        lf = ctk.CTkFrame(sb, fg_color="transparent")
        lf.pack(fill="x", pady=(20,4))
        ctk.CTkLabel(lf, text="💎", font=ctk.CTkFont(size=32)).pack()
        ctk.CTkLabel(lf, text="FINOVA",
                     font=ctk.CTkFont("Segoe UI",22,"bold"),
                     text_color=C["accent"]).pack()
        ctk.CTkLabel(lf, text="Tài chính cá nhân",
                     font=ctk.CTkFont("Segoe UI",10),
                     text_color=C["muted"]).pack(pady=(0,16))

        ctk.CTkFrame(sb, fg_color=C["border"], height=1).pack(fill="x",padx=12,pady=4)

        # Nav buttons
        self._nav_btns = {}
        nav_items = [
            ("dashboard",    "🏠  Tổng quan"),
            ("transactions", "📋  Giao dịch"),
            ("budget",       "📦  Ngân sách"),
            ("statistics",   "📊  Thống kê"),
        ]
        for key, text in nav_items:
            b = ctk.CTkButton(sb, text=text, width=186, height=42,
                              anchor="w",
                              font=ctk.CTkFont("Segoe UI",13),
                              fg_color="transparent",
                              hover_color=C["card"],
                              text_color=C["text"],
                              corner_radius=8,
                              command=lambda k=key: self._show(k))
            b.pack(padx=10, pady=3)
            self._nav_btns[key] = b

        ctk.CTkFrame(sb, fg_color=C["border"], height=1).pack(fill="x",padx=12,pady=12)

        # Quick Add
        btn(sb,"➕ Thêm giao dịch",
            lambda: TransactionDialog(self, self.db, self._refresh_all),
            width=186).pack(padx=10,pady=4)

        # Bottom info
        ctk.CTkLabel(sb, text=f"Python Programming\nCourse Final Project",
                     font=ctk.CTkFont("Segoe UI",9),
                     text_color=C["muted"], justify="center").pack(side="bottom",pady=16)

        # ── Content ────────────────────────────────────────
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(side="left", fill="both", expand=True, padx=16, pady=12)

        # Header
        hf = ctk.CTkFrame(self.content, fg_color="transparent")
        hf.pack(fill="x", pady=(0,12))
        self.page_title = ctk.CTkLabel(hf, text="Tổng quan",
                                       font=ctk.CTkFont("Segoe UI",22,"bold"),
                                       text_color=C["text"])
        self.page_title.pack(side="left")
        ctk.CTkLabel(hf, text=datetime.now().strftime("📅 %d/%m/%Y"),
                     font=ctk.CTkFont("Segoe UI",12),
                     text_color=C["muted"]).pack(side="right", pady=4)

        # Pages
        self.pages = {
            "dashboard":    DashboardPage(self.content, self.db),
            "transactions": TransactionsPage(self.content, self.db),
            "budget":       BudgetPage(self.content, self.db),
            "statistics":   StatisticsPage(self.content, self.db),
        }

    def _show(self, key):
        titles = {
            "dashboard":    "🏠  Tổng quan",
            "transactions": "📋  Giao dịch",
            "budget":       "📦  Ngân sách",
            "statistics":   "📊  Thống kê",
        }
        for k, p in self.pages.items():
            p.pack_forget()
        self.pages[key].pack(fill="both", expand=True)
        self.page_title.configure(text=titles[key])

        # Highlight nav
        for k, b in self._nav_btns.items():
            b.configure(fg_color=C["accent"] if k==key else "transparent")

        # Refresh
        self.pages[key].refresh()

    def _refresh_all(self):
        key = next(k for k,p in self.pages.items()
                   if p.winfo_manager()=="pack")
        self.pages[key].refresh()


if __name__ == "__main__":
    app = FinovaApp()
    app.mainloop()