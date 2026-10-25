from gui.customer_form import open_customer_form
from services.customer_service import load_customers,get_customer_by_id,toggle_customer_active
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from services.text_service import normalize_persian_search_text
from gui.styles import COLORS,schedule_title_bar_color
class CustomerList(tk.Frame):
    def __init__(self, parent, role="کاربر"):
        super().__init__(
            parent,
            bg=COLORS["background"]
        )
        self.parent = parent
        self.role = role
        self.customer_selected = None
        self.search_window = None
        self.create_widgets()
        self.load_data()
    def create_widgets(self):
        # ==================================================
        # Header
        # ==================================================
        header_frame = tk.Frame(
            self,
            bg=COLORS["background"]
        )
        header_frame.pack(
            fill="x",
            pady=(0, 15)
        )
        tk.Label(
            header_frame,
            text="لیست بیمه‌گذاران",
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=("Tahoma", 18, "bold"),
            anchor="e"
        ).pack(
            side="right"
        )
        # ==================================================
        # Table
        # ==================================================
        table_frame = tk.Frame(
            self,
            bg=COLORS["background"]
        )
        table_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )
        columns = (
            "is_active",
            "national_id",
            "phone",
            "family",
            "name",
            "customer_code",
            "id"
        )
        widths = {
            "is_active": 50,
            "national_id": 160,
            "phone": 140,
            "family": 200,
            "name": 200,
            "customer_code": 100,
            "id": 70
        }
        # ==================================================
        # Treeview Style
        # ==================================================
        style = ttk.Style()
        style.map(
            "Treeview",
            background=[
                ("selected", "#3498DB")
            ],
            foreground=[
                ("selected", "white")
            ]
        )
        # ==================================================
        # Treeview
        # ==================================================
        self.customer_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )
        headers = {
            "is_active": "فعال",
            "national_id": "کد ملی",
            "phone": "تلفن همراه",
            "family": "نام خانوادگی",
            "name": "نام",
            "customer_code": "کد بیمه‌گذار",
            "id": "شناسه"
        }
        for column, text in headers.items():
            self.customer_tree.heading(
                column,
                text=text,
                anchor="e"
            )
            self.customer_tree.column(
                column,
                width=widths[column],
                minwidth=widths[column],
                anchor="e",
                stretch=True
            )
        # ==================================================
        # Scrollbars
        # ==================================================
        y_scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.customer_tree.yview
        )
        x_scrollbar = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.customer_tree.xview
        )
        self.customer_tree.configure(
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )
        self.customer_tree.grid(
            row=0,
            column=0,
            sticky="nsew"
        )
        y_scrollbar.grid(
            row=0,
            column=1,
            sticky="ns"
        )
        x_scrollbar.grid(
            row=1,
            column=0,
            sticky="ew"
        )
        table_frame.grid_rowconfigure(
            0,
            weight=1
        )
        table_frame.grid_columnconfigure(
            0,
            weight=1
        )
        # ==================================================
        # Buttons
        # ==================================================
        button_frame = tk.Frame(
            self,
            bg=COLORS["background"]
        )
        button_frame.pack(
            pady=10
        )
        self.add_button = tk.Button(
            button_frame,
            text="ثبت بیمه‌گذار جدید",
            command=self.add_customer,
            width=20,
            background="#CDCCCC"
        )
        self.add_button.pack(
            side="right",
            padx=15
        )
        self.edit_button = tk.Button(
            button_frame,
            text="ویرایش بیمه‌گذار",
            command=self.edit_customer,
            width=20,
            background="#CDCCCC"
        )
        self.edit_button.pack(
            side="right",
            padx=15
        )
        self.toggle_button = tk.Button(
            button_frame,
            text="فعال/غیرفعال کردن بیمه‌گذار",
            command=self.toggle_active_customer,
            width=20,
            background="#CDCCCC"
        )
        self.toggle_button.pack(
            side="right",
            padx=15
        )
        self.search_button = tk.Button(
            button_frame,
            text="جستجوی بیمه‌گذار",
            command=self.open_search,
            width=20,
            background="#CDCCCC"
        )
        self.search_button.pack(
            side="right",
            padx=15
        )
        # تعیین دسترسی دکمه‌ها براساس نقش کاربر
        if self.role == "کاربر":
            self.add_button.pack_forget()
            self.edit_button.pack_forget()
        if self.role not in ("مدیر", "مدیر سیستم"):
            self.toggle_button.pack_forget()
    def load_data(self,customer=None):
        customers = load_customers()
        for item in self.customer_tree.get_children():
            self.customer_tree.delete(item)
        for customer in customers:
            self.customer_tree.insert(
                "",
                "end",
                values=(
                    "\u2713" if customer.is_active else "-",
                    "----" if customer.national_id is None else customer.national_id,
                    "----" if customer.phone is None else customer.phone,
                    "----" if customer.family is None else customer.family,
                    customer.name,
                    customer.customer_code,
                    customer.id
                )
            )
    def add_customer(self):
        if self.role not in (
            "کاربر ارشد",
            "مدیر",
            "مدیر سیستم",
        ):
            return
        open_customer_form(
            self,
            self.load_data
        )
    def edit_customer(self):
        if self.role not in (
            "کاربر ارشد",
            "مدیر",
            "مدیر سیستم",
        ):
            return
        selected = self.customer_tree.selection()
        if not selected:
            messagebox.showerror(
                "خطا",
                "لطفاً یک بیمه‌گذار را انتخاب کنید",
                parent=self
            )
            return
        item_id = selected[0]
        values = self.customer_tree.item(
            item_id,
            "values"
        )
        customer_id = values[-1]
        customer = get_customer_by_id(customer_id)
        open_customer_form(
            self,
            self.load_data,
            customer
        )
    def toggle_active_customer(self):
        if self.role not in ("مدیر", "مدیر سیستم"):
            return
        selected = self.customer_tree.selection()
        if not selected:
            messagebox.showerror(
                "خطا",
                "لطفاً یک بیمه‌گذار را انتخاب کنید",
                parent=self
            )
            return
        item_id = selected[0]
        values = self.customer_tree.item(
            item_id,
            "values"
        )
        customer_id = values[-1]
        customer = get_customer_by_id(
            customer_id
        )
        if customer.is_active:
            message = (
                "آیا از غیرفعال کردن این بیمه‌گذار "
                "مطمئن هستید؟"
            )
        else:
            message = (
                "آیا از فعال کردن این بیمه‌گذار "
                "مطمئن هستید؟"
            )
        confirm = messagebox.askyesno(
            "تأیید",
            message,
            parent=self
        )
        if not confirm:
            return
        try:
            toggle_customer_active(
                customer_id
            )
            self.load_data()
        except Exception as e:
            messagebox.showerror(
                "خطا",
                str(e),
                parent=self
            )
    def open_search(self):
        if self.search_window is not None:
            self.search_window.deiconify()
            self.search_window.lift()
            self.search_window.focus_force()
            return
        self.search_window = tk.Toplevel(self)
        self.search_window.title("جستجوی بیمه‌گذار")
        self.search_window.geometry("500x400")
        schedule_title_bar_color(self.search_window)
        self.search_window.protocol(
        "WM_DELETE_WINDOW",
        self.search_window.withdraw
         )
        tk.Label(
            self.search_window,
            text=":جستجو بر اساس",
            font=("Arial", 12, "bold")
        ).pack(
            pady=10,
            padx=10,
            anchor="e"
        )
        container = tk.Frame(self.search_window)
        container.pack(
            anchor="e",
            padx=20,
            pady=10
        )
        criteria_frame = tk.Frame(container)
        criteria_frame.pack()
        criteria = [
            ("name", "نام"),
            ("family", "نام خانوادگی"),
            ("national_id", "کد /شناسه ملی"),
            ("phone", "تلفن همراه"),
            ("customer_code", "کد بیمه گذار"),
            ("is_active", "فقط بیمه گذار فعال")
        ]
        self.customer_vars = {}
        self.customer_frames = {}
        tk.Label(
            criteria_frame,
            text="نوع شرط                           مورد جستجو"
        ).grid(
            row=0,
            column=0,
            padx=5,
            pady=4,
            sticky="e"
        )
        for row, (name, text) in enumerate(criteria):
            variable = tk.BooleanVar(
                master=self.search_window,
                value=False
            )
            self.customer_vars[name] = variable
            field_frame = tk.Frame(criteria_frame)
            self.customer_frames[name] = field_frame
            if name == "name":
                self.name_condition_combo = ttk.Combobox(
                    field_frame,
                    width=15,
                    values=["برابر با", "شامل"],
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
                    values=["برابر با", "شامل"],
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
                    values=["برابر با"],
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
            if name == "phone":
                self.phone_condition_combo = ttk.Combobox(
                    field_frame,
                    width=15,
                    values=["برابر با"],
                    state="readonly"
                )
                self.phone_condition_combo.current(0)
                self.phone_condition_combo.pack(
                    side="right",
                    padx=5
                )
                self.phone_condition_combo.bind(
                    "<<ComboboxSelected>>",
                    self.search_customer
                )
                self.phone_entry = tk.Entry(
                    field_frame,
                    width=25
                )
                self.phone_entry.pack(
                    side="right",
                    padx=5
                )
                self.phone_entry.bind(
                    "<KeyRelease>",
                    self.search_customer
                )
            if name == "customer_code":
                self.code_condition_combo = ttk.Combobox(
                    field_frame,
                    width=15,
                    values=["برابر با"],
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
            if name=="is_active":            
                self.is_active_search_var=tk.StringVar(master=self.search_window,value="فعال")
                tk.Radiobutton(
                    field_frame,
                    text="فعال",
                    variable=self.is_active_search_var,
                    value="فعال",
                    command=self.toggle_is_active_search
                ).pack(side=
                    "right"
                    )
                tk.Radiobutton(
                    field_frame,
                    text="غیر فعال",
                    variable=self.is_active_search_var,
                    value="غیر فعال",
                    command=self.toggle_is_active_search
                ).pack(
                    side="right",
                    padx=5
                )
            tk.Checkbutton(
                criteria_frame,
                variable=variable,
                command=lambda n=name: self.toggle_customer_field(n)
            ).grid(
                row=row + 1,
                column=1,
                padx=5,
                pady=4,
                sticky="e"
            )
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
            field_frame.grid(
                row=row + 1,
                column=0,
                padx=10,
                pady=4
            )
            field_frame.grid_remove()
        button_frame = tk.Frame(self.search_window)
        button_frame.pack(
            pady=15
        )
        tk.Button(
            button_frame,
            text="حذف تمام فیلترها",
            width=18,
            background="#CDCCCC",
            command=self.clear_customer_filters
        ).pack(
            side="right",
            padx=5
        )
        tk.Button(
            button_frame,
            text="تأیید",
            width=15,
            background="#CDCCCC",
            command=self.search_window.withdraw
        ).pack(
            side="right",
            padx=5
        )
    def toggle_customer_field(self, name):
        frame = self.customer_frames[name]
        variable = self.customer_vars[name]
        if variable.get():
            frame.grid()
        else:
            frame.grid_remove()
        self.search_customer()
    def search_customer(self, event=None):
        for item in self.customer_tree.get_children():
            self.customer_tree.delete(item)
        customers = load_customers()
        filtered_customers = customers
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
        if self.customer_vars["national_id"].get():
            national_id = self.national_id_entry.get()
            if national_id != "":
                filtered_customers = [
                    customer
                    for customer in filtered_customers
                    if national_id == (customer.national_id or "")
                ]
        if self.customer_vars["phone"].get():
            phone = self.phone_entry.get().strip()
            if phone != "":
                filtered_customers = [
                    customer
                    for customer in filtered_customers
                    if phone == (customer.phone or "")
                ]
        if self.customer_vars["customer_code"].get():
            customer_code = self.code_id_entry.get()
            if customer_code != "":
                filtered_customers = [
                    customer
                    for customer in filtered_customers
                    if customer_code == (customer.customer_code or "")
                ]
        if self.customer_vars["is_active"].get():
            if self.is_active_search_var.get() == "فعال":
                filtered_customers = [
                    customer
                    for customer in filtered_customers
                    if customer.is_active
                ]
            elif self.is_active_search_var.get() == "غیر فعال":
                filtered_customers = [
                    customer
                    for customer in filtered_customers
                    if not customer.is_active
                ]
        for customer in filtered_customers:
            self.customer_tree.insert(
                "",
                "end",
                values=(
                    "✓" if customer.is_active else "-",
                    "----" if customer.national_id is None else customer.national_id,
                    "----" if customer.phone is None else customer.phone,
                    "----" if customer.family is None else customer.family,
                    "----" if customer.name is None else customer.name,
                    "----" if customer.customer_code is None else customer.customer_code,
                    customer.id
                )
            )
    def clear_customer_filters(self):
        for name, variable in self.customer_vars.items():
            variable.set(False)
            self.customer_frames[name].grid_remove()
        self.customer_name_entry.delete(0, tk.END)
        self.customer_family_entry.delete(0, tk.END)
        self.national_id_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.code_id_entry.delete(0, tk.END)
        self.search_customer()
    def toggle_is_active_search(self):
        self.search_customer()
def open_customer_list(parent):
    app=CustomerList(parent)
    return app
