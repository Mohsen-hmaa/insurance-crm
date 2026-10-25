import tkinter as tk
from tkinter import ttk, messagebox

from gui.customer_selector import open_customer_selector
from gui.styles import (
    COLORS,
    configure_report_styles,
    apply_report_window_style,
    finalize_report_window,
)
from gui.window_registry import SingleWindowMixin, register_window
from services.date_service import convert_shamsi_to_date
from services.customer_report_service import (
    get_customer_payment_behavior,
    get_customers_with_average_delay_between,
    get_customers_with_over_15_days_delay,
    get_customers_by_total_premium,
)


class CustomerReports(SingleWindowMixin, tk.Toplevel):

    def __init__(self, parent, show_menu=True):
        super().__init__(parent)

        configure_report_styles()

        self.configure(bg=COLORS["surface"])
        self.title("گزارش بیمه‌گذاران")
        self.geometry("600x500")
        self.resizable(False, False)

        if show_menu:
            self.create_widgets()

    # =========================================================
    # Helpers
    # =========================================================
    def _new_window(self, title, geometry, heading, key=None):
        window = tk.Toplevel(self)
        if key:
            register_window(key, window)
        window.configure(bg=COLORS["surface"])
        window.title(title)
        window.geometry(geometry)
        window.resizable(False, False)

        ttk.Label(
            window,
            text=heading,
            style="CommissionTitle.TLabel",
            anchor="e",
        ).pack(fill="x", padx=30, pady=(20, 0))

        return window

    @staticmethod
    def _clear(frame):
        for widget in frame.winfo_children():
            widget.destroy()

    # =========================================================
    # Main UI
    # =========================================================
    def create_widgets(self):
        ttk.Label(
            self,
            text="گزارش بیمه‌گذاران",
            font=("Tahoma", 16, "bold"),
        ).pack(pady=20)

        customer_frame = ttk.LabelFrame(self, text="")
        customer_frame.pack(fill="x", padx=30, pady=10)

        buttons = [
            ("گزارش میزان خوش حسابی بیمه گذار", self.open_payment_behavior_report),
            (
                "گزارش بیمه‌گذاران با میانگین تأخیر بیش از مدت معین",
                self.open_average_delay_report,
            ),
            (
                "گزارش بیمه‌گذاران بر اساس مجموع حق‌بیمه",
                self.open_total_premium_report,
            ),
        ]
        for text, command in buttons:
            ttk.Button(
                customer_frame,
                text=text,
                command=command,
            ).pack(fill="x", padx=15, pady=5, ipady=10)

        finalize_report_window(self)

    # =========================================================
    # گزارش اول: میزان خوش‌حسابی
    # =========================================================
    def open_payment_behavior_report(self):
        if self.reuse_window("customer_payment_behavior"):
            return

        window = self._new_window(
            "گزارش میزان خوش حسابی بیمه گذار",
            "600x560",
            "میزان خوش‌حسابی بیمه‌گذار",
            key="customer_payment_behavior",
        )
        self.payment_behavior_window = window

        # انتخاب بیمه‌گذار
        customer_frame = ttk.LabelFrame(window, text="")
        customer_frame.pack(fill="x", padx=30, pady=15)

        ttk.Label(
            customer_frame,
            text="بیمه گذار:",
        ).pack(side="right", padx=10, pady=10)

        self.customer_name_var = tk.StringVar()
        self.customer_entry = ttk.Entry(
            customer_frame,
            textvariable=self.customer_name_var,
            state="readonly",
            justify="right",
            width=35,
        )
        self.customer_entry.pack(side="right", padx=5, pady=10)

        ttk.Button(
            customer_frame,
            text="انتخاب",
            command=self.select_report_customer,
        ).pack(side="right", padx=10, pady=10)

        # محل نمایش نتیجه
        self.payment_result_frame = ttk.LabelFrame(
            window,
            text="نتیجه گزارش",
            labelanchor="ne",
        )
        self.payment_result_frame.pack(
            fill="both", expand=True, padx=30, pady=10
        )

        finalize_report_window(window)

    def select_report_customer(self):
        open_customer_selector(
            self.payment_behavior_window,
            on_selected=self.on_customer_selected,
        )

    def on_customer_selected(self, customer):
        customer_name = f"{customer.name} {customer.family or ''}".strip()
        self.customer_name_var.set(customer_name)

        try:
            report = get_customer_payment_behavior(customer.id)
        except Exception as e:
            messagebox.showerror(
                "خطا",
                f"خطا در تهیه گزارش:\n{e}",
                parent=self.payment_behavior_window,
            )
            return

        self.show_payment_behavior_report(report)

    def show_payment_behavior_report(self, report):
        self._clear(self.payment_result_frame)

        if not report:
            ttk.Label(
                self.payment_result_frame,
                text="اطلاعاتی برای این بیمه‌گذار یافت نشد.",
            ).pack(pady=20)
            apply_report_window_style(self.payment_result_frame)
            return

        # سرویس برای بیمه‌گذار بدون وصولی سررسیددار میانگین 0 برمی‌گرداند؛
        # در این حالت عدد 0.00 گمراه‌کننده است.
        if not report["total_collections"]:
            average_delay_text = "-"
        else:
            average_delay_text = f'{report["average_delay"]:.2f} روز'

        report_rows = [
            ("تعداد وصولی‌های سررسیددار", report["total_collections"]),
            ("میانگین تأخیر در وصولی", average_delay_text),
            ("تعداد پرداختی در موعد سررسید", report["on_time_count"]),
            ("تعداد پرداختی یک روز بعد از سررسید", report["one_day_late_count"]),
            ("تعداد پرداختی 2 تا 5 روز بعد از سررسید", report["up_to_5_days_count"]),
            ("تعداد پرداختی 6 تا 10 روز بعد از سررسید", report["up_to_10_days_count"]),
            ("تعداد پرداختی 11 تا 14 روز بعد از سررسید", report["up_to_15_days_count"]),
            ("تعداد پرداختی 15 روز به بالا بعد از سررسید", report["over_15_days_count"]),
        ]

        # یک فریم داخلی؛ همه فرزندان این فریم با grid
        result_table = ttk.Frame(self.payment_result_frame)
        result_table.pack(fill="x", padx=15, pady=10)

        for row, (label, value) in enumerate(report_rows):
            ttk.Label(
                result_table,
                text=label,
            ).grid(row=row, column=1, sticky="e", padx=10, pady=4)

            ttk.Label(
                result_table,
                text=value,
                font=("Tahoma", 10, "bold"),
            ).grid(row=row, column=0, sticky="w", padx=10, pady=4)

        result_table.columnconfigure(1, weight=1)

        # ویجت‌های ساخته‌شده بعد از باز شدن پنجره هم هم‌استایل شوند
        apply_report_window_style(self.payment_result_frame)

    # =========================================================
    # گزارش دوم: میانگین تأخیر
    # =========================================================
    def open_average_delay_report(self):
        if self.reuse_window("customer_average_delay"):
            return

        window = self._new_window(
            "گزارش بیمه‌گذاران با میانگین تأخیر",
            "900x700",
            "بیمه‌گذاران با میانگین تأخیر",
            key="customer_average_delay",
        )
        self.delay_report_window = window

        criteria_frame = ttk.LabelFrame(
            window,
            text="معیار گزارش",
            labelanchor="ne",
        )
        criteria_frame.pack(fill="x", padx=30, pady=20)

        self.delay_report_option = tk.IntVar(value=0)

        options = [
            ("میانگین تأخیر ۵ تا ۱۰ روز", 1),
            ("میانگین تأخیر ۱۰ تا ۱۵ روز", 2),
            ("میانگین تأخیر ۱۵ روز به بالا", 3),
            ("دارای موارد تأخیر ۱۵ روز به بالا", 4),
        ]
        for text, value in options:
            ttk.Radiobutton(
                criteria_frame,
                text=text,
                variable=self.delay_report_option,
                value=value,
                command=self.show_average_delay_report,
            ).pack(anchor="e", padx=15, pady=5)

        self.delay_result_frame = ttk.LabelFrame(
            window,
            text="نتیجه گزارش",
            labelanchor="ne",
        )
        self.delay_result_frame.pack(
            fill="both", expand=True, padx=30, pady=10
        )

        finalize_report_window(window)

    def show_average_delay_report(self):
        option = self.delay_report_option.get()

        try:
            if option == 1:
                results = get_customers_with_average_delay_between(5, 10)
            elif option == 2:
                results = get_customers_with_average_delay_between(10, 15)
            elif option == 3:
                results = get_customers_with_average_delay_between(15, None)
            elif option == 4:
                results = get_customers_with_over_15_days_delay()
            else:
                results = []
        except Exception as e:
            messagebox.showerror(
                "خطا",
                f"خطا در تهیه گزارش:\n{e}",
                parent=self.delay_report_window,
            )
            return

        self._clear(self.delay_result_frame)

        if not results:
            ttk.Label(
                self.delay_result_frame,
                text="موردی یافت نشد.",
            ).pack(pady=20)
            apply_report_window_style(self.delay_result_frame)
            return

        columns = (
            "over_15_days",
            "average_delay",
            "total_collections",
            "customer",
            "row",
        )

        result_table = ttk.Treeview(
            self.delay_result_frame,
            columns=columns,
            show="headings",
        )

        result_table.heading("over_15_days", text="موارد تأخیر ۱۵ روز به بالا")
        result_table.heading("average_delay", text="میانگین تأخیر")
        result_table.heading(
            "total_collections", text="تعداد وصولی‌های سررسیددار"
        )
        result_table.heading("customer", text="بیمه‌گذار")
        result_table.heading("row", text="ردیف")

        result_table.column("row", width=60, anchor="center")
        result_table.column("customer", width=300, anchor="e")
        result_table.column("total_collections", width=150, anchor="center")
        result_table.column("average_delay", width=120, anchor="center")
        result_table.column("over_15_days", width=170, anchor="center")

        for index, item in enumerate(results, start=1):
            customer_name = (
                f'{item["customer_name"]} {item["customer_family"]}'
            ).strip()
            customer_display = f'{customer_name} - کد: {item["customer_code"]}'

            result_table.insert(
                "",
                "end",
                values=(
                    item["over_15_days_count"],
                    f'{item["average_delay"]:.2f}',
                    item["total_collections"],
                    customer_display,
                    index,
                ),
            )

        scrollbar = ttk.Scrollbar(
            self.delay_result_frame,
            orient="vertical",
            command=result_table.yview,
        )
        result_table.configure(yscrollcommand=scrollbar.set)

        result_table.pack(side="right", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")

    # =========================================================
    # گزارش سوم: مجموع حق‌بیمه
    # =========================================================
    def open_total_premium_report(self):
        if self.reuse_window("customer_total_premium"):
            return

        window = self._new_window(
            "گزارش بیمه‌گذاران بر اساس مجموع حق‌بیمه",
            "900x660",
            "بیمه‌گذاران بر اساس مجموع حق‌بیمه",
            key="customer_total_premium",
        )
        self.total_premium_window = window

        criteria_frame = ttk.LabelFrame(
            window,
            text="معیار گزارش",
            labelanchor="ne",
        )
        criteria_frame.pack(fill="x", padx=30, pady=20)

        self.total_premium_option = tk.IntVar(value=0)

        for text, value in (("کل دوره", 1), ("بازه زمانی مشخص", 2)):
            ttk.Radiobutton(
                criteria_frame,
                text=text,
                variable=self.total_premium_option,
                value=value,
                command=self.show_total_premium_report,
            ).pack(anchor="e", padx=15, pady=5)

        date_frame = ttk.Frame(window)
        date_frame.pack(fill="x", padx=30, pady=5)

        ttk.Label(date_frame, text="از تاریخ:").pack(side="right", padx=5)
        self.total_premium_from_date = ttk.Entry(
            date_frame, width=15, justify="center"
        )
        self.total_premium_from_date.pack(side="right", padx=5)
        self.total_premium_from_date.bind(
            "<KeyRelease>", self.on_total_premium_date_changed
        )

        ttk.Label(date_frame, text="تا تاریخ:").pack(side="right", padx=5)
        self.total_premium_to_date = ttk.Entry(
            date_frame, width=15, justify="center"
        )
        self.total_premium_to_date.pack(side="right", padx=5)
        self.total_premium_to_date.bind(
            "<KeyRelease>", self.on_total_premium_date_changed
        )

        self.total_premium_result_frame = ttk.LabelFrame(
            window,
            text="نتیجه گزارش",
            labelanchor="ne",
        )
        self.total_premium_result_frame.pack(
            fill="both", expand=True, padx=30, pady=10
        )

        finalize_report_window(window)

    def _read_total_premium_dates(self):
        """
        برمی‌گرداند (from_date, to_date) یا None اگر تاریخ‌ها هنوز کامل
        یا معتبر نیستند. تاریخ باید به صورت کامل YYYY/MM/DD وارد شده باشد
        و حداقل یکی از دو تاریخ لازم است.
        """
        dates = []

        for entry in (
            self.total_premium_from_date,
            self.total_premium_to_date,
        ):
            text = entry.get().strip()

            if not text:
                dates.append(None)
                continue

            if len(text) != 10:
                return None

            try:
                value = convert_shamsi_to_date(text)
            except Exception:
                return None

            if value is None:
                return None

            dates.append(value)

        if dates[0] is None and dates[1] is None:
            return None

        return tuple(dates)

    def show_total_premium_report(self):
        option = self.total_premium_option.get()

        try:
            if option == 1:
                # کل دوره
                results = get_customers_by_total_premium()

            elif option == 2:
                # بازه زمانی مشخص
                dates = self._read_total_premium_dates()
                if dates is None:
                    return
                results = get_customers_by_total_premium(*dates)

            else:
                return
        except Exception as e:
            messagebox.showerror(
                "خطا",
                f"خطا در تهیه گزارش:\n{e}",
                parent=self.total_premium_window,
            )
            return

        # پاک کردن نتیجه قبلی
        self._clear(self.total_premium_result_frame)

        if not results:
            ttk.Label(
                self.total_premium_result_frame,
                text="موردی یافت نشد.",
            ).pack(pady=20)
            apply_report_window_style(self.total_premium_result_frame)
            return

        columns = (
            "total_premium",
            "policy_count",
            "customer",
            "row",
        )

        result_table = ttk.Treeview(
            self.total_premium_result_frame,
            columns=columns,
            show="headings",
        )

        result_table.heading("total_premium", text="مجموع حق‌بیمه خالص")
        result_table.heading("policy_count", text="تعداد بیمه‌نامه")
        result_table.heading("customer", text="بیمه‌گذار")
        result_table.heading("row", text="ردیف")

        result_table.column("row", width=60, anchor="center")
        result_table.column("customer", width=350, anchor="e")
        result_table.column("policy_count", width=150, anchor="center")
        result_table.column("total_premium", width=200, anchor="center")

        for index, item in enumerate(results, start=1):
            customer_name = (
                f'{item["customer_name"]} {item["customer_family"]}'
            ).strip()
            customer_display = f'{customer_name} - کد: {item["customer_code"]}'

            total_premium = round(item["total_premium"])

            result_table.insert(
                "",
                "end",
                values=(
                    f"{total_premium:,}",
                    item["policy_count"],
                    customer_display,
                    index,
                ),
            )

        scrollbar = ttk.Scrollbar(
            self.total_premium_result_frame,
            orient="vertical",
            command=result_table.yview,
        )
        result_table.configure(yscrollcommand=scrollbar.set)

        result_table.pack(side="right", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")

    def on_total_premium_date_changed(self, event=None):
        """
        اجرای گزارش بعد از کامل شدن هر تاریخ.
        فقط وقتی گزینه‌ی «بازه زمانی مشخص» انتخاب شده باشد.
        """
        if self.total_premium_option.get() != 2:
            return

        if self._read_total_premium_dates() is None:
            return

        self.show_total_premium_report()
