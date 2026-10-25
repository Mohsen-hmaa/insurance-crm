import tkinter as tk
from datetime import date, timedelta
from tkinter import ttk, messagebox, filedialog

from gui.styles import (
    COLORS,
    configure_report_styles,
    finalize_report_window,
)
from gui.window_registry import SingleWindowMixin, register_window
from services.date_service import (
    convert_shamsi_to_date,
    convert_date_to_shamsi,
)
from services.policy_report_service import (
    generate_expiry_report,
    get_expiry_policies,
)
from services.policy_service import load_policies


class PolicyReports(SingleWindowMixin, tk.Toplevel):

    def __init__(self, parent, show_menu=True):
        super().__init__(parent)

        configure_report_styles()

        self.configure(bg=COLORS["surface"])
        self.title("گزارش‌های بیمه‌نامه‌ها")
        self.geometry("600x500")
        self.resizable(False, False)

        if show_menu:
            self.create_widgets()

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------
    def _new_window(
        self,
        title,
        geometry,
        resizable=False,
        minsize=None,
        key=None,
    ):
        window = tk.Toplevel(self)
        if key:
            register_window(key, window)
        window.configure(bg=COLORS["surface"])
        window.title(title)
        window.geometry(geometry)
        window.resizable(resizable, resizable)
        if minsize:
            window.minsize(*minsize)
        return window

    # ---------------------------------------------------------
    # Main UI
    # ---------------------------------------------------------
    def create_widgets(self):
        ttk.Label(
            self,
            text="گزارش‌های بیمه‌نامه‌ها",
            font=("Tahoma", 16, "bold"),
        ).pack(pady=20)

        policy_frame = ttk.LabelFrame(self, text="")
        policy_frame.pack(fill="x", padx=30, pady=10)

        buttons = [
            (
                "گزارش بیمه نامه های منقضی شونده در یک بازه زمانی",
                self.open_expiry_report,
            ),
            (
                "بیمه‌نامه‌های منقضی شونده روز جاری",
                self.open_today_expired_report,
            ),
            (
                "بیمه‌نامه‌های در شرف انقضا تا ۵ روز آینده",
                self.open_upcoming_expiry_report,
            ),
        ]
        for text, command in buttons:
            ttk.Button(
                policy_frame,
                text=text,
                command=command,
            ).pack(fill="x", padx=15, pady=5, ipady=10)

        finalize_report_window(self)

    # ---------------------------------------------------------
    # Expiry Report Window (خروجی اکسل)
    # ---------------------------------------------------------
    def open_expiry_report(self):
        if self.reuse_window("policy_expiry_range"):
            return

        expiry_window = self._new_window(
            "گزارش بیمه‌نامه‌های در حال انقضا",
            "500x380",
            key="policy_expiry_range",
        )

        ttk.Label(
            expiry_window,
            text="بیمه‌نامه‌های در حال انقضا",
            style="CommissionTitle.TLabel",
            anchor="e",
        ).pack(fill="x", padx=30, pady=20)

        # Filter frame
        filter_frame = ttk.LabelFrame(
            expiry_window,
            text="بازه تاریخ پایان",
            labelanchor="ne",
        )
        filter_frame.pack(fill="x", padx=30, pady=10)
        filter_frame.columnconfigure(0, weight=1)

        entries = []
        for row, label_text in enumerate(("از تاریخ:", "تا تاریخ:")):
            ttk.Label(
                filter_frame,
                text=label_text,
            ).grid(row=row, column=1, padx=10, pady=10, sticky="e")

            entry = ttk.Entry(filter_frame, width=20, justify="center")
            entry.grid(row=row, column=0, padx=10, pady=10, sticky="e")
            entries.append(entry)

        from_date_entry, to_date_entry = entries

        ttk.Button(
            expiry_window,
            text="تهیه گزارش",
            command=lambda: self.run_expiry_report(
                from_date_entry,
                to_date_entry,
                expiry_window,
            ),
        ).pack(pady=20, ipadx=30, ipady=4)

        finalize_report_window(expiry_window)

    # ---------------------------------------------------------
    # Run Expiry Report
    # ---------------------------------------------------------
    def run_expiry_report(
        self,
        end_date_from_entry,
        end_date_to_entry,
        expiry_window,
    ):
        end_date_from = end_date_from_entry.get().strip()
        end_date_to = end_date_to_entry.get().strip()

        # Empty dates
        if not end_date_from or not end_date_to:
            messagebox.showerror(
                "خطا",
                "لطفاً تاریخ شروع و پایان بازه را وارد کنید.",
                parent=expiry_window,
            )
            return

        # Convert dates
        try:
            end_date_from = convert_shamsi_to_date(end_date_from)
            end_date_to = convert_shamsi_to_date(end_date_to)
        except (ValueError, AttributeError):
            messagebox.showerror(
                "خطا",
                "فرمت تاریخ وارد شده صحیح نیست.",
                parent=expiry_window,
            )
            return

        if end_date_from > end_date_to:
            messagebox.showerror(
                "خطا",
                "تاریخ شروع بازه نمی‌تواند بعد از تاریخ پایان بازه باشد.",
                parent=expiry_window,
            )
            return

        policies = load_policies()

        file_path = filedialog.asksaveasfilename(
            parent=expiry_window,
            title="ذخیره گزارش",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            initialfile=(
                f"expiry_report"
                f"{convert_date_to_shamsi(end_date_from).replace('/', '_')}"
                f"_to_"
                f"{convert_date_to_shamsi(end_date_to).replace('/', '_')}"
                f".xlsx"
            ),
        )
        if not file_path:
            return

        generate_expiry_report(
            policies,
            end_date_from,
            end_date_to,
            file_path,
        )

        messagebox.showinfo(
            "گزارش",
            "گزارش با موفقیت ذخیره شد.",
            parent=expiry_window,
        )
        expiry_window.destroy()

    # ---------------------------------------------------------
    # فهرست بیمه‌نامه‌های امروز / ۵ روز آینده
    # ---------------------------------------------------------
    def _open_expiry_list_window(
        self,
        title,
        start_date,
        end_date,
        empty_message,
        key,
    ):
        if self.reuse_window(key):
            return

        window = self._new_window(
            title,
            "1100x500",
            resizable=True,
            minsize=(900, 400),
            key=key,
        )

        ttk.Label(
            window,
            text=title,
            style="CommissionTitle.TLabel",
            anchor="e",
        ).pack(fill="x", padx=20, pady=15)

        policies = load_policies()
        filtered_policies = get_expiry_policies(
            policies,
            start_date,
            end_date,
        )

        self.show_expiry_treeview(window, filtered_policies, empty_message)

        finalize_report_window(window)

    def open_today_expired_report(self):
        today = date.today()
        self._open_expiry_list_window(
            "بیمه‌نامه‌های منقضی شده روز جاری",
            today,
            today,
            "امروز بیمه‌نامه‌ای منقضی نمی‌شود.",
            "policy_expired_today",
        )

    def open_upcoming_expiry_report(self):
        today = date.today()
        self._open_expiry_list_window(
            "بیمه‌نامه‌های در شرف انقضا تا ۵ روز آینده",
            today,
            today + timedelta(days=5),
            "تا ۵ روز آینده بیمه‌نامه‌ای منقضی نمی‌شود.",
            "policy_expiry_upcoming",
        )

    # ---------------------------------------------------------
    # Treeview
    # ---------------------------------------------------------
    def show_expiry_treeview(self, parent, policies, empty_message=""):
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Treeview از چپ به راست نمایش داده می‌شود؛ بنابراین از سمت راست:
        # تیک | ردیف | بیمه‌گذار | شماره بیمه‌نامه |
        # رشته بیمه | تاریخ پایان | معرف | موبایل
        columns = (
            "mobile",
            "referrer",
            "end_date",
            "insurance_type",
            "policy_number",
            "customer",
            "row",
            "check",
        )

        headings = {
            "check": "",
            "row": "ردیف",
            "customer": "بیمه‌گذار",
            "policy_number": "شماره بیمه‌نامه",
            "insurance_type": "رشته بیمه",
            "end_date": "تاریخ پایان",
            "referrer": "معرف",
            "mobile": "موبایل",
        }

        widths = {
            "check": 45,
            "row": 60,
            "customer": 220,
            "policy_number": 120,
            "insurance_type": 180,
            "end_date": 110,
            "referrer": 180,
            "mobile": 120,
        }

        # رنگ هدر و زمینه از استایل پایه‌ی Treeview در styles.py
        # ارث‌بری می‌شود؛ اینجا فقط فونت و ارتفاع ردیف تنظیم می‌شود.
        style = ttk.Style()
        style.configure(
            "Expiry.Treeview",
            font=("Tahoma", 10),
            rowheight=28,
        )
        style.configure(
            "Expiry.Treeview.Heading",
            font=("Tahoma", 10, "bold"),
        )

        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="Expiry.Treeview",
        )

        # Column configuration
        for column in columns:
            anchor = "e" if column in ("customer", "insurance_type") else "center"

            tree.heading(column, text=headings[column], anchor="center")
            tree.column(
                column,
                width=widths[column],
                minwidth=widths[column],
                anchor=anchor,
                stretch=False,
            )

        # Row colors
        tree.tag_configure("odd", background=COLORS["surface"])
        tree.tag_configure("even", background="#E8EEF7")
        tree.tag_configure("odd_checked", background="#A9D18E")
        tree.tag_configure("even_checked", background="#93C47D")

        # Insert rows
        for index, policy in enumerate(policies, start=1):
            customer_name = ""
            if policy.customer:
                customer_name = (
                    f"{policy.customer.name or ''} "
                    f"{policy.customer.family or ''} "
                    f"{policy.customer.customer_code or ''}"
                ).strip()

            insurance_type = ""
            if policy.insurance_type:
                insurance_type = (
                    policy.insurance_type.display_name or ""
                ).strip()

            referrer = policy.referrer if policy.referrer else ""

            mobile = "-"
            if policy.customer:
                mobile = policy.customer.phone or "-"

            row_tag = "even" if index % 2 == 0 else "odd"

            # ترتیب values دقیقاً مطابق columns است
            values = (
                mobile,
                referrer,
                convert_date_to_shamsi(policy.end_date),
                insurance_type,
                policy.policy_number or "",
                customer_name,
                index,
                "☐",
            )

            tree.insert("", "end", values=values, tags=(row_tag,))

        # Checkbox click
        def toggle_checkbox(event):
            if tree.identify("region", event.x, event.y) != "cell":
                return

            # ستون هشتم = checkbox
            if tree.identify_column(event.x) != "#8":
                return

            item_id = tree.identify_row(event.y)
            if not item_id:
                return

            row_number = int(tree.item(item_id, "values")[6])
            is_even = row_number % 2 == 0

            if tree.set(item_id, "check") == "☐":
                tree.set(item_id, "check", "☑")
                new_tag = "even_checked" if is_even else "odd_checked"
            else:
                tree.set(item_id, "check", "☐")
                new_tag = "even" if is_even else "odd"

            tree.item(item_id, tags=(new_tag,))

        tree.bind("<Button-1>", toggle_checkbox)

        # Scrollbars
        vertical_scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=tree.yview
        )
        horizontal_scrollbar = ttk.Scrollbar(
            tree_frame, orient="horizontal", command=tree.xview
        )
        tree.configure(
            yscrollcommand=vertical_scrollbar.set,
            xscrollcommand=horizontal_scrollbar.set,
        )

        tree.grid(row=0, column=0, sticky="nsew")
        vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        horizontal_scrollbar.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # No result
        if not policies and empty_message:
            ttk.Label(
                parent,
                text=empty_message,
                font=("Tahoma", 10),
            ).pack(pady=10)
