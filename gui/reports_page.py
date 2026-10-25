import tkinter as tk
from tkinter import messagebox
from gui.styles import COLORS
from services.permissions_service import can_access_menu
from gui.commission_reports import CommissionReports
from gui.policy_reports import PolicyReports
from gui.financial_reports import FinancialReports
from gui.customer_reports import CustomerReports
from gui.agency_performance_report import (
    AgencyPerformanceReport,
)
class ReportsPage(tk.Frame):
    """
    صفحه اصلی گزارش‌ها.
    ساختار این صفحه شبیه «اطلاعات پایه» است:
    ابتدا دسته گزارش انتخاب می‌شود و سپس گزارش‌های همان دسته
    در پنجره اصلی نمایش داده می‌شوند.
    """
    def __init__(self, parent, role=None):
        super().__init__(
            parent,
            bg=COLORS["background"],
        )
        self.role = role
        self._show_main()
    def _can_access_report(self, report):
        if not can_access_menu(self.role, report):
            messagebox.showwarning(
                "عدم دسترسی",
                "شما اجازه دسترسی به این گزارش را ندارید.",
                parent=self.winfo_toplevel(),
            )
            return False
        return True
    # ==================================================
    # Main Page
    # ==================================================
    def _show_main(self):
        self._clear()
        # سربرگ صفحه
        header = tk.Frame(
            self,
            bg=COLORS["background"],
        )
        header.pack(
            fill="x",
            pady=(0, 12),
        )
        tk.Label(
            header,
            text="گزارش‌ها",
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=("Tahoma", 18, "bold"),
            anchor="e",
        ).pack(side="right")
        tk.Label(
            header,
            text="انتخاب نوع گزارش",
            bg=COLORS["background"],
            fg=COLORS["muted_text"],
            font=("Tahoma", 10),
            anchor="e",
        ).pack(
            side="right",
            padx=(20, 0),
        )
        # محدوده کارت‌ها؛ تمام‌عرض و بدون کشیده‌شدن عمودی
        grid = tk.Frame(
            self,
            bg=COLORS["background"],
        )
        grid.pack(
            fill="x",
            padx=10,
            pady=5,
        )
        grid.grid_columnconfigure(0, weight=1)
        # فهرست گزارش‌ها
        cards = []
        if can_access_menu(self.role, "agency_performance"):
            cards.append((
                "گزارش عملکرد نمایندگی",
                "عملکرد نمایندگی در یک بازه مشخص",
                self._open_agency_performance_report,
            ))
        cards.append((
                "گزارش بیمه‌نامه",
                "گزارش بیمه‌نامه‌های در حال انقضا",
                self._show_policy_reports,
            ))
        if can_access_menu(self.role, "commission_reports"):
            cards.append((
                "گزارش کارمزد",
                "گزارش‌های مربوط به کارمزد و هزینه صدور",
                self._show_commission_reports,
            ))
        cards.append((
            "گزارش‌های مالی",
            "گزارش پرداختی‌ها و مبالغ مالی",
            self._show_financial_reports,
        ))
        cards.append((
                "گزارش بیمه‌گذاران",
                "گزارش خوش‌حسابی، تأخیر و تولید",
                self._show_customer_reports,
            ))
        # نمایش تمام گزارش‌ها در یک ستون
        for row, (title, description, command) in enumerate(cards):
            self._create_category_card(
                grid,
                row=row,
                column=0,
                title=title,
                description=description,
                command=command,
            )
      # ==================================================
    # Category Card
    # ==================================================
    def _create_category_card(
        self,
        parent,
        row,
        column,
        title,
        description,
        command,
    ):
        card = tk.Frame(
            parent,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            cursor="hand2",
        )
        card.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=8,
            pady=5,
        )
        title_label = tk.Label(
            card,
            text=title,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Tahoma", 11, "bold"),
            anchor="e",
            cursor="hand2",
        )
        title_label.pack(
            fill="x",
            padx=18,
            pady=(12, 4),
        )
        description_label = tk.Label(
            card,
            text=description,
            bg=COLORS["surface"],
            fg=COLORS["muted_text"],
            font=("Tahoma", 9),
            anchor="e",
            justify="right",
            cursor="hand2",
        )
        description_label.pack(
            fill="x",
            padx=18,
            pady=(0, 12),
        )
        # کلیک روی هر قسمت کارت، گزارش را باز می‌کند.
        for widget in (
            card,
            title_label,
            description_label,
        ):
            widget.bind(
                "<Button-1>",
                lambda event, action=command: action(),
            )
    # ==================================================
    # Category Pages
    # ==================================================
    def _show_category_header(self, title):
        header = tk.Frame(
            self,
            bg=COLORS["background"],
        )
        header.pack(
            fill="x",
            pady=(0, 20),
        )
        back_button = tk.Button(
            header,
            text="→  بازگشت به گزارش‌ها",
            command=self._show_main,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            activebackground="#E8EEF5",
            activeforeground=COLORS["primary"],
            relief="flat",
            bd=0,
            font=("Tahoma", 9),
            cursor="hand2",
            padx=12,
            pady=6,
        )
        back_button.pack(
            side="left",
        )
        tk.Label(
            header,
            text=title,
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=("Tahoma", 18, "bold"),
            anchor="e",
        ).pack(
            side="right",
        )
    def _show_category_cards(self, title, items):
        self._clear()
        self._show_category_header(title)
        grid = tk.Frame(
            self,
            bg=COLORS["background"],
        )
        grid.pack(
            fill="x",
            padx=10,
            pady=5,
        )
        grid.grid_columnconfigure(0, weight=1)
        for row, (card_title, description, command) in enumerate(items):
            self._create_category_card(
                grid,
                row=row,
                column=0,
                title=card_title,
                description=description,
                command=command,
            )
    def _show_report_buttons(
        self,
        title,
        items,
    ):
        self._clear()
        self._show_category_header(title)
        card = tk.Frame(
            self,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        card.pack(
            fill="x",
            padx=5,
            pady=5,
        )
        for item_title, command in items:
            button = tk.Button(
                card,
                text=item_title,
                command=command,
                bg=COLORS["surface"],
                fg=COLORS["text"],
                activebackground="#E8EEF5",
                activeforeground=COLORS["primary"],
                relief="flat",
                bd=0,
                font=("Tahoma", 10),
                anchor="e",
                cursor="hand2",
                padx=20,
                pady=12,
            )
            button.pack(
                fill="x",
                padx=8,
                pady=4,
            )
    # ==================================================
    # Agency
    # ==================================================
    def _show_agency_reports(self):
        self._clear()
        self._show_category_header(
            "گزارش عملکرد نمایندگی"
        )
        tk.Label(
            self,
            text="گزارش عملکرد نمایندگی در بازه مشخص",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Tahoma", 11),
            anchor="e",
            padx=20,
            pady=20,
        ).pack(
            fill="x",
            padx=5,
            pady=5,
        )
        tk.Button(
            self,
            text="باز کردن گزارش",
            command=self._open_agency_performance_report,
            bg="#CDCCCC",
            fg=COLORS["text"],
            relief="flat",
            bd=0,
            font=("Tahoma", 9),
            cursor="hand2",
            padx=14,
            pady=7,
        ).pack(
            anchor="e",
            padx=25,
            pady=10,
        )
    # ==================================================
    # Commission
    # ==================================================
    def _show_commission_reports(self):
        if not self._can_access_report("commission_reports"):
            return
        self._show_category_cards(
            "گزارش کارمزد",
            [
                (
                    "کارمزد نمایندگی در یک دوره",
                    "مشاهده خلاصه و جزئیات کارمزد نمایندگی در بازه زمانی انتخابی",
                    self._open_period_commission_report,
                ),
                (
                    "کارمزد بازاریاب در یک دوره",
                    "بررسی کارمزد بازاریاب‌ها در دوره زمانی مشخص",
                    self._open_marketer_commission_report,
                ),
                (
                    "کارمزد نمایندگی به تفکیک رشته",
                    "مشاهده کارمزد و هزینه صدور به تفکیک رشته‌های بیمه‌ای",
                    self._open_commission_by_type_report,
                ),
                (
                    "کارمزد یک بیمه‌نامه",
                    "مشاهده محاسبات کارمزد و هزینه صدور یک بیمه‌نامه مشخص",
                    self._open_policy_commission_report,
                ),
            ],
        )
    # ==================================================
    # Policy
    # ==================================================
    def _show_policy_reports(self):
        self._show_category_cards(
            "گزارش بیمه‌نامه",
            [
                (
                    "بیمه‌نامه‌های منقضی‌شونده در یک بازه",
                    "مشاهده بیمه‌نامه‌هایی که تاریخ انقضایشان در بازه زمانی انتخابی است",
                    self._open_policy_expiry_report,
                ),
                (
                    "بیمه‌نامه‌های منقضی‌شونده در ۵ روز آینده",
                    "فهرست بیمه‌نامه‌هایی که ظرف ۵ روز آینده منقضی می‌شوند",
                    self._open_upcoming_expiry_report,
                ),
            ],
        )
    # ==================================================
    # Financial
    # ==================================================
    def _show_financial_reports(self):
        self._show_category_cards(
            "گزارش‌های مالی",
            [
                (
                    "پرداختی‌ها از صندوق و پیش‌دریافتی",
                    "مشاهده پرداختی‌هایی که از صندوق یا پیش‌دریافتی انجام شده است",
                    self._open_fund_advance_report,
                ),
                (
                    "گزارش کل پرداختی‌ها",
                    "مشاهده مجموع پرداختی‌ها در بازه زمانی انتخابی",
                    self._open_total_payments_report,
                ),
            ],
        )
    # ==================================================
    # Customers
    # ==================================================
    def _show_customer_reports(self):
        self._show_category_cards(
            "گزارش بیمه‌گذاران",
            [
                (
                    "گزارش میزان خوش‌حسابی بیمه‌گذاران",
                    "بررسی وضعیت پرداخت و خوش‌حسابی بیمه‌گذاران",
                    self._open_customer_payment_behavior_report,
                ),
                (
                    "بیمه‌گذاران با میانگین تأخیر بیش از مدت معین",
                    "فهرست بیمه‌گذارانی که میانگین تأخیرشان از حد مشخص بیشتر است",
                    self._open_customer_delay_report,
                ),
                (
                    "بیمه‌گذاران بر اساس مجموع حق‌بیمه تولیدی",
                    "رتبه‌بندی بیمه‌گذاران بر اساس مجموع حق‌بیمه تولیدی",
                    self._open_customer_production_report,
                ),
            ],
        )
    # ==================================================
    # Report Actions
    # ==================================================
    def _open_agency_performance_report(self):
        if not self._can_access_report("agency_performance"):
            return
        try:
            self._clear()
            report_page = AgencyPerformanceReport(
                self
            )
            report_page.pack(
                fill="both",
                expand=True,
            )
        except Exception as e:
            messagebox.showerror(
                "خطا",
                f"خطا در باز کردن گزارش عملکرد نمایندگی:\n{e}",
                parent=self.winfo_toplevel(),
            )
    def _open_period_commission_report(self):
        try:
            report = CommissionReports(self.winfo_toplevel())
            report.withdraw()
            report.open_period_commission_report()
        except Exception as e:
            messagebox.showerror(
                "خطا",
                f"خطا در باز کردن گزارش کارمزد:\n{e}",
                parent=self.winfo_toplevel(),
            )
    def _open_marketer_commission_report(self):
        try:
            report = CommissionReports(self.winfo_toplevel())
            report.withdraw()
            report.open_marketer_commission_report()
        except Exception as e:
            messagebox.showerror(
                "خطا",
                f"خطا در باز کردن گزارش کارمزد بازاریاب:\n{e}",
                parent=self.winfo_toplevel(),
            )
    def _open_commission_by_type_report(self):
        try:
            report = CommissionReports(self.winfo_toplevel())
            report.withdraw()
            report.open_commission_by_type_report()
        except Exception as e:
            messagebox.showerror(
                "خطا",
                f"خطا در باز کردن گزارش کارمزد به تفکیک رشته:\n{e}",
                parent=self.winfo_toplevel(),
            )
    def _open_policy_commission_report(self):
        try:
            report = CommissionReports(self.winfo_toplevel())
            report.withdraw()
            report.open_policy_commission_report()
        except Exception as e:
            messagebox.showerror(
                "خطا",
                f"خطا در باز کردن گزارش کارمزد بیمه‌نامه:\n{e}",
                parent=self.winfo_toplevel(),
            )
    def _open_policy_expiry_report(self):
        try:
            report = PolicyReports(self.winfo_toplevel())
            report.withdraw()
            report.open_expiry_report()
        except Exception as e:
            messagebox.showerror(
                "خطا",
                f"خطا در باز کردن گزارش انقضا:\n{e}",
                parent=self.winfo_toplevel(),
            )
    def _open_upcoming_expiry_report(self):
        try:
            report = PolicyReports(self.winfo_toplevel())
            report.withdraw()
            report.open_upcoming_expiry_report()
        except Exception as e:
            messagebox.showerror(
                "خطا",
                f"خطا در باز کردن گزارش ۵ روز آینده:\n{e}",
                parent=self.winfo_toplevel(),
            )
    # ==================================================
    # Financial placeholders
    # ==================================================
    def _open_financial_report(self, method_name, error_title):
        try:
            from gui.financial_reports import FinancialReports
            report = FinancialReports(
                self.winfo_toplevel(),
                show_menu=False,
            )
            report.withdraw()
            getattr(report, method_name)()
        except Exception as e:
            messagebox.showerror(
                "خطا",
                f"{error_title}:\n{e}",
                parent=self.winfo_toplevel(),
            )
    def _open_fund_advance_report(self):
        self._open_financial_report(
            "open_collection_report",
            "خطا در باز کردن گزارش پرداختی‌ها",
        )
    def _open_total_payments_report(self):
        self._open_financial_report(
            "open_total_payments_report",
            "خطا در باز کردن گزارش کل پرداختی‌ها",
        )
    # ==================================================
    # Customer placeholders
    # ==================================================
    def _open_customer_report(self, method_name, error_title):
        try:
            report = CustomerReports(
                self.winfo_toplevel(),
                show_menu=False,
            )
            report.withdraw()
            getattr(report, method_name)()
        except Exception as e:
            messagebox.showerror(
                "خطا",
                f"{error_title}:\n{e}",
                parent=self.winfo_toplevel(),
            )
    def _open_customer_payment_behavior_report(self):
        self._open_customer_report(
            "open_payment_behavior_report",
            "خطا در باز کردن گزارش خوش‌حسابی",
        )
    def _open_customer_delay_report(self):
        self._open_customer_report(
            "open_average_delay_report",
            "خطا در باز کردن گزارش میانگین تأخیر",
        )
    def _open_customer_production_report(self):
        self._open_customer_report(
            "open_total_premium_report",
            "خطا در باز کردن گزارش حق‌بیمه تولیدی",
        )
    # ==================================================
    # Helpers
    # ==================================================
    def _clear(self):
        for widget in self.winfo_children():
            widget.destroy()
