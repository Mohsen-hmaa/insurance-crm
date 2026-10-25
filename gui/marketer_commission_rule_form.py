import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation
from gui.styles import COLORS, set_title_bar_color
from services.marketer_service import (
create_commission_rule,
get_commission_rules,
delete_commission_rule
)
from gui.policy_selector import open_policy_selector
from gui.customer_selector import open_customer_selector
from services.insurance_type_service import (
load_root_insurance_types
)
from gui.insurance_selector import InsuranceSelector
from services.date_service import (
convert_shamsi_to_date,
convert_date_to_shamsi
)
class MarketerCommissionRuleForm:
    def __init__(
        self,
        parent,
        marketer,
        on_saved=None
    ):
        self.parent = parent
        self.marketer = marketer
        self.on_saved = on_saved
        self.selected_customer = None
        self.selected_insurance_type = None
        self.selected_policy = None
        self.window = tk.Toplevel(parent)
        self.window.title(
            f"قوانین کمیسیون بازاریاب «{marketer.name}»"
        )
        self.window.geometry("1000x600")
        self.window.after(
            200,
            lambda: set_title_bar_color(
                self.window,
                COLORS["primary"],
            ),
        )
        self.create_widgets()
        self.load_rules()
    # ==================================================
    # ابزارها
    # ==================================================
    def to_persian_digits(self, value):
        """
        تبدیل اعداد انگلیسی به فارسی
        """
        if value is None:
            return ""
        translation_table = str.maketrans(
            "0123456789",
            "۰۱۲۳۴۵۶۷۸۹"
        )
        return str(value).translate(
            translation_table
        )
    def format_policy_number(self, value):
        """
        حذف .0 از شماره بیمه نامه
        و نمایش اعداد به صورت فارسی
        """
        if value is None:
            return ""
        text = str(value).strip()
        if not text:
            return ""
        try:
            number = Decimal(text)
            if number == number.to_integral_value():
                text = str(
                    number.quantize(
                        Decimal("1")
                    )
                )
            else:
                text = str(number)
        except (
            InvalidOperation,
            ValueError,
            TypeError
        ):
            pass
        return self.to_persian_digits(
            text
        )
    def set_entry_value(
        self,
        entry,
        value,
        readonly=True
    ):
        entry.config(
            state="normal"
        )
        entry.delete(
            0,
            tk.END
        )
        if value is not None:
            entry.insert(
                0,
                str(value)
            )
        if readonly:
            entry.config(
                state="readonly"
            )
    # ==================================================
    # ساخت فرم
    # ==================================================
    def create_widgets(self):
        top_container = tk.Frame(
            self.window
        )
        top_container.pack(
            fill="x",
            padx=10,
            pady=10
        )
        form_frame = tk.Frame(
            top_container
        )
        form_frame.pack(
            side="right"
        )
        # ----------------------------------------------
        # مشتری
        # ----------------------------------------------
        tk.Label(
            form_frame,
            text="بیمه گذار:"
        ).grid(
            row=0,
            column=3,
            padx=5,
            pady=5,
            sticky="e"
        )
        self.customer_entry = tk.Entry(
            form_frame,
            width=45,
            state="readonly",
            justify="right"
        )
        self.customer_entry.grid(
            row=0,
            column=2,
            padx=5,
            pady=5
        )
        self.customer_select_button = tk.Button(
            form_frame,
            text="انتخاب",
            command=self.select_customer
        )
        self.customer_select_button.grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )
        self.customer_clear_button = tk.Button(
            form_frame,
            text="پاک کردن",
            command=self.clear_customer
        )
        self.customer_clear_button.grid(
            row=0,
            column=0,
            padx=5,
            pady=5
        )
        # ----------------------------------------------
        # نوع بیمه
        # ----------------------------------------------
        tk.Label(
            form_frame,
            text="نوع بیمه:"
        ).grid(
            row=1,
            column=3,
            padx=5,
            pady=5,
            sticky="e"
        )
        self.insurance_type_entry = tk.Entry(
            form_frame,
            width=45,
            state="readonly",
            justify="right"
        )
        self.insurance_type_entry.grid(
            row=1,
            column=2,
            padx=5,
            pady=5
        )
        self.insurance_type_select_button = tk.Button(
            form_frame,
            text="انتخاب",
            command=self.select_insurance_type
        )
        self.insurance_type_select_button.grid(
            row=1,
            column=1,
            padx=5,
            pady=5
        )
        self.insurance_type_clear_button = tk.Button(
            form_frame,
            text="پاک کردن",
            command=self.clear_insurance_type
        )
        self.insurance_type_clear_button.grid(
            row=1,
            column=0,
            padx=5,
            pady=5
        )
        # ----------------------------------------------
        # بیمه نامه
        # ----------------------------------------------
        tk.Label(
            form_frame,
            text="بیمه‌نامه:"
        ).grid(
            row=2,
            column=3,
            padx=5,
            pady=5,
            sticky="e"
        )
        self.policy_entry = tk.Entry(
            form_frame,
            width=45,
            state="readonly",
            justify="right"
        )
        self.policy_entry.grid(
            row=2,
            column=2,
            padx=5,
            pady=5
        )
        self.policy_select_button = tk.Button(
            form_frame,
            text="انتخاب",
            command=self.select_policy
        )
        self.policy_select_button.grid(
            row=2,
            column=1,
            padx=5,
            pady=5
        )
        self.policy_clear_button = tk.Button(
            form_frame,
            text="پاک کردن",
            command=self.clear_policy
        )
        self.policy_clear_button.grid(
            row=2,
            column=0,
            padx=5,
            pady=5
        )
        # ----------------------------------------------
        # مرهون
        # ----------------------------------------------
        tk.Label(
            form_frame,
            text="وضعیت مرهون:"
        ).grid(
            row=3,
            column=3,
            padx=5,
            pady=5,
            sticky="e"
        )
        self.mortgage_var = tk.StringVar(
            value="همه"
        )
        self.mortgage_combo = ttk.Combobox(
            form_frame,
            textvariable=self.mortgage_var,
            state="readonly",
            values=[
                "همه",
                "مرهون",
                "غیر مرهون"
            ],
            width=15
        )
        self.mortgage_combo.grid(
            row=3,
            column=2,
            padx=5,
            pady=5,
            sticky="w"
        )
        # ----------------------------------------------
        # تاریخ شروع اثر قانون
        # ----------------------------------------------
        tk.Label(
            form_frame,
            text="از تاریخ:"
        ).grid(
            row=4,
            column=3,
            padx=5,
            pady=5,
            sticky="e"
        )
        self.start_date_entry = tk.Entry(
            form_frame,
            width=20,
            justify="right"
        )
        self.start_date_entry.grid(
            row=4,
            column=2,
            padx=5,
            pady=5,
            sticky="w"
        )
        # ----------------------------------------------
        # تاریخ پایان اثر قانون
        # ----------------------------------------------
        tk.Label(
            form_frame,
            text="تا تاریخ:"
        ).grid(
            row=5,
            column=3,
            padx=5,
            pady=5,
            sticky="e"
        )
        self.end_date_entry = tk.Entry(
            form_frame,
            width=20,
            justify="right"
        )
        self.end_date_entry.grid(
            row=5,
            column=2,
            padx=5,
            pady=5,
            sticky="w"
        )
        # ----------------------------------------------
        # درصد کمیسیون
        # ----------------------------------------------
        tk.Label(
            form_frame,
            text="درصد کمیسیون:"
        ).grid(
            row=6,
            column=3,
            padx=5,
            pady=5,
            sticky="e"
        )
        self.commission_entry = tk.Entry(
            form_frame,
            width=20,
            justify="right"
        )
        self.commission_entry.grid(
            row=6,
            column=2,
            padx=5,
            pady=5,
            sticky="w"
        )
        # ----------------------------------------------
        # ثبت و پاک کردن
        # ----------------------------------------------
        button_frame = tk.Frame(
            self.window
        )
        button_frame.pack(
            pady=10
        )
        tk.Button(
            button_frame,
            text="ثبت قانون",
            width=15,
            command=self.save_rule
        ).pack(
            side="right",
            padx=5
        )
        tk.Button(
            button_frame,
            text="پاک کردن فرم",
            width=15,
            command=self.clear_form
        ).pack(
            side="right",
            padx=5
        )
        # ==================================================
        # لیست قوانین
        # ==================================================
        list_frame = tk.Frame(
            self.window
        )
        list_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )
        columns = (
            "end_date",
            "start_date",
            "commission",
            "mortgage",
            "policy",
            "insurance_type",
            "customer",
            "id"
        )
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings"
        )
        headings = {
            "id": "شناسه",
            "customer": "مشتری",
            "insurance_type": "نوع بیمه",
            "policy": "بیمه‌نامه",
            "mortgage": "مرهون",
            "commission": "درصد کمیسیون",
            "start_date": "از تاریخ",
            "end_date": "تا تاریخ"
        }
        for column in columns:
            self.tree.heading(
                column,
                text=headings[column],
                anchor="e"
            )
        self.tree.column(
            "end_date",
            width=100,
            anchor="e"
        )
        self.tree.column(
            "start_date",
            width=100,
            anchor="e"
        )
        self.tree.column(
            "commission",
            width=100,
            anchor="e"
        )
        self.tree.column(
            "mortgage",
            width=80,
            anchor="e"
        )
        self.tree.column(
            "policy",
            width=120,
            anchor="e"
        )
        self.tree.column(
            "insurance_type",
            width=150,
            anchor="e"
        )
        self.tree.column(
            "customer",
            width=250,
            anchor="e"
        )
        self.tree.column(
            "id",
            width=60,
            anchor="e"
        )
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(
            yscrollcommand=scrollbar.set
        )
        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )
        scrollbar.pack(
            side="right",
            fill="y"
        )
        # ----------------------------------------------
        # حذف
        # ----------------------------------------------
        tk.Button(
            self.window,
            text="حذف قانون",
            command=self.delete_rule
        ).pack(
            pady=10
        )
    # ==================================================
    # مشتری
    # ==================================================
    def select_customer(self):
        if self.selected_policy:
            return
        open_customer_selector(
            self.window,
            self.customer_selected
        )
    def customer_selected(
        self,
        customer
    ):
        self.selected_customer = customer
        display_name = (
            f"{customer.name} "
            f"{customer.family or ''} "
            f"{customer.customer_code or ''}"
        ).strip()
        self.set_entry_value(
            self.customer_entry,
            display_name
        )
    def clear_customer(self):
        if self.selected_policy:
            return
        self.selected_customer = None
        self.set_entry_value(
            self.customer_entry,
            ""
        )
    # ==================================================
    # نوع بیمه
    # ==================================================
    def select_insurance_type(self):
        if self.selected_policy:
            return
        root_types = load_root_insurance_types()
        InsuranceSelector(
            self.window,
            root_types,
            self.insurance_type_selected
        )
    def insurance_type_selected(
        self,
        selected_path
    ):
        if not selected_path:
            return
        self.selected_insurance_type = (
            selected_path[-1]
        )
        self.set_entry_value(
            self.insurance_type_entry,
            self.selected_insurance_type.display_name
        )
    def clear_insurance_type(self):
        if self.selected_policy:
            return
        self.selected_insurance_type = None
        self.set_entry_value(
            self.insurance_type_entry,
            ""
        )
    # ==================================================
    # بیمه نامه
    # ==================================================
    def select_policy(self):
        open_policy_selector(
            self.window,
            self.policy_selected
        )
    def policy_selected(
        self,
        policy
    ):
        self.selected_policy = policy
        # ----------------------------------------------
        # شماره بیمه نامه
        # ----------------------------------------------
        policy_number = self.format_policy_number(
            policy.policy_number
        )
        policy_text = policy_number
        if policy.endorsement_number:
            policy_text += (
                f" - الحاقیه "
                f"{self.to_persian_digits(policy.endorsement_number)}"
            )
        self.set_entry_value(
            self.policy_entry,
            policy_text
        )
        # ----------------------------------------------
        # بیمه گذار
        # ----------------------------------------------
        self.selected_customer = (
            policy.customer
        )
        customer_text = "-"
        if policy.customer:
            customer_text = (
                f"{policy.customer.name} "
                f"{policy.customer.family or ''} "
                f"{policy.customer.customer_code or ''}"
            ).strip()
        self.set_entry_value(
            self.customer_entry,
            customer_text
        )
        # ----------------------------------------------
        # نوع بیمه
        # ----------------------------------------------
        self.selected_insurance_type = (
            policy.insurance_type
        )
        insurance_type_text = "-"
        if policy.insurance_type:
            insurance_type_text = (
                policy.insurance_type.display_name
            )
        self.set_entry_value(
            self.insurance_type_entry,
            insurance_type_text
        )
        # ----------------------------------------------
        # وضعیت مرهون بیمه نامه
        # ----------------------------------------------
        if policy.is_mortgage:
            self.mortgage_var.set(
                "مرهون"
            )
        else:
            self.mortgage_var.set(
                "غیر مرهون"
            )
        self.mortgage_combo.config(
            state="disabled"
        )
        # ----------------------------------------------
        # تاریخ اثر قانون
        #
        # نکته:
        # تاریخ شروع و پایان بیمه نامه اینجا قرار نمی‌گیرند.
        # این دو فیلد فقط بازه اثر خود قانون هستند.
        # ----------------------------------------------
        self.start_date_entry.config(
            state="normal"
        )
        self.start_date_entry.delete(
            0,
            tk.END
        )
        self.start_date_entry.config(
            state="disabled"
        )
        self.end_date_entry.config(
            state="normal"
        )
        self.end_date_entry.delete(
            0,
            tk.END
        )
        self.end_date_entry.config(
            state="disabled"
        )
        # ----------------------------------------------
        # غیرفعال کردن انتخاب مشتری
        # ----------------------------------------------
        self.customer_select_button.config(
            state="disabled"
        )
        self.customer_clear_button.config(
            state="disabled"
        )
        # ----------------------------------------------
        # غیرفعال کردن انتخاب رشته
        # ----------------------------------------------
        self.insurance_type_select_button.config(
            state="disabled"
        )
        self.insurance_type_clear_button.config(
            state="disabled"
        )
    def clear_policy(self):
        self.selected_policy = None
        # ----------------------------------------------
        # پاک کردن بیمه نامه
        # ----------------------------------------------
        self.set_entry_value(
            self.policy_entry,
            ""
        )
        # ----------------------------------------------
        # پاک کردن مشتری
        # ----------------------------------------------
        self.selected_customer = None
        self.set_entry_value(
            self.customer_entry,
            ""
        )
        # ----------------------------------------------
        # پاک کردن رشته
        # ----------------------------------------------
        self.selected_insurance_type = None
        self.set_entry_value(
            self.insurance_type_entry,
            ""
        )
        # ----------------------------------------------
        # فعال کردن مرهون
        # ----------------------------------------------
        self.mortgage_var.set(
            "همه"
        )
        self.mortgage_combo.config(
            state="readonly"
        )
        # ----------------------------------------------
        # فعال کردن تاریخ شروع قانون
        # ----------------------------------------------
        self.start_date_entry.config(
            state="normal"
        )
        self.start_date_entry.delete(
            0,
            tk.END
        )
        # ----------------------------------------------
        # فعال کردن تاریخ پایان قانون
        # ----------------------------------------------
        self.end_date_entry.config(
            state="normal"
        )
        self.end_date_entry.delete(
            0,
            tk.END
        )
        # ----------------------------------------------
        # فعال کردن انتخاب مشتری
        # ----------------------------------------------
        self.customer_select_button.config(
            state="normal"
        )
        self.customer_clear_button.config(
            state="normal"
        )
        # ----------------------------------------------
        # فعال کردن انتخاب رشته
        # ----------------------------------------------
        self.insurance_type_select_button.config(
            state="normal"
        )
        self.insurance_type_clear_button.config(
            state="normal"
        )
    # ==================================================
    # ذخیره قانون
    # ==================================================
    def save_rule(self):
        mortgage_value = (
            self.mortgage_var.get()
        )
        start_date_text = (
            self.start_date_entry
            .get()
            .strip()
        )
        end_date_text = (
            self.end_date_entry
            .get()
            .strip()
        )
        # ----------------------------------------------
        # حداقل یک شرط
        # ----------------------------------------------
        has_condition = any([
            self.selected_customer is not None,
            self.selected_insurance_type is not None,
            self.selected_policy is not None,
            mortgage_value != "همه",
            bool(start_date_text),
            bool(end_date_text)
        ])
        if not has_condition:
            messagebox.showwarning(
                "خطا",
                "حداقل یک شرط برای قانون کمیسیون تعیین کنید.",
                parent=self.window
            )
            return
        # ----------------------------------------------
        # درصد کمیسیون
        # ----------------------------------------------
        commission_text = (
            self.commission_entry
            .get()
            .strip()
        )
        if not commission_text:
            messagebox.showwarning(
                "خطا",
                "درصد کمیسیون را وارد کنید.",
                parent=self.window
            )
            return
        try:
            commission_percent = float(
                commission_text
            )
        except ValueError:
            messagebox.showwarning(
                "خطا",
                "درصد کمیسیون باید عدد باشد.",
                parent=self.window
            )
            return
        if (
            commission_percent < 0
            or commission_percent > 100
        ):
            messagebox.showwarning(
                "خطا",
                "درصد کمیسیون باید بین ۰ تا ۱۰۰ باشد.",
                parent=self.window
            )
            return
        # ----------------------------------------------
        # تاریخ اثر قانون
        # ----------------------------------------------
        start_date = None
        end_date = None
        try:
            if start_date_text:
                start_date = convert_shamsi_to_date(
                    start_date_text
                )
            if end_date_text:
                end_date = convert_shamsi_to_date(
                    end_date_text
                )
        except Exception:
            messagebox.showwarning(
                "خطا",
                "فرمت تاریخ صحیح نیست.",
                parent=self.window
            )
            return
        if (
            start_date is not None
            and end_date is not None
            and start_date > end_date
        ):
            messagebox.showwarning(
                "خطا",
                "تاریخ شروع نمی‌تواند بعد از تاریخ پایان باشد.",
                parent=self.window
            )
            return
        # ----------------------------------------------
        # وضعیت مرهون
        # ----------------------------------------------
        is_mortgage = None
        if mortgage_value == "مرهون":
            is_mortgage = True
        elif mortgage_value == "غیر مرهون":
            is_mortgage = False
        # ----------------------------------------------
        # اطلاعات قانون
        # ----------------------------------------------
        data = {
            "marketer_id": self.marketer.id,
            "policy_id": (
                self.selected_policy.id
                if self.selected_policy
                else None
            ),
            "customer_id": (
                self.selected_customer.id
                if self.selected_customer
                else None
            ),
            "insurance_type_id": (
                self.selected_insurance_type.id
                if self.selected_insurance_type
                else None
            ),
            "is_mortgage": is_mortgage,
            "commission_percent":
                commission_percent,
            "start_date":
                start_date,
            "end_date":
                end_date
        }
        try:
            create_commission_rule(
                data
            )
        except Exception as e:
            messagebox.showerror(
                "خطا",
                f"ثبت قانون با خطا مواجه شد:\n{e}",
                parent=self.window
            )
            return
        self.load_rules()
        self.clear_form()
        if self.on_saved:
            self.on_saved()
        messagebox.showinfo(
            "ثبت قانون",
            "قانون کمیسیون با موفقیت ثبت شد.",
            parent=self.window
        )
    # ==================================================
    # پاک کردن فرم
    # ==================================================
    def clear_form(self):
        self.clear_policy()
        self.mortgage_var.set(
            "همه"
        )
        self.start_date_entry.config(
            state="normal"
        )
        self.start_date_entry.delete(
            0,
            tk.END
        )
        self.end_date_entry.config(
            state="normal"
        )
        self.end_date_entry.delete(
            0,
            tk.END
        )
        self.commission_entry.delete(
            0,
            tk.END
        )
    # ==================================================
    # نمایش قوانین
    # ==================================================
    def load_rules(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        rules = get_commission_rules(
            self.marketer.id
        )
        for rule in rules:
            # ------------------------------------------
            # بیمه گذار
            # ------------------------------------------
            customer_text = "-"
            if rule.customer:
                customer_text = (
                    f"{rule.customer.name} "
                    f"{rule.customer.family or ''}"
                ).strip()
                if rule.customer.customer_code:
                    customer_text += (
                        f" {rule.customer.customer_code}"
                    )
            # ------------------------------------------
            # رشته بیمه
            # ------------------------------------------
            insurance_type_text = "-"
            if rule.insurance_type:
                insurance_type_text = (
                    rule.insurance_type.display_name
                )
            # ------------------------------------------
            # بیمه نامه
            # ------------------------------------------
            policy_text = "-"
            if rule.policy:
                policy_number = (
                    self.format_policy_number(
                        rule.policy.policy_number
                    )
                )
                policy_text = policy_number
                if rule.policy.endorsement_number:
                    policy_text += (
                        f" - الحاقیه "
                        f"{self.to_persian_digits(
                            rule.policy.endorsement_number
                        )}"
                    )
            # ------------------------------------------
            # مرهون
            # ------------------------------------------
            if rule.is_mortgage is True:
                mortgage_text = "بله"
            elif rule.is_mortgage is False:
                mortgage_text = "خیر"
            else:
                mortgage_text = "همه"
            # ------------------------------------------
            # تاریخ اثر قانون
            # ------------------------------------------
            start_date_text = ""
            if rule.start_date:
                start_date_text = convert_date_to_shamsi(
                    rule.start_date
                )
            end_date_text = ""
            if rule.end_date:
                end_date_text = convert_date_to_shamsi(
                    rule.end_date
                )
            # ------------------------------------------
            # تبدیل تاریخ‌ها به اعداد فارسی
            # ------------------------------------------
            start_date_text = self.to_persian_digits(
                start_date_text
            )
            end_date_text = self.to_persian_digits(
                end_date_text
            )
            # ------------------------------------------
            # ثبت در جدول
            # ------------------------------------------
            self.tree.insert(
                "",
                "end",
                values=(
                    end_date_text,
                    start_date_text,
                    self.to_persian_digits(
                        rule.commission_percent
                    ),
                    mortgage_text,
                    policy_text,
                    insurance_type_text,
                    customer_text,
                    rule.id
                )
            )
    # ==================================================
    # حذف قانون
    # ==================================================
    def delete_rule(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning(
                "حذف قانون",
                "لطفاً یک قانون را انتخاب کنید.",
                parent=self.window
            )
            return
        values = self.tree.item(
            selection[0],
            "values"
        )
        rule_id = int(
            values[-1]
        )
        confirm = messagebox.askyesno(
            "حذف قانون",
            "آیا از حذف این قانون مطمئن هستید؟",
            parent=self.window
        )
        if not confirm:
            return
        try:
            delete_commission_rule(
                rule_id
            )
        except Exception as e:
            messagebox.showerror(
                "خطا",
                f"حذف قانون با خطا مواجه شد:\n{e}",
                parent=self.window
            )
            return
        self.load_rules()
        if self.on_saved:
            self.on_saved()
def open_marketer_commission_rule_form(
    parent,
    marketer,
    on_saved=None
    ):
        MarketerCommissionRuleForm(
            parent,
            marketer,
            on_saved=on_saved
        )
