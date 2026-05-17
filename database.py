"""
database.py — Lớp kết nối và thao tác với SQLite
Chứa tất cả các hàm CRUD (Create, Read, Update, Delete)
"""

import sqlite3
from config import DB_PATH


class Database:
    def __init__(self, path=DB_PATH):
        # Kết nối SQLite, check_same_thread=False cho phép dùng từ nhiều widget
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row   # Truy cập cột bằng tên: row["amount"]
        self._migrate()

    # ── Tạo bảng nếu chưa tồn tại ─────────────────────────
    def _migrate(self):
        c = self.conn.cursor()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS transactions (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            type          TEXT    NOT NULL CHECK(type IN ('income','expense')),
            category      TEXT    NOT NULL,
            amount        REAL    NOT NULL CHECK(amount > 0),
            note          TEXT,
            date          TEXT    NOT NULL,
            created_at    TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS budgets (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            category      TEXT    UNIQUE NOT NULL,
            monthly_limit REAL    NOT NULL CHECK(monthly_limit > 0)
        );
        """)
        self.conn.commit()

    # ══════════════════════════════════════════════════════
    #  TRANSACTIONS — Giao dịch
    # ══════════════════════════════════════════════════════

    def add_transaction(self, type_, category, amount, note, date_):
        """Thêm giao dịch mới."""
        self.conn.execute(
            "INSERT INTO transactions (type, category, amount, note, date) VALUES (?,?,?,?,?)",
            (type_, category, amount, note, date_)
        )
        self.conn.commit()

    def get_transactions(self, search="", type_filter="all", month=""):
        """
        Lấy danh sách giao dịch. Hỗ trợ:
          - search: tìm theo category hoặc note
          - type_filter: 'all' | 'income' | 'expense'
          - month: lọc theo tháng, định dạng 'YYYY-MM'
        """
        q = "SELECT * FROM transactions WHERE 1=1"
        params = []

        if search:
            q += " AND (category LIKE ? OR note LIKE ?)"
            params += [f"%{search}%", f"%{search}%"]

        if type_filter != "all":
            q += " AND type = ?"
            params.append(type_filter)

        if month:
            q += " AND date LIKE ?"
            params.append(f"{month}%")

        q += " ORDER BY date DESC, id DESC"
        return self.conn.execute(q, params).fetchall()

    def update_transaction(self, id_, type_, category, amount, note, date_):
        """Cập nhật giao dịch theo id."""
        self.conn.execute(
            "UPDATE transactions SET type=?, category=?, amount=?, note=?, date=? WHERE id=?",
            (type_, category, amount, note, date_, id_)
        )
        self.conn.commit()

    def delete_transaction(self, id_):
        """Xóa giao dịch theo id."""
        self.conn.execute("DELETE FROM transactions WHERE id=?", (id_,))
        self.conn.commit()

    # ══════════════════════════════════════════════════════
    #  SUMMARY — Tổng hợp số liệu (dùng cho Dashboard)
    # ══════════════════════════════════════════════════════

    def summary(self, month=""):
        """Trả về (tổng_thu, tổng_chi) trong tháng (hoặc toàn bộ nếu month='')."""
        where = f"AND date LIKE '{month}%'" if month else ""
        row = self.conn.execute(f"""
            SELECT
              COALESCE(SUM(CASE WHEN type='income'  THEN amount ELSE 0 END), 0) AS income,
              COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END), 0) AS expense
            FROM transactions WHERE 1=1 {where}
        """).fetchone()
        return row["income"], row["expense"]

    def by_category(self, type_, month=""):
        """Tổng hợp theo danh mục (dùng cho biểu đồ tròn và bar chart)."""
        where = f"AND date LIKE '{month}%'" if month else ""
        rows = self.conn.execute(f"""
            SELECT category, SUM(amount) AS total
            FROM transactions WHERE type=? {where}
            GROUP BY category ORDER BY total DESC
        """, (type_,)).fetchall()
        return rows

    def monthly_trend(self, limit=6):
        """Xu hướng thu/chi theo tháng, lấy `limit` tháng gần nhất."""
        rows = self.conn.execute("""
            SELECT strftime('%Y-%m', date) AS m,
                   SUM(CASE WHEN type='income'  THEN amount ELSE 0 END) AS income,
                   SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS expense
            FROM transactions
            GROUP BY m ORDER BY m DESC LIMIT ?
        """, (limit,)).fetchall()
        return list(reversed(rows))   # Đảo lại để chart hiển thị từ trái → phải

    # ══════════════════════════════════════════════════════
    #  BUDGETS — Ngân sách
    # ══════════════════════════════════════════════════════

    def set_budget(self, category, limit_):
        """Thêm hoặc cập nhật ngân sách cho một danh mục (UPSERT)."""
        self.conn.execute("""
            INSERT INTO budgets (category, monthly_limit) VALUES (?, ?)
            ON CONFLICT(category) DO UPDATE SET monthly_limit = excluded.monthly_limit
        """, (category, limit_))
        self.conn.commit()

    def get_budgets(self):
        """Lấy toàn bộ danh sách ngân sách."""
        return self.conn.execute("SELECT * FROM budgets ORDER BY category").fetchall()

    def delete_budget(self, id_):
        """Xóa ngân sách theo id."""
        self.conn.execute("DELETE FROM budgets WHERE id=?", (id_,))
        self.conn.commit()