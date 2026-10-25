import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from gui.styles import COLORS, set_title_bar_color
from services.policy_details_service import get_policy_details
from services.date_service import convert_date_to_shamsi
def _format_date(value):
    if not value:
        return "-----"
    return convert_date_to_shamsi(value)
def _format_amount(value):
    if value is None:
        return "0"
    return f"{value:,}"
def _add_section_title(parent, text):
    tk.Label(
        parent,
        text=text,
        font=("Arial", 12, "bold"),
        anchor="e"
    ).pack(
        fill="x",
        padx=10,
        pady=(12, 5)
    )
class PolicyDetails:
    def __init__(self, parent, policy_id):
        self.parent = parent
        self.policy_id = policy_id
        self.window = tk.Toplevel(parent)
        self.window.title("جزئیات بیمه‌نامه")
        self.window.state("zoomed")
        self.window.after(
            200,
            lambda: set_title_bar_color(
                self.window,
                COLORS["primary"],
            ),
        )
        self.create_widgets()
        self.load_data()
        self.window.protocol(
            "WM_DELETE_WINDOW",
            self.close_window
        )
    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def create_widgets(self):
        title_frame = tk.Frame(self.window)
        title_frame.pack(
            fill="x",
            padx=15,
            pady=10
        )
        tk.Label(
            title_frame,
            text="جزئیات بیمه‌نامه",
            font=("Arial", 15, "bold"),
            anchor="e"
        ).pack(anchor="e")
        # -----------------------------------------------------
        # Scrollable area
        # -----------------------------------------------------
        container = tk.Frame(self.window)
        container.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        )
        self.canvas = tk.Canvas(
            container,
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            container,
            orient="vertical",
            command=self.canvas.yview
        )
        self.canvas.configure(
            yscrollcommand=scrollbar.set
        )
        scrollbar.pack(
            side="right",
            fill="y"
        )
        self.canvas.pack(
            side="left",
            fill="both",
            expand=True
        )
        self.content_frame = tk.Frame(
            self.canvas
        )
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.content_frame,
            anchor="nw"
        )
        self.content_frame.bind(
            "<Configure>",
            self._update_scroll_region
        )
        self.canvas.bind(
            "<Configure>",
            self._resize_content
        )
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        # -----------------------------------------------------
        # Close button
        # -----------------------------------------------------
        tk.Button(
            self.window,
            text="بستن",
            width=20,
            background="#CDCCCC",
            command=self.close_window
        ).pack(
            pady=10
        )
    # ---------------------------------------------------------
    # Scroll
    # ---------------------------------------------------------
    def _update_scroll_region(self, event=None):
        self.canvas.configure(
            scrollregion=self.canvas.bbox("all")
        )
    def _resize_content(self, event):
        self.canvas.itemconfig(
            self.canvas_window,
            width=event.width
        )
    # ---------------------------------------------------------
    # Load data
    # ---------------------------------------------------------
    def load_data(self):
        details = get_policy_details(
            self.policy_id
        )
        if not details:
            messagebox.showerror(
                "خطا",
                "اطلاعات بیمه‌نامه پیدا نشد.",
                parent=self.window
            )
            self.window.destroy()
            return
        policy = details["policy"]
        collections = details["collections"]
        latest_endorsement_number = (
            details["latest_endorsement_number"]
        )
        # -----------------------------------------------------
        # Calculate financial information
        # -----------------------------------------------------
        total_collected = sum(
            (collection.settlement_amount or 0)
            for collection in collections
        )
        premium = policy.premium or 0
        debt_amount = max(
            premium - total_collected,
            0
        )
        # -----------------------------------------------------
        # Build sections
        # -----------------------------------------------------
        self.build_policy_section(
            policy,
            latest_endorsement_number
        )
        self.build_customer_section(
            policy
        )
        self.build_collections_section(
            collections,
            total_collected,
            debt_amount
        )
    # ---------------------------------------------------------
    # Policy information
    # ---------------------------------------------------------
    def build_policy_section(
        self,
        policy,
        latest_endorsement_number
    ):
        _add_section_title(
            self.content_frame,
            "اطلاعات بیمه‌نامه"
        )
        frame = tk.Frame(
            self.content_frame,
            relief="groove",
            borderwidth=1
        )
        frame.pack(
            fill="x",
            padx=10,
            pady=5
        )
        for column in range(4):
            frame.columnconfigure(
                column,
                weight=1
            )
        values = [
            (
                "شماره بیمه‌نامه",
                policy.policy_number
            ),
            (
                "کد رایانه‌ای",
                policy.computer_code
            ),
            (
                "کد صدور",
                policy.issue_code
            ),
            (
                "شماره آخرین الحاقیه",
                latest_endorsement_number
            ),
            (
                "تاریخ صدور",
                _format_date(policy.issue_date)
            ),
            (
                "تاریخ شروع",
                _format_date(policy.start_date)
            ),
            (
                "تاریخ پایان",
                _format_date(policy.end_date)
            ),
            (
                "حق‌بیمه",
                _format_amount(policy.premium)
            ),
            (
                "سهم صندوق",
                _format_amount(policy.fund)
            ),
            (
                "وضعیت",
                "مرهوناتی"
                if policy.is_mortgage
                else "غیر مرهوناتی"
            ),
            (
                "صادرکننده",
                policy.issuer
            ),
            (
                "معرف",
                policy.referrer
            ),
            (
                "واحد کاری معرف",
                policy.referrer_work_unit
            ),
            (
                "بازاریاب",
                policy.marketer.name
                if policy.marketer
                else None
            ),
            (
                "نوع بیمه",
                policy.insurance_type.display_name
                if policy.insurance_type
                else None
            ),
        ]
        for index, (label, value) in enumerate(values):
            row = index // 2
            pair = index % 2
            if pair == 0:
                label_column = 3
                value_column = 2
            else:
                label_column = 1
                value_column = 0
            tk.Label(
                frame,
                text=label,
                font=("Arial", 10, "bold"),
                anchor="e"
            ).grid(
                row=row,
                column=label_column,
                padx=8,
                pady=6,
                sticky="e"
            )
            tk.Label(
                frame,
                text=(
                    value
                    if value not in (None, "")
                    else "-----"
                ),
                anchor="e"
            ).grid(
                row=row,
                column=value_column,
                padx=8,
                pady=6,
                sticky="e"
            )
    # ---------------------------------------------------------
    # Customer information
    # ---------------------------------------------------------
    def build_customer_section(self, policy):
        _add_section_title(
            self.content_frame,
            "اطلاعات بیمه‌گذار"
        )
        frame = tk.Frame(
            self.content_frame,
            relief="groove",
            borderwidth=1
        )
        frame.pack(
            fill="x",
            padx=10,
            pady=5
        )
        customer = policy.customer
        if not customer:
            tk.Label(
                frame,
                text="اطلاعات بیمه‌گذار موجود نیست."
            ).pack(
                padx=10,
                pady=10
            )
            return
        for column in range(4):
            frame.columnconfigure(
                column,
                weight=1
            )
        full_name = (
            f"{customer.name} "
            f"{customer.family or ''}"
        ).strip()
        values = [
            (
                "نام و نام خانوادگی",
                full_name
            ),
            (
                "کد مشتری",
                customer.customer_code
            ),
            (
                "کد ملی",
                customer.national_id
            ),
            (
                "تلفن",
                customer.phone
            ),
        ]
        for index, (label, value) in enumerate(values):
            if index % 2 == 0:
                label_column = 3
                value_column = 2
            else:
                label_column = 1
                value_column = 0
            row = index // 2
            tk.Label(
                frame,
                text=label,
                font=("Arial", 10, "bold"),
                anchor="e"
            ).grid(
                row=row,
                column=label_column,
                padx=8,
                pady=6,
                sticky="e"
            )
            tk.Label(
                frame,
                text=(
                    value
                    if value not in (None, "")
                    else "-----"
                ),
                anchor="e"
            ).grid(
                row=row,
                column=value_column,
                padx=8,
                pady=6,
                sticky="e"
            )
    # ---------------------------------------------------------
    # Collections + Debt
    # ---------------------------------------------------------
    def build_collections_section(
        self,
        collections,
        total_collected,
        debt_amount
    ):
        _add_section_title(
            self.content_frame,
            "وصولی‌ها و بدهی بیمه‌نامه"
        )
        frame = tk.Frame(
            self.content_frame,
            relief="groove",
            borderwidth=1
        )
        frame.pack(
            fill="x",
            padx=10,
            pady=5
        )
        columns = (
            "due_date",
            "collection_date",
            "amount"
        )
        tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            height=8
        )
        tree.heading(
            "due_date",
            text="تاریخ سررسید",
            anchor="e"
        )
        tree.heading(
            "collection_date",
            text="تاریخ وصول",
            anchor="e"
        )
        tree.heading(
            "amount",
            text="مبلغ وصول",
            anchor="e"
        )
        tree.column(
            "due_date",
            width=150,
            anchor="e"
        )
        tree.column(
            "collection_date",
            width=150,
            anchor="e"
        )
        tree.column(
            "amount",
            width=180,
            anchor="e"
        )
        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=tree.yview
        )
        tree.configure(
            yscrollcommand=scrollbar.set
        )
        tree.pack(
            side="left",
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )
        scrollbar.pack(
            side="right",
            fill="y",
            pady=5
        )
        # -----------------------------------------------------
        # Sort collections
        # -----------------------------------------------------
        sorted_collections = sorted(
            collections,
            key=lambda item: (
                item.collection_date
                or item.due_date
                or date.min
            )
        )
        for collection in sorted_collections:
            amount = (
                collection.settlement_amount
                or 0
            )
            tree.insert(
                "",
                "end",
                values=(
                    _format_date(
                        collection.due_date
                    ),
                    _format_date(
                        collection.collection_date
                    ),
                    _format_amount(
                        amount
                    ),
                )
            )
        # -----------------------------------------------------
        # Financial summary
        # -----------------------------------------------------
        summary_frame = tk.Frame(
            self.content_frame
        )
        summary_frame.pack(
            fill="x",
            padx=10,
            pady=(0, 10)
        )
        tk.Label(
            summary_frame,
            text=(
                f"جمع وصولی: "
                f"{_format_amount(total_collected)}"
            ),
            font=("Arial", 10, "bold"),
            anchor="e"
        ).pack(
            anchor="e",
            pady=2
        )
        tk.Label(
            summary_frame,
            text=(
                f"مانده بدهی: "
                f"{_format_amount(debt_amount)}"
            ),
            font=("Arial", 11, "bold"),
            anchor="e"
        ).pack(
            anchor="e",
            pady=2
        )
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units"
        )
    def close_window(self):
        self.canvas.unbind_all("<MouseWheel>")
        self.window.destroy()
def open_policy_details(parent, policy_id):
    return PolicyDetails(
        parent,
        policy_id
    )