import tkinter as tk
from tkinter import ttk
from services.policy_service import load_policies
from services.date_service import convert_date_to_shamsi
from services.insurance_type_service import load_root_insurance_types
from services.marketer_service import load_marketers
from gui.insurance_selector import InsuranceSelector
from gui.customer_selector import open_customer_selector
from gui.styles import COLORS, set_title_bar_color
from services.system_config_service import get_current_agent
from services.policy_filter_service import (
    filter_policies,
    format_policy_number,
)
class PolicySelector:
    BASE_TITLE = "انتخاب بیمه‌نامه"
    # ورودی‌های متنی بعد از این مدت توقف تایپ جستجو می‌کنند (میلی‌ثانیه).
    SEARCH_DELAY_MS = 400
    # حداکثر تعداد ردیف نمایش‌داده‌شده در جدول. None یعنی بدون سقف.
    # اگر با تعداد زیاد رکورد باز هم کند بود، مثلاً 1500 بگذارید.
    MAX_DISPLAY_ROWS = None
    # کلیدهایی که متن را عوض نمی‌کنند و جستجو لازم ندارند
    IGNORED_KEYS = frozenset({
        "Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next",
        "Shift_L", "Shift_R", "Control_L", "Control_R",
        "Alt_L", "Alt_R", "Tab", "Caps_Lock", "Escape",
    })
    DATE_CONDITIONS = ["برابر با", "کوچکتر از", "بزرگتر از", "مابین"]
    NUMBER_CONDITIONS = ["برابر با", "کوچکتر از", "بزرگتر از"]
    # شماره بیمه‌نامه فقط با شرط «برابر با» جستجو می‌شود
    POLICY_NUMBER_CONDITION = "برابر با"
    # مقدار «تریستیت» رادیوبوتن‌ها. پیش‌فرض Tk رشته‌ی خالی است و وقتی متغیر
    # خالی باشد هر دو دکمه پُر (انتخاب‌شده) نمایش داده می‌شوند.
    RADIO_NONE = "__none__"
    # نام فیلتر -> (کمبوی شرط، ورودی اول، ورودی دوم برای «مابین»)
    DATE_FILTERS = {
        "issue_date": (
            "issue_condition_combo",
            "issue_date_search_entry",
            "issue_date_search_entry2",
        ),
        "start_date": (
            "start_condition_combo",
            "start_date_entry",
            "start_date_entry2",
        ),
        "end_date": (
            "end_condition_combo",
            "end_date_entry",
            "end_date_entry2",
        ),
    }
    def __init__(self, parent, on_selected):
        self.parent = parent
        self.on_selected = on_selected
        self.selected_customer = None
        self.selected_insurance_type = None
        self.selected_marketer = None
        self.window = tk.Toplevel(parent)
        self.window.title(self.BASE_TITLE)
        self.window.geometry("1200x700")
        self.window.after(
            200,
            lambda: set_title_bar_color(
                self.window,
                COLORS["primary"],
            ),
        )
        self.all_policies = []
        self.marketers = []
        self.search_vars = {}
        self.search_frames = {}
        self._search_job = None
        self._row_cache = {}
        self._policies_by_id = {}
        self.current_agent = get_current_agent()
        self.window.bind("<Destroy>", self._on_window_destroy, add="+")
        self.create_widgets()
        self.load_data()
        # شروع نمایش جدول از سمت راست
        self.window.after(250, self._scroll_table_to_right)
    # ==================================================
    # جستجوی تأخیری (Debounce)
    # ==================================================
    def schedule_policy_search(self, event=None):
        """
        جستجو را به بعد از توقف تایپ موکول می‌کند تا با هر کاراکتر
        یک جستجوی کامل روی همه‌ی رکوردها اجرا نشود.
        """
        if (
            event is not None
            and getattr(event, "keysym", None) in self.IGNORED_KEYS
        ):
            return
        self._cancel_pending_search()
        self._search_job = self.window.after(
            self.SEARCH_DELAY_MS,
            self._run_scheduled_search,
        )
    def _run_scheduled_search(self):
        self._search_job = None
        self.refresh_policy_search_results()
    def _cancel_pending_search(self):
        if self._search_job is not None:
            try:
                self.window.after_cancel(self._search_job)
            except tk.TclError:
                pass
            self._search_job = None
    def _on_window_destroy(self, event):
        if event.widget is self.window:
            self._cancel_pending_search()
    # ==================================================
    # ابزارهای کمکی
    # ==================================================
    @staticmethod
    def _set_readonly_text(entry, text=""):
        entry.config(state="normal")
        entry.delete(0, tk.END)
        if text:
            entry.insert(0, text)
        entry.config(state="readonly")
    def _date_widgets(self, filter_name):
        combo_attr, entry_attr, entry2_attr = self.DATE_FILTERS[filter_name]
        return (
            getattr(self, combo_attr),
            getattr(self, entry_attr),
            getattr(self, entry2_attr),
        )
    @staticmethod
    def _customer_text(customer):
        return (
            f"{customer.name} "
            f"{customer.family or ''} "
            f"{customer.customer_code or ''}"
        ).strip()
    # ==================================================
    # ساخت فرم
    # ==================================================
    def create_widgets(self):
        tk.Label(
            self.window,
            text=self.BASE_TITLE,
            font=("Arial", 14, "bold")
        ).pack(pady=10)
        # ----------------------------------------------
        # فریم جستجو
        # ----------------------------------------------
        search_container = tk.Frame(self.window)
        search_container.pack(fill="x", padx=10, pady=5)
        criteria_frame = tk.Frame(search_container)
        criteria_frame.pack(side="right")
        criteria = [
            ("customer", "بیمه‌گذار"),
            ("policy_number", "شماره بیمه‌نامه"),
            ("insurance_type", "رشته بیمه"),
            ("issue_date", "تاریخ صدور"),
            ("start_date", "تاریخ شروع"),
            ("end_date", "تاریخ پایان"),
            ("referrer", "معرف"),
            ("marketer", "بازاریاب"),
            ("record_type", "نوع رکورد"),
            ("premium", "حق‌بیمه"),
            ("fund", "سهم صندوق"),
            ("mortgage", "وضعیت مرهوناتی"),
        ]
        builders = {
            "customer": self.create_customer_search,
            "policy_number": self._create_policy_number_search,
            "insurance_type": self.create_insurance_type_search,
            "issue_date": lambda f: self._create_date_search(f, "issue_date"),
            "start_date": lambda f: self._create_date_search(f, "start_date"),
            "end_date": lambda f: self._create_date_search(f, "end_date"),
            "referrer": self._create_referrer_search,
            "marketer": self._create_marketer_search,
            "record_type": self._create_record_type_search,
            "premium": self._create_premium_search,
            "fund": self._create_fund_search,
            "mortgage": self._create_mortgage_search,
        }
        for row, (name, text) in enumerate(criteria):
            variable = tk.BooleanVar(master=self.window, value=False)
            self.search_vars[name] = variable
            field_frame = tk.Frame(criteria_frame)
            self.search_frames[name] = field_frame
            builders[name](field_frame)
            # چک باکس فعال‌سازی فیلتر
            tk.Checkbutton(
                criteria_frame,
                variable=variable,
                command=lambda n=name: self.toggle_search_field(n)
            ).grid(row=row, column=1, padx=5, pady=4, sticky="e")
            # عنوان
            tk.Label(
                criteria_frame,
                text=text
            ).grid(row=row, column=2, padx=5, pady=4, sticky="e")
            # فریم فیلتر
            field_frame.grid(row=row, column=0, padx=10, pady=4)
            field_frame.grid_remove()
        # ----------------------------------------------
        # دکمه حذف همه فیلتر ها و انتخاب
        # ----------------------------------------------
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=5)
        tk.Button(
            button_frame,
            text="حذف همه فیلترها",
            width=20,
            background="#CDCCCC",
            command=self.clear_search_filters
        ).pack(side="right", padx=5)
        tk.Button(
            button_frame,
            text="انتخاب بیمه‌نامه",
            width=20,
            background="#CDCCCC",
            command=self.select_policy
        ).pack(side="right", padx=5)
        # ==================================================
        # جدول
        # ==================================================
        table_frame = tk.Frame(self.window)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        columns = (
            "mortgage",
            "premium",
            "marketer",
            "referrer",
            "end_date",
            "start_date",
            "issue_date",
            "insurance_type",
            "endorsement_number",
            "policy_number",
            "policy_type",
            "customer",
            "id"
        )
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )
        headings = {
            "mortgage": "مرهوناتی",
            "premium": "حق‌بیمه",
            "marketer": "بازاریاب",
            "referrer": "معرف",
            "end_date": "تاریخ پایان",
            "start_date": "تاریخ شروع",
            "issue_date": "تاریخ صدور",
            "insurance_type": "رشته بیمه",
            "endorsement_number": "ش الحاقیه",
            "policy_number": "ش بیمه",
            "policy_type": "نوع",
            "customer": "بیمه‌گذار",
            "id": "شناسه"
        }
        widths = {
            "mortgage": 70,
            "premium": 110,
            "marketer": 100,
            "referrer": 150,
            "end_date": 100,
            "start_date": 100,
            "issue_date": 100,
            "insurance_type": 200,
            "endorsement_number": 80,
            "policy_number": 80,
            "policy_type": 80,
            "customer": 220,
            "id": 60
        }
        for column in columns:
            self.tree.heading(column, text=headings[column], anchor="e")
            self.tree.column(column, width=widths[column], anchor="e")
        # مخفی کردن شناسه
        self.tree.column("id", width=0, minwidth=0, stretch=False)
        self.tree.heading("id", text="")
        # رنگ‌بندی
        self.tree.tag_configure("even", background="#E0E0E0")
        self.tree.tag_configure("odd", background="#FFFFFF")
        self.tree.tag_configure(
            "endorsement_even",
            background="#E0E0E0",
            foreground="#C91F28"
        )
        self.tree.tag_configure(
            "endorsement_odd",
            background="#FFFFFF",
            foreground="#C91F28"
        )
        # اسکرول عمودی و افقی جدول
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        vertical_scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        horizontal_scrollbar = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.tree.xview
        )
        self.tree.configure(
            yscrollcommand=vertical_scrollbar.set,
            xscrollcommand=horizontal_scrollbar.set
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        horizontal_scrollbar.grid(row=1, column=0, sticky="ew")
        # انتخاب با دابل کلیک
        self.tree.bind("<Double-1>", self.select_policy)
        # ==================================================
        # فریم دکمه پایین پنجره
        # ==================================================
        bottom_frame = tk.Frame(self.window)
        bottom_frame.pack(fill="x", pady=8)
        tk.Button(
            bottom_frame,
            text="انتخاب بیمه‌نامه",
            width=20,
            background="#CDCCCC",
            command=self.select_policy
        ).pack(side="right", padx=10)
    def _scroll_table_to_right(self):
        try:
            self.tree.xview_moveto(1.0)
        except tk.TclError:
            # پنجره قبل از اجرای این تابع بسته شده
            pass
    # ==================================================
    # سازنده‌ی هر فیلتر
    # ==================================================
    def _create_policy_number_search(self, frame):
        self.policy_number_entry = tk.Entry(frame, width=25)
        self.policy_number_entry.bind(
            "<KeyRelease>",
            self.schedule_policy_search
        )
        self.policy_number_entry.pack(side="right", padx=5)
    def _create_date_search(self, frame, filter_name):
        combo_attr, entry_attr, entry2_attr = self.DATE_FILTERS[filter_name]
        combo = ttk.Combobox(
            frame,
            width=15,
            values=self.DATE_CONDITIONS,
            state="readonly"
        )
        combo.current(0)
        combo.bind(
            "<<ComboboxSelected>>",
            lambda event, n=filter_name: self.change_date_condition(n)
        )
        combo.pack(side="right", padx=5)
        entry = tk.Entry(frame, width=15)
        entry.bind("<KeyRelease>", self.schedule_policy_search)
        entry.pack(side="right", padx=5)
        # ورودی دوم فقط برای شرط «مابین» نمایش داده می‌شود
        entry2 = tk.Entry(frame, width=15)
        entry2.bind("<KeyRelease>", self.schedule_policy_search)
        entry2.pack(side="right", padx=5)
        entry2.pack_forget()
        setattr(self, combo_attr, combo)
        setattr(self, entry_attr, entry)
        setattr(self, entry2_attr, entry2)
    def _create_referrer_search(self, frame):
        self.referrer_condition_combo = ttk.Combobox(
            frame,
            width=15,
            values=["معرف دارد", "بدون معرف", "برابر با", "شامل"],
            state="readonly"
        )
        self.referrer_condition_combo.current(0)
        self.referrer_condition_combo.bind(
            "<<ComboboxSelected>>",
            self.change_referrer_entry
        )
        self.referrer_condition_combo.pack(side="right", padx=5)
        self.referrer_entry = tk.Entry(frame, width=25, state="readonly")
        self.referrer_entry.bind("<KeyRelease>", self.schedule_policy_search)
        self.referrer_entry.pack(side="right", padx=5)
    def _create_marketer_search(self, frame):
        self.marketer_condition_combo = ttk.Combobox(
            frame,
            width=15,
            values=["بازاریاب دارد", "بدون بازاریاب", "برابر با"],
            state="readonly"
        )
        self.marketer_condition_combo.current(0)
        self.marketer_condition_combo.bind(
            "<<ComboboxSelected>>",
            self.change_marketer_combo
        )
        self.marketer_condition_combo.pack(side="right", padx=5)
        self.marketer_combo = ttk.Combobox(
            frame,
            width=25,
            state="disabled"
        )
        self.marketer_combo.bind(
            "<<ComboboxSelected>>",
            self.select_marketer
        )
        self.marketer_combo.pack(side="right", padx=5)
        # فهرست بازاریاب‌ها فقط یک بار از دیتابیس خوانده می‌شود
        self.marketers = load_marketers()
        self.marketer_combo["values"] = [
            marketer.name for marketer in self.marketers
        ]
    def _create_record_type_search(self, frame):
        self.record_type_search_var = tk.StringVar(
            master=self.window,
            value="بیمه‌نامه"
        )
        tk.Radiobutton(
            frame,
            tristatevalue=self.RADIO_NONE,
            text="بیمه‌نامه",
            variable=self.record_type_search_var,
            value="بیمه‌نامه",
            command=self.refresh_policy_search_results
        ).pack(side="right")
        tk.Radiobutton(
            frame,
            tristatevalue=self.RADIO_NONE,
            text="الحاقیه",
            variable=self.record_type_search_var,
            value="الحاقیه",
            command=self.refresh_policy_search_results
        ).pack(side="right", padx=5)
    def _create_premium_search(self, frame):
        self.premium_condition_combo = ttk.Combobox(
            frame,
            width=15,
            values=self.NUMBER_CONDITIONS,
            state="readonly"
        )
        self.premium_condition_combo.current(0)
        self.premium_condition_combo.bind(
            "<<ComboboxSelected>>",
            self.refresh_policy_search_results
        )
        self.premium_condition_combo.pack(side="right", padx=5)
        self.premium_entry = tk.Entry(frame, width=25)
        self.premium_entry.bind("<KeyRelease>", self.format_premium)
        self.premium_entry.pack(side="right", padx=5)
    def _create_fund_search(self, frame):
        self.fund_condition_combo = ttk.Combobox(
            frame,
            width=15,
            values=self.NUMBER_CONDITIONS,
            state="readonly"
        )
        self.fund_condition_combo.current(0)
        self.fund_condition_combo.bind(
            "<<ComboboxSelected>>",
            self.refresh_policy_search_results
        )
        self.fund_condition_combo.pack(side="right", padx=5)
        self.fund_search_entry = tk.Entry(frame, width=25)
        self.fund_search_entry.bind(
            "<KeyRelease>",
            self.schedule_policy_search
        )
        self.fund_search_entry.pack(side="right", padx=5)
    def _create_mortgage_search(self, frame):
        self.mortgage_search_var = tk.StringVar(
            master=self.window,
            value="غیر مرهوناتی"
        )
        tk.Radiobutton(
            frame,
            tristatevalue=self.RADIO_NONE,
            text="غیر مرهوناتی",
            variable=self.mortgage_search_var,
            value="غیر مرهوناتی",
            command=self.refresh_policy_search_results
        ).pack(side="right")
        tk.Radiobutton(
            frame,
            tristatevalue=self.RADIO_NONE,
            text="مرهوناتی",
            variable=self.mortgage_search_var,
            value="مرهوناتی",
            command=self.refresh_policy_search_results
        ).pack(side="right", padx=5)
    # ==================================================
    # بارگذاری
    # ==================================================
    def load_data(self):
        self._row_cache.clear()
        self.all_policies = load_policies()
        self._policies_by_id = {
            policy.id: policy for policy in self.all_policies
        }
        self.show_policies(self.all_policies)
    # ==================================================
    # نمایش Policy ها
    # ==================================================
    @staticmethod
    def _shamsi(value):
        return convert_date_to_shamsi(value) if value else "-----"
    def _build_row_values(self, policy):
        """مقادیر نمایشی هر ردیف فقط یک بار محاسبه و cache می‌شود."""
        cached = self._row_cache.get(policy.id)
        if cached is not None:
            return cached
        mortgage = "✓" if policy.is_mortgage else "-"
        referrer = policy.referrer
        if referrer == self.current_agent:
            referrer = ""
        customer_text = "------"
        if policy.customer:
            customer_text = self._customer_text(policy.customer)
        insurance_type_text = "------"
        if policy.insurance_type:
            insurance_type_text = policy.insurance_type.display_name.strip()
        values = (
            mortgage,
            f"{policy.premium or 0:,}",
            policy.marketer.name.strip() if policy.marketer else "-----",
            referrer if referrer else "------",
            self._shamsi(policy.end_date),
            self._shamsi(policy.start_date),
            self._shamsi(policy.issue_date),
            insurance_type_text,
            policy.endorsement_number,
            format_policy_number(policy.policy_number),
            "بیمه‌نامه" if policy.endorsement_number == 0 else "الحاقیه",
            customer_text,
            policy.id,
        )
        self._row_cache[policy.id] = values
        return values
    def show_policies(self, policies):
        self.tree.delete(*self.tree.get_children())
        # بیمه‌نامه‌های بدون تاریخ صدور اول می‌آیند. مقایسه‌ی مستقیم
        # None/"" با تاریخ در پایتون خطا می‌دهد، پس جدا مرتب می‌شوند.
        undated = [p for p in policies if not p.issue_date]
        dated = sorted(
            (p for p in policies if p.issue_date),
            key=lambda policy: policy.issue_date
        )
        policies = undated + dated
        total = len(policies)
        title = self.BASE_TITLE
        if self.MAX_DISPLAY_ROWS and total > self.MAX_DISPLAY_ROWS:
            policies = policies[:self.MAX_DISPLAY_ROWS]
            title = (
                f"{self.BASE_TITLE} — نمایش {self.MAX_DISPLAY_ROWS} "
                f"از {total} مورد، فیلتر را دقیق‌تر کنید"
            )
        self.window.title(title)
        for index, policy in enumerate(policies):
            even = index % 2 == 0
            if policy.endorsement_number != 0:
                tag = "endorsement_even" if even else "endorsement_odd"
            else:
                tag = "even" if even else "odd"
            self.tree.insert(
                "",
                "end",
                values=self._build_row_values(policy),
                tags=(tag,)
            )
    # ==================================================
    # جستجو
    # ==================================================
    def search_policy(self):
        customer_ids = None
        if self.search_vars["customer"].get():
            if self.selected_customer:
                customer_ids = [self.selected_customer.id]
        policy_number = ""
        if self.search_vars["policy_number"].get():
            policy_number = self.policy_number_entry.get().strip()
        insurance_type_id = None
        if self.search_vars["insurance_type"].get():
            if self.selected_insurance_type:
                insurance_type_id = self.selected_insurance_type.id
        date_filters = {}
        for name in self.DATE_FILTERS:
            date_filters[name] = None
            if self.search_vars[name].get():
                combo, entry, entry2 = self._date_widgets(name)
                date_filters[name] = (combo.get(), entry.get(), entry2.get())
        referrer_condition = None
        referrer = ""
        if self.search_vars["referrer"].get():
            referrer_condition = self.referrer_condition_combo.get()
            referrer = self.referrer_entry.get().strip()
        marketer_condition = None
        marketer_id = None
        if self.search_vars["marketer"].get():
            marketer_condition = self.marketer_condition_combo.get()
            if self.selected_marketer:
                marketer_id = self.selected_marketer.id
        record_type = None
        if self.search_vars["record_type"].get():
            record_type = self.record_type_search_var.get()
        premium = None
        premium_condition = "برابر با"
        if self.search_vars["premium"].get():
            premium_text = (
                self.premium_entry.get().replace(",", "").strip()
            )
            premium_condition = self.premium_condition_combo.get()
            if premium_text:
                try:
                    premium = int(premium_text)
                except ValueError:
                    premium = None
        fund = None
        fund_condition = "برابر با"
        if self.search_vars["fund"].get():
            fund_text = (
                self.fund_search_entry.get().replace(",", "").strip()
            )
            fund_condition = self.fund_condition_combo.get()
            if fund_text:
                try:
                    fund = int(fund_text)
                except ValueError:
                    fund = None
        mortgage = None
        if self.search_vars["mortgage"].get():
            mortgage = self.mortgage_search_var.get()
        filtered_policies = filter_policies(
            self.all_policies,
            customer_ids=customer_ids,
            policy_number=policy_number,
            policy_number_condition=self.POLICY_NUMBER_CONDITION,
            insurance_type_id=insurance_type_id,
            issue_date=date_filters["issue_date"],
            start_date=date_filters["start_date"],
            end_date=date_filters["end_date"],
            referrer_condition=referrer_condition,
            referrer=referrer,
            marketer_condition=marketer_condition,
            marketer_id=marketer_id,
            record_type=record_type,
            premium=premium,
            premium_condition=premium_condition,
            fund=fund,
            fund_condition=fund_condition,
            mortgage=mortgage,
            current_agent=self.current_agent,
        )
        self.show_policies(filtered_policies)
    # ==================================================
    # بیمه‌گذار
    # ==================================================
    def create_customer_search(self, frame):
        tk.Label(
            frame,
            text=": بیمه‌گذار",
            anchor="e"
        ).pack(side="right", padx=5)
        self.customer_search_entry = tk.Entry(
            frame,
            width=25,
            state="readonly"
        )
        self.customer_search_entry.pack(side="right", padx=5)
        tk.Button(
            frame,
            text="انتخاب",
            background="#CDCCCC",
            command=self.customer_selector
        ).pack(side="right", padx=5)
        tk.Button(
            frame,
            text="پاک کردن",
            background="#CDCCCC",
            command=self.clear_customer
        ).pack(side="right", padx=5)
    def customer_selector(self):
        open_customer_selector(
            self.window,
            self.customer_selected
        )
    def customer_selected(self, customer):
        self.selected_customer = customer
        self._set_readonly_text(
            self.customer_search_entry,
            self._customer_text(customer)
        )
        self.refresh_policy_search_results()
    def clear_customer(self):
        self.selected_customer = None
        self._set_readonly_text(self.customer_search_entry)
        self.refresh_policy_search_results()
    # ==================================================
    # رشته بیمه
    # ==================================================
    def create_insurance_type_search(self, frame):
        tk.Label(
            frame,
            text=": نوع بیمه",
            anchor="e"
        ).pack(side="right", padx=5)
        self.insurance_type_search_entry = tk.Entry(
            frame,
            width=25,
            state="readonly"
        )
        self.insurance_type_search_entry.pack(side="right", padx=5)
        tk.Button(
            frame,
            text="انتخاب",
            background="#CDCCCC",
            command=self.open_insurance_selector
        ).pack(side="right", padx=5)
        tk.Button(
            frame,
            text="پاک کردن",
            background="#CDCCCC",
            command=self.clear_insurance_type
        ).pack(side="right", padx=5)
    def open_insurance_selector(self):
        root_types = load_root_insurance_types()
        InsuranceSelector(
            self.window,
            root_types,
            self.insurance_selected
        )
    def insurance_selected(self, selected_path):
        if not selected_path:
            return
        self.selected_insurance_type = selected_path[-1]
        self._set_readonly_text(
            self.insurance_type_search_entry,
            self.selected_insurance_type.display_name
        )
        self.refresh_policy_search_results()
    def clear_insurance_type(self):
        self.selected_insurance_type = None
        self._set_readonly_text(self.insurance_type_search_entry)
        self.refresh_policy_search_results()
    # ==================================================
    # تغییر فیلترها
    # ==================================================
    def _filter_has_value(self, name):
        """آیا فیلتر فعال‌شده الان مقدار یا شرطی دارد که جستجو را عوض کند؟"""
        if name == "customer":
            return bool(self.selected_customer)
        if name == "policy_number":
            return bool(self.policy_number_entry.get().strip())
        if name == "insurance_type":
            return bool(self.selected_insurance_type)
        if name in self.DATE_FILTERS:
            _, entry, _ = self._date_widgets(name)
            return bool(entry.get().strip())
        if name == "referrer":
            # «معرف دارد» و «بدون معرف» مقدار متنی نمی‌خواهند
            if self.referrer_condition_combo.get() in (
                "معرف دارد",
                "بدون معرف"
            ):
                return True
            return bool(self.referrer_entry.get().strip())
        if name == "marketer":
            # «بازاریاب دارد» و «بدون بازاریاب» انتخاب بازاریاب نمی‌خواهند
            if self.marketer_condition_combo.get() in (
                "بازاریاب دارد",
                "بدون بازاریاب"
            ):
                return True
            return bool(self.selected_marketer)
        if name == "record_type":
            return bool(self.record_type_search_var.get().strip())
        if name == "premium":
            return bool(self.premium_entry.get().strip())
        if name == "fund":
            return bool(self.fund_search_entry.get().strip())
        if name == "mortgage":
            return bool(self.mortgage_search_var.get().strip())
        return False
    def toggle_search_field(self, name):
        frame = self.search_frames[name]
        variable = self.search_vars[name]
        if variable.get():
            frame.grid()
        else:
            frame.grid_remove()
        self._cancel_pending_search()
        # اگر فیلتر خاموش شد، نتیجه جستجو باید به‌روز شود
        if not variable.get():
            self.search_policy()
            return
        if self._filter_has_value(name):
            self.search_policy()
    def change_date_condition(self, filter_name):
        combo, _, entry2 = self._date_widgets(filter_name)
        if combo.get() == "مابین":
            entry2.pack(side="right", padx=5)
        else:
            entry2.delete(0, tk.END)
            entry2.pack_forget()
        self.refresh_policy_search_results()
    # ==================================================
    # معرف
    # ==================================================
    def change_referrer_entry(self, event=None):
        condition = self.referrer_condition_combo.get()
        if condition in ("معرف دارد", "بدون معرف"):
            self._set_readonly_text(self.referrer_entry)
        else:
            self.referrer_entry.config(state="normal")
        self.refresh_policy_search_results()
    # ==================================================
    # بازاریاب
    # ==================================================
    def change_marketer_combo(self, event=None):
        condition = self.marketer_condition_combo.get()
        if condition in ("بازاریاب دارد", "بدون بازاریاب"):
            self.marketer_combo.set("")
            self.marketer_combo.config(state="disabled")
            self.selected_marketer = None
        else:
            # readonly: فقط از فهرست قابل انتخاب باشد، نه تایپ آزاد
            self.marketer_combo.config(state="readonly")
        self.refresh_policy_search_results()
    def select_marketer(self, event=None):
        marketer_name = self.marketer_combo.get()
        self.selected_marketer = next(
            (
                marketer
                for marketer in self.marketers
                if marketer.name == marketer_name
            ),
            None
        )
        self.refresh_policy_search_results()
    # ==================================================
    # حق بیمه
    # ==================================================
    def format_premium(self, event=None):
        if (
            event is not None
            and getattr(event, "keysym", None) in self.IGNORED_KEYS
        ):
            return
        raw = self.premium_entry.get()
        cursor_position = self.premium_entry.index(tk.INSERT)
        digits_before_cursor = sum(
            1 for char in raw[:cursor_position] if char.isdigit()
        )
        # هر کاراکتر غیر عددی حذف می‌شود
        digits = "".join(char for char in raw if char.isdigit())
        formatted = f"{int(digits):,}" if digits else ""
        if formatted != raw:
            self.premium_entry.delete(0, tk.END)
            self.premium_entry.insert(0, formatted)
            # مکان‌نما بعد از همان تعداد رقم قبلی بماند
            if digits_before_cursor == 0:
                new_cursor_position = 0
            else:
                new_cursor_position = len(formatted)
                counted = 0
                for index, char in enumerate(formatted):
                    if char.isdigit():
                        counted += 1
                        if counted == digits_before_cursor:
                            new_cursor_position = index + 1
                            break
            self.premium_entry.icursor(new_cursor_position)
        self.schedule_policy_search()
    # ==================================================
    # حذف همه فیلترها
    # ==================================================
    def clear_search_filters(self):
        self._cancel_pending_search()
        # مشتری
        self.selected_customer = None
        self._set_readonly_text(self.customer_search_entry)
        # رشته
        self.selected_insurance_type = None
        self._set_readonly_text(self.insurance_type_search_entry)
        # شماره
        self.policy_number_entry.delete(0, tk.END)
        # تاریخ‌ها
        for name in self.DATE_FILTERS:
            combo, entry, entry2 = self._date_widgets(name)
            entry.delete(0, tk.END)
            entry2.delete(0, tk.END)
            combo.current(0)
            entry2.pack_forget()
        # معرف
        self.referrer_condition_combo.current(0)
        self._set_readonly_text(self.referrer_entry)
        # بازاریاب
        self.selected_marketer = None
        self.marketer_condition_combo.current(0)
        self.marketer_combo.set("")
        self.marketer_combo.config(state="disabled")
        # حق بیمه
        self.premium_entry.delete(0, tk.END)
        self.premium_condition_combo.current(0)
        # صندوق
        self.fund_search_entry.delete(0, tk.END)
        self.fund_condition_combo.current(0)
        # مرهون
        self.mortgage_search_var.set("غیر مرهوناتی")
        # نوع رکورد
        self.record_type_search_var.set("بیمه‌نامه")
        # حذف تیک‌ها و مخفی کردن فیلترها
        for variable in self.search_vars.values():
            variable.set(False)
        for frame in self.search_frames.values():
            frame.grid_remove()
        # نمایش همه
        self.show_policies(self.all_policies)
    # ==================================================
    # به‌روزرسانی لحظه‌ای
    # ==================================================
    def refresh_policy_search_results(self, event=None):
        # اگر جستجوی تأخیری در انتظار بود، دیگر لازم نیست
        self._cancel_pending_search()
        # تاریخ باید یا خالی باشد یا کامل (YYYY/MM/DD)
        for name in self.DATE_FILTERS:
            if not self.search_vars[name].get():
                continue
            _, entry, entry2 = self._date_widgets(name)
            for date_entry in (entry, entry2):
                if len(date_entry.get().strip()) not in (0, 10):
                    return
        self.search_policy()
    # ==================================================
    # انتخاب Policy
    # ==================================================
    def select_policy(self, event=None):
        selection = self.tree.selection()
        if not selection:
            return
        values = self.tree.item(selection[0], "values")
        policy_id = int(values[-1])
        selected_policy = self._policies_by_id.get(policy_id)
        if not selected_policy:
            return
        self.on_selected(selected_policy)
        self.window.destroy()
# ==================================================
# تابع باز کردن Selector
# ==================================================
def open_policy_selector(parent, on_selected):
    form = PolicySelector(parent, on_selected)
    form.window.wait_window()
