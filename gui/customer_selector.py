import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from gui.styles import COLORS, set_title_bar_color
from services.customer_service import (
    get_customer_by_id,
    load_customers
)
from services.text_service import normalize_persian_search_text
class CustomerSelector:
    def __init__(
        self,
        parent,
        on_selected=None,
        multi_select=False
    ):
        self.window = tk.Toplevel(parent)
        self.window.title(
            "جستجوی بیمه گذار"
        )
        self.window.geometry(
            "600x700" if multi_select else "600x600"
        )
        self.window.after(
            200,
            lambda: set_title_bar_color(
                self.window,
                COLORS["primary"],
            ),
        )
        self.customer_selected = None
        self.multi_select = multi_select
        if self.multi_select:
            self.selected_customers = []
        self.on_selected = on_selected
        self.create_widgets()
    def create_widgets(self):
        tk.Label(
            self.window,
            text=":جستجو بر اساس",
            font=("Arial", 12, "bold")
        ).pack(
            pady=10,
            padx=10,
            anchor="e"
        )
        # ==========================================
        # فریم اصلی معیارهای جستجو
        # ==========================================
        container = tk.Frame(
            self.window
        )
        container.pack(
            anchor="e",
            padx=20,
            pady=(10,2)
        )
        criteria_frame = tk.Frame(
            container
        )
        criteria_frame.pack()
        criteria = [
            ("name", "نام"),
            ("family", "نام خانوادگی"),
            ("national_id", "کد /شناسه ملی"),
            ("customer_code", "کد بیمه گذار"),
            ("is_active", "فقط بیمه گذار فعال")
        ]
        self.customer_vars = {}
        self.customer_frames = {}
        tk.Label(
            criteria_frame,
            text="نوع شرط                           مورد جستجو            "
        ).grid(
            row=0,
            column=0,
            padx=5,
            pady=4,
            sticky="e"
        )
        for row, (name, text) in enumerate(criteria):
            variable = tk.BooleanVar(
                master=self.window,
                value=False
            )
            self.customer_vars[name] = variable
            # فریم فیلد جستجوی هر معیار
            field_frame = tk.Frame(
                criteria_frame
            )
            self.customer_frames[name] = field_frame
            if name == "name":
                self.name_condition_combo = ttk.Combobox(
                    field_frame,
                    width=15,
                    values=[
                        "برابر با",
                        "شامل"
                    ],
                    state="readonly"
                )
                self.name_condition_combo.current(1)
                self.name_condition_combo.pack(
                    side="right",
                    padx=5
                )
                self.name_condition_combo.bind(
                    "<<ComboboxSelected>>",
                    self.search_customer
                )
                self.customer_name_entry = tk.Entry(
                    field_frame,
                    width=25
                )
                self.customer_name_entry.pack(
                    side="right",
                    padx=5
                )
                self.customer_name_entry.bind(
                    "<KeyRelease>",
                    self.search_customer
                )
            if name == "family":
                self.family_condition_combo = ttk.Combobox(
                    field_frame,
                    width=15,
                    values=[
                        "برابر با",
                        "شامل"
                    ],
                    state="readonly"
                )
                self.family_condition_combo.current(1)
                self.family_condition_combo.pack(
                    side="right",
                    padx=5
                )
                self.family_condition_combo.bind(
                    "<<ComboboxSelected>>",
                    self.search_customer
                )
                self.customer_family_entry = tk.Entry(
                    field_frame,
                    width=25
                )
                self.customer_family_entry.pack(
                    side="right",
                    padx=5
                )
                self.customer_family_entry.bind(
                    "<KeyRelease>",
                    self.search_customer
                )
            if name == "national_id":
                self.national_condition_combo = ttk.Combobox(
                    field_frame,
                    width=15,
                    values=[
                        "برابر با"
                    ],
                    state="readonly"
                )
                self.national_condition_combo.current(0)
                self.national_condition_combo.pack(
                    side="right",
                    padx=5
                )
                self.national_condition_combo.bind(
                    "<<ComboboxSelected>>",
                    self.search_customer
                )
                self.national_id_entry = tk.Entry(
                    field_frame,
                    width=25
                )
                self.national_id_entry.pack(
                    side="right",
                    padx=5
                )
                self.national_id_entry.bind(
                    "<KeyRelease>",
                    self.search_customer
                )
            if name == "customer_code":
                self.code_condition_combo = ttk.Combobox(
                    field_frame,
                    width=15,
                    values=[
                        "برابر با"
                    ],
                    state="readonly"
                )
                self.code_condition_combo.current(0)
                self.code_condition_combo.pack(
                    side="right",
                    padx=5
                )
                self.code_condition_combo.bind(
                    "<<ComboboxSelected>>",
                    self.search_customer
                )
                self.code_id_entry = tk.Entry(
                    field_frame,
                    width=25
                )
                self.code_id_entry.pack(
                    side="right",
                    padx=5
                )
                self.code_id_entry.bind(
                    "<KeyRelease>",
                    self.search_customer
                )
            # چک‌باکس
            tk.Checkbutton(
                criteria_frame,
                variable=variable,
                command=lambda n=name:
                    self.toggle_customer_field(n)
            ).grid(
                row=row + 1,
                column=1,
                padx=5,
                pady=4,
                sticky="e"
            )
            # عنوان
            tk.Label(
                criteria_frame,
                text=text
            ).grid(
                row=row + 1,
                column=2,
                padx=5,
                pady=4,
                sticky="e"
            )
            # فریم جستجو
            field_frame.grid(
                row=row + 1,
                column=0,
                padx=10,
                pady=4
            )
            # فعلاً مخفی
            field_frame.grid_remove()
        # ==========================================
        # فریم نتایج جستجو
        # ==========================================
        tree_frame = tk.Frame(
            self.window
        )
        tree_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=0,
        )
        self.customer_tree = ttk.Treeview(
            tree_frame,
            columns=(
                "national_id",
                "family",
                "name",
                "customer_code",
                "id"
            ),
            show="headings",
            selectmode=(
                "extended"
                if self.multi_select
                else "browse"
            )
        )
        self.customer_tree.heading(
            "national_id",
            text="کد ملی"
        )
        self.customer_tree.heading(
            "family",
            text="نام خانوادگی"
        )
        self.customer_tree.heading(
            "name",
            text="نام"
        )
        self.customer_tree.heading(
            "customer_code",
            text="کد بیمه گذار"
        )
        self.customer_tree.heading(
            "id",
            text="شناسه"
        )
        self.customer_tree.column(
            "national_id",
            width=50,
            anchor="e"
        )
        self.customer_tree.column(
            "family",
            width=100,
            anchor="e"
        )
        self.customer_tree.column(
            "name",
            width=200,
            anchor="e"
        )
        self.customer_tree.column(
            "customer_code",
            width=60,
            anchor="e"
        )
        self.customer_tree.column(
            "id",
            width=30,
            anchor="e"
        )
        # اسکرول عمودی
        tree_scrollbar = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.customer_tree.yview
        )
        self.customer_tree.configure(
            yscrollcommand=tree_scrollbar.set
        )
        self.customer_tree.pack(
            side="right",
            fill="x",
            expand=True
        )
        self.customer_tree.configure(
            height=8
        )
        tree_scrollbar.pack(
            side="left",
            fill="y"
        )
        # ==========================================
        # حالت چند انتخابی
        # ==========================================
        if self.multi_select:
            # -----------------------------
            # دکمه افزودن به انتخاب‌ها
            # -----------------------------
            tk.Button(
                self.window,
                text="افزودن به انتخاب‌ها",
                width=20,
                command=self.add_selected_customers,
                background="#CDCCCC"
            ).pack(
                pady=(1, 1)
            )
            # -----------------------------
            # عنوان انتخاب‌های فعلی
            # -----------------------------
            tk.Label(
                self.window,
                text=":بیمه‌گذاران انتخاب شده",
                font=("Arial", 10, "bold")
            ).pack(
                pady=(1, 1),
                anchor="e",
                padx=20
            )
            # -----------------------------
            # لیست انتخاب‌ها
            # -----------------------------
            selected_frame = tk.Frame(self.window)
            selected_frame.pack(
                fill="x",
                padx=20,
                pady=(1, 1)
            )
            self.selected_customers_listbox = tk.Listbox(
                selected_frame,
                height=4,
                justify="right"
            )
            self.selected_customers_listbox.pack(
                side="left",
                fill="both",
                expand=True
            )
            selected_scrollbar = tk.Scrollbar(
                selected_frame,
                orient="vertical",
                command=self.selected_customers_listbox.yview
            )
            selected_scrollbar.pack(
                side="right",
                fill="y"
            )
            self.selected_customers_listbox.configure(
                yscrollcommand=selected_scrollbar.set
            )
            # -----------------------------
            # دکمه نهایی
            # -----------------------------
            tk.Button(
                self.window,
                text="انتخاب بیمه‌گذاران",
                width=20,
                command=self.confirm_selected_customers,
                background="#CDCCCC"
            ).pack(
                pady=(5, 20)
            )
        else:
            tk.Button(
                self.window,
                text="انتخاب بیمه گذار",
                width=20,
                command=self.select_customer,
                background="#CDCCCC"
            ).pack(
                pady=5
            )
    def search_customer(self, event=None):
        # فقط نتایج جستجو پاک می‌شوند
        # انتخاب‌های قبلی دست نخورده باقی می‌مانند
        for item in self.customer_tree.get_children():
            self.customer_tree.delete(
                item
            )
        customers = load_customers()
        filtered_customers = customers
        # ==========================================
        # نام
        # ==========================================
        if self.customer_vars["name"].get():
            name = normalize_persian_search_text(
                self.customer_name_entry.get()
            )
            condition = (
                self.name_condition_combo.get()
            )
            if name != "":
                if condition == "شامل":
                    filtered_customers = [
                        customer
                        for customer in filtered_customers
                        if name in normalize_persian_search_text(
                            customer.name
                        )
                    ]
                elif condition == "برابر با":
                    filtered_customers = [
                        customer
                        for customer in filtered_customers
                        if name == normalize_persian_search_text(
                            customer.name
                        )
                    ]
        # ==========================================
        # نام خانوادگی
        # ==========================================
        if self.customer_vars["family"].get():
            family = normalize_persian_search_text(
                self.customer_family_entry.get()
            )
            condition = self.family_condition_combo.get()
            if family != "":
                if condition == "شامل":
                    filtered_customers = [
                        customer
                        for customer in filtered_customers
                        if family in normalize_persian_search_text(
                            customer.family
                        )
                    ]
                elif condition == "برابر با":
                    filtered_customers = [
                        customer
                        for customer in filtered_customers
                        if family == normalize_persian_search_text(
                            customer.family
                        )
                    ]
        # ==========================================
        # کد ملی
        # ==========================================
        if self.customer_vars["national_id"].get():
            national_id = (
                self.national_id_entry.get()
            )
            condition = (
                self.national_condition_combo.get()
            )
            if national_id != "":
                if condition == "برابر با":
                    filtered_customers = [
                        customer
                        for customer in filtered_customers
                        if national_id == (
                            customer.national_id or ""
                        )
                    ]
        # ==========================================
        # کد بیمه گذار
        # ==========================================
        if self.customer_vars["customer_code"].get():
            customer_code = (
                self.code_id_entry.get()
            )
            condition = (
                self.code_condition_combo.get()
            )
            if customer_code != "":
                if condition == "برابر با":
                    filtered_customers = [
                        customer
                        for customer in filtered_customers
                        if customer_code == (
                            customer.customer_code or ""
                        )
                    ]
        # ==========================================
        # فقط فعال‌ها
        # ==========================================
        if self.customer_vars["is_active"].get():
            filtered_customers = [
                customer
                for customer in filtered_customers
                if customer.is_active
            ]
        # ==========================================
        # نمایش نتایج
        # ==========================================
        for customer in filtered_customers:
            self.customer_tree.insert(
                "",
                "end",
                values=(
                    customer.national_id or "-",
                    customer.family or "-",
                    customer.name or "-",
                    customer.customer_code or "-",
                    customer.id
                )
            )
    def toggle_customer_field(
        self,
        name
    ):
        frame = self.customer_frames[name]
        variable = self.customer_vars[name]
        if variable.get():
            frame.grid()
        else:
            frame.grid_remove()
        self.search_customer()
    def add_selected_customers(self):
        selected_items = (
            self.customer_tree.selection()
        )
        if not selected_items:
            messagebox.showerror(
                "خطا",
                "حداقل یک بیمه گذار را انتخاب کنید",
                parent=self.window
            )
            return
        # شناسه بیمه‌گذارانی که قبلاً انتخاب شده‌اند
        existing_ids = {
            customer.id
            for customer in self.selected_customers
        }
        # اضافه کردن انتخاب‌های جدید
        for item_id in selected_items:
            customer_values = (
                self.customer_tree.item(
                    item_id,
                    "values"
                )
            )
            customer_id = int(
                customer_values[-1]
            )
            # اگر قبلاً اضافه شده، دوباره اضافه نکن
            if customer_id in existing_ids:
                continue
            customer = get_customer_by_id(
                customer_id
            )
            if customer:
                self.selected_customers.append(
                    customer
                )
                existing_ids.add(
                    customer_id
                )
        # ==========================================
        # بازسازی لیست انتخاب‌شده‌ها
        # ==========================================
        self.selected_customers_listbox.delete(
            0,
            tk.END
        )
        for customer in self.selected_customers:
            customer_display = (
                f"{customer.name} "
                f"{customer.family or ''} "
                f"{customer.customer_code}"
            )
            self.selected_customers_listbox.insert(
                tk.END,
                customer_display
            )
        # پاک کردن انتخاب از Treeview
        self.customer_tree.selection_remove(
            self.customer_tree.selection()
        )
    def confirm_selected_customers(self):
        if not self.selected_customers:
            messagebox.showerror(
                "خطا",
                "حداقل یک بیمه گذار را انتخاب کنید",
                parent=self.window
            )
            return
        if self.on_selected:
            self.on_selected(
                self.selected_customers
            )
        self.window.destroy()
    def select_customer(self):
        selected_items = (
            self.customer_tree.selection()
        )
        if not selected_items:
            messagebox.showerror(
                "خطا",
                "بیمه گذار را انتخاب کنید",
                parent=self.window
            )
            return False
        item_id = selected_items[0]
        customer_values = (
            self.customer_tree.item(
                item_id,
                "values"
            )
        )
        customer_id = customer_values[-1]
        self.customer_selected = (
            get_customer_by_id(
                customer_id
            )
        )
        if self.on_selected:
            self.on_selected(
                self.customer_selected
            )
        self.window.destroy()
def open_customer_selector(
    parent=None,
    on_selected=None,
    multi_select=False
):
    form = CustomerSelector(
        parent,
        on_selected,
        multi_select
    )
    form.window.wait_window()