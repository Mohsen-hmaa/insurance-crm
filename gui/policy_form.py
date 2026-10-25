import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from services.marketer_service import load_marketers
from services.policy_service import update_policy
from services.date_service import convert_date_to_shamsi
from gui.styles import COLORS, set_title_bar_color
class PolicyForm:
    def __init__(self, policy, parent=None):
        if policy is None:
            raise ValueError("برای ویرایش، بیمه‌نامه باید مشخص باشد.")
        self.window = tk.Toplevel(parent)
        self.parent = parent
        self.window.title("ویرایش بیمه نامه")
        self.window.geometry("500x700")
        self.window.after(
            200,
            lambda: set_title_bar_color(
                self.window,
                COLORS["primary"],
            ),
        )
        self.policy = policy
        self.marketer_map = {}
        self.selected_insurance_type = None
        self.main_insurance_type = None
        self.create_widgets()
        self.fill_marketer_combo()
        self.saved = False
        self.fill_policy_form()
        if parent:
            self.window.transient(parent)
    # ---------------------------------------------------------
    # ایجاد کلی فرم
    # ---------------------------------------------------------
    def create_widgets(self):
        self.create_customer_section()
        self.create_policy_section()
        self.create_insurance_section()
        self.create_mortgage_section()
        self.create_date_section()
        self.create_referrer_section()
        self.create_premium_section()
        self.create_submit_section()
    # ---------------------------------------------------------
    # بیمه گذار
    # ---------------------------------------------------------
    def create_customer_section(self):
        tk.Label(
            self.window,
            text="بیمه گذار",
        ).pack()
        customer_frame = tk.Frame(self.window)
        customer_frame.pack(pady=5)
        self.customer_combo = ttk.Combobox(
            customer_frame,
            width=35,
            state="disabled"
        )
        self.customer_combo.pack(
            side="left"
        )
    # ---------------------------------------------------------
    # شماره بیمه نامه و الحاقیه
    # ---------------------------------------------------------
    def create_policy_section(self):
        policy_frame = tk.Frame(self.window)
        policy_frame.pack(pady=5)
        tk.Label(
            policy_frame,
            text="شماره بیمه نامه"
        ).grid(
            row=0,
            column=1,
            padx=10
        )
        tk.Label(
            policy_frame,
            text="شماره الحاقیه"
        ).grid(
            row=0,
            column=0,
            padx=10
        )
        self.policy_number_entry = tk.Entry(
            policy_frame,
            width=25,
            state="readonly"
        )
        self.policy_number_entry.grid(
            row=1,
            column=1,
            padx=15
        )
        self.endorsement_number_entry = tk.Entry(
            policy_frame,
            width=15,
            state="readonly"
        )
        self.endorsement_number_entry.grid(
            row=1,
            column=0,
            padx=10
        )
    # ---------------------------------------------------------
    # تاریخ ها
    # ---------------------------------------------------------
    def create_date_section(self):
        date_frame = tk.Frame(self.window)
        date_frame.pack(pady=5)
        tk.Label(
            date_frame,
            text="تاریخ صدور"
        ).grid(
            row=0,
            column=2,
            padx=10
        )
        tk.Label(
            date_frame,
            text="تاریخ شروع بیمه نامه"
        ).grid(
            row=0,
            column=1,
            padx=10
        )
        tk.Label(
            date_frame,
            text="تاریخ پایان بیمه نامه"
        ).grid(
            row=0,
            column=0,
            padx=10
        )
        self.issue_date_entry = tk.Entry(
            date_frame,
            width=15,
            state="readonly"
        )
        self.issue_date_entry.grid(
            row=1,
            column=2,
            padx=10
        )
        self.start_date_entry = tk.Entry(
            date_frame,
            width=15,
            state="readonly"
        )
        self.start_date_entry.grid(
            row=1,
            column=1,
            padx=10
        )
        self.end_date_entry = tk.Entry(
            date_frame,
            width=15,
            state="readonly"
        )
        self.end_date_entry.grid(
            row=1,
            column=0,
            padx=10
        )
    # ---------------------------------------------------------
    # معرف / بازاریاب
    # ---------------------------------------------------------
    def create_referrer_section(self):
        self.referrer_type = tk.StringVar(
            master=self.window,
            value="none"
        )
        self.referrer_type_frame = tk.Frame(
            self.window
        )
        self.referrer_type_frame.pack(
            pady=5
        )
        tk.Radiobutton(
            self.referrer_type_frame,
            text="بدون معرف و بازاریاب",
            variable=self.referrer_type,
            value="none",
            command=self.toggle_referrer
        ).pack(
            side="right"
        )
        tk.Radiobutton(
            self.referrer_type_frame,
            text="معرف دارد",
            variable=self.referrer_type,
            value="introducer",
            command=self.toggle_referrer
        ).pack(
            side="right",
            padx=5
        )
        tk.Radiobutton(
            self.referrer_type_frame,
            text="بازاریاب دارد",
            variable=self.referrer_type,
            value="marketer",
            command=self.toggle_referrer
        ).pack(
            side="right",
            padx=5
        )
        self.referrer_container = tk.Frame(
            self.window
        )
        self.referrer_container.pack(
            pady=5
        )
        # ---------------- معرف ----------------
        self.introducer_frame = tk.Frame(
            self.referrer_container
        )
        tk.Label(
            self.introducer_frame,
            text="نام معرف"
        ).pack()
        self.introducer_entry = tk.Entry(
            self.introducer_frame,
            width=40
        )
        self.introducer_entry.pack()
        # ---------------- بازاریاب ----------------
        self.marketer_frame = tk.Frame(
            self.referrer_container
        )
        tk.Label(
            self.marketer_frame,
            text="نام بازاریاب"
        ).pack()
        self.marketer_combo = ttk.Combobox(
            self.marketer_frame,
            width=40,
            state="readonly"
        )
        self.marketer_combo.pack()
    # ---------------------------------------------------------
    # رشته بیمه
    # ---------------------------------------------------------
    def create_insurance_section(self):
        tk.Label(
            self.window,
            text="رشته بیمه"
        ).pack()
        self.insurance_label = tk.Label(
            self.window,
            width=42,
            height=3,
            anchor="e",
            justify="right",
            wraplength=300,
            relief="sunken"
        )
        self.insurance_label.pack(
            pady=5
        )
    # ---------------------------------------------------------
    # مرهوناتی
    # ---------------------------------------------------------
    def create_mortgage_section(self):
        self.mortgage_frame_container = tk.Frame(
            self.window
        )
        self.mortgage_frame_container.pack(
            pady=5
        )
        self.mortgage_frame = tk.Frame(
            self.mortgage_frame_container
        )
        self.mortgage_type = tk.BooleanVar(
            master=self.window,
            value=False
        )
        tk.Radiobutton(
            self.mortgage_frame,
            text="غیر مرهوناتی",
            variable=self.mortgage_type,
            value=False
        ).pack(
            side="right"
        )
        tk.Radiobutton(
            self.mortgage_frame,
            text="مرهوناتی",
            variable=self.mortgage_type,
            value=True
        ).pack(
            side="left"
        )
    # ---------------------------------------------------------
    # حق بیمه و صندوق
    # ---------------------------------------------------------
    def create_premium_section(self):
        self.premium_fund_frame = tk.Frame(
            self.window
        )
        self.premium_fund_frame.pack(
            pady=5
        )
        # ---------------- حق بیمه ----------------
        tk.Label(
            self.premium_fund_frame,
            text="جمع کل حق بیمه"
        ).pack()
        self.premium_entry = tk.Entry(
            self.premium_fund_frame,
            width=42,
            state="readonly"
        )
        self.premium_entry.pack(
            pady=5
        )
        # ---------------- صندوق ----------------
        self.fund_frame = tk.Frame(
            self.premium_fund_frame
        )
        tk.Label(
            self.fund_frame,
            text="سهم صندوق"
        ).pack()
        self.fund_entry = tk.Entry(
            self.fund_frame,
            width=42,
            state="readonly"
        )
        self.fund_entry.pack(
            pady=5
        )
        self.fund_frame.pack_forget()
    # ---------------------------------------------------------
    # دکمه ذخیره
    # ---------------------------------------------------------
    def create_submit_section(self):
        self.save_button = tk.Button(
            self.window,
            text="ذخیره تغییرات",
            command=self.save_policy
        )
        self.save_button.pack(
            pady=20
        )
    # ---------------------------------------------------------
    # بارگذاری بازاریاب ها
    # ---------------------------------------------------------
    def fill_marketer_combo(self):
        self.marketer_map.clear()
        marketers = load_marketers()
        marketer_names = []
        for marketer in marketers:
            if marketer.is_active:
                marketer_names.append(
                    marketer.name
                )
                self.marketer_map[
                    marketer.name
                ] = marketer.id
        self.marketer_combo["values"] = marketer_names
    # ---------------------------------------------------------
    # تغییر وضعیت معرف / بازاریاب
    # ---------------------------------------------------------
    def toggle_referrer(self):
        choice = self.referrer_type.get()
        self.introducer_frame.pack_forget()
        self.marketer_frame.pack_forget()
        if choice == "introducer":
            self.marketer_combo.set("")
            self.introducer_frame.pack(
                pady=5
            )
        elif choice == "marketer":
            self.introducer_entry.delete(
                0,
                tk.END
            )
            self.marketer_frame.pack(
                pady=5
            )
        else:
            self.introducer_entry.delete(
                0,
                tk.END
            )
            self.marketer_combo.set("")
    # ---------------------------------------------------------
    # اطلاعات قابل ویرایش
    # ---------------------------------------------------------
    def get_policy_data(self):
        choice = self.referrer_type.get()
        data = {
            "marketer_id": None,
            "referrer": None,
            "referrer_type": choice,
            "is_mortgage": self.mortgage_type.get(),
        }
        if choice == "introducer":
            data["referrer"] = (
                self.introducer_entry
                .get()
                .strip()
            )
        elif choice == "marketer":
            marketer_name = self.marketer_combo.get()
            data["marketer_id"] = (
                self.marketer_map.get(marketer_name)
            )
            data["referrer"] = marketer_name
        return data
    # ---------------------------------------------------------
    # ذخیره تغییرات
    # ---------------------------------------------------------
    def save_policy(self):
        if not self.validate_form():
            return
        data = self.get_policy_data()
        try:
            update_policy(
                self.policy.id,
                data
            )
            messagebox.showinfo(
                "موفق",
                "تغییرات با موفقیت ذخیره شد",
                parent=self.window
            )
            self.saved = True
            self.window.destroy()
        except Exception as e:
            messagebox.showerror(
                "خطا",
                str(e),
                parent=self.window
            )
    # ---------------------------------------------------------
    # اعتبارسنجی
    # ---------------------------------------------------------
    def validate_form(self):
        choice = self.referrer_type.get()
        if choice == "introducer":
            if not self.introducer_entry.get().strip():
                messagebox.showerror(
                    "خطا",
                    "نام معرف را وارد کنید",
                    parent=self.window
                )
                return False
        elif choice == "marketer":
            if not self.marketer_combo.get():
                messagebox.showerror(
                    "خطا",
                    "بازاریاب را انتخاب کنید",
                    parent=self.window
                )
                return False
        return True
    # ---------------------------------------------------------
    # پر کردن فرم با اطلاعات بیمه نامه
    # ---------------------------------------------------------
    def fill_policy_form(self):
        # ---------------- شماره بیمه نامه ----------------
        self.policy_number_entry.config(
            state="normal"
        )
        self.policy_number_entry.delete(
            0,
            tk.END
        )
        self.policy_number_entry.insert(
            0,
            self.policy.policy_number or ""
        )
        self.policy_number_entry.config(
            state="readonly"
        )
        # ---------------- شماره الحاقیه ----------------
        self.endorsement_number_entry.config(
            state="normal"
        )
        self.endorsement_number_entry.delete(
            0,
            tk.END
        )
        self.endorsement_number_entry.insert(
            0,
            str(self.policy.endorsement_number)
        )
        self.endorsement_number_entry.config(
            state="readonly"
        )
        # ---------------- بیمه گذار ----------------
        if self.policy.customer:
            customer_name = (
                f"{self.policy.customer.customer_code} - "
                f"{self.policy.customer.name} "
                f"{self.policy.customer.family or ''}"
            ).strip()
            self.customer_combo.config(
                state="normal"
            )
            self.customer_combo.set(
                customer_name
            )
            self.customer_combo.config(
                state="disabled"
            )
        # ---------------- رشته بیمه ----------------
        if self.policy.insurance_type:
            self.selected_insurance_type = (
                self.policy.insurance_type
            )
            self.insurance_label.config(
                text=self.policy.insurance_type.display_name
            )
        # ---------------- مرهوناتی ----------------
        self.mortgage_type.set(
            bool(self.policy.is_mortgage)
        )
        self.show_mortgage_section()
        # ---------------- صندوق ----------------
        if (
            self.policy.insurance_type
            and self.policy.insurance_type.name == "ثالث"
        ):
            self.fund_frame.pack(
                pady=5
            )
            self.fund_entry.config(
                state="normal"
            )
            self.fund_entry.delete(
                0,
                tk.END
            )
            self.fund_entry.insert(
                0,
                f"{self.policy.fund:,}"
            )
            self.fund_entry.config(
                state="readonly"
            )
        else:
            self.fund_frame.pack_forget()
        # ---------------- تاریخ صدور ----------------
        if self.policy.issue_date:
            self.issue_date_entry.config(
                state="normal"
            )
            self.issue_date_entry.delete(
                0,
                tk.END
            )
            self.issue_date_entry.insert(
                0,
                str(
                    convert_date_to_shamsi(
                        self.policy.issue_date
                    )
                )
            )
            self.issue_date_entry.config(
                state="readonly"
            )
        # ---------------- تاریخ شروع ----------------
        if self.policy.start_date:
            self.start_date_entry.config(
                state="normal"
            )
            self.start_date_entry.delete(
                0,
                tk.END
            )
            self.start_date_entry.insert(
                0,
                str(
                    convert_date_to_shamsi(
                        self.policy.start_date
                    )
                )
            )
            self.start_date_entry.config(
                state="readonly"
            )
        # ---------------- تاریخ پایان ----------------
        if self.policy.end_date:
            self.end_date_entry.config(
                state="normal"
            )
            self.end_date_entry.delete(
                0,
                tk.END
            )
            self.end_date_entry.insert(
                0,
                str(
                    convert_date_to_shamsi(
                        self.policy.end_date
                    )
                )
            )
            self.end_date_entry.config(
                state="readonly"
            )
        # ---------------- حق بیمه ----------------
        self.premium_entry.config(
            state="normal"
        )
        self.premium_entry.delete(
            0,
            tk.END
        )
        self.premium_entry.insert(
            0,
            f"{self.policy.premium:,}"
        )
        self.premium_entry.config(
            state="readonly"
        )
        # ---------------- معرف / بازاریاب ----------------
        choice = self.policy.referrer_type or "none"
        self.referrer_type.set(
            choice
        )
        self.toggle_referrer()
        if choice == "introducer":
            self.introducer_entry.delete(
                0,
                tk.END
            )
            self.introducer_entry.insert(
                0,
                self.policy.referrer or ""
            )
        elif choice == "marketer":
            if self.policy.marketer:
                marketer_name = (
                    self.policy.marketer.name.strip()
                )
                self.marketer_combo.set(
                    marketer_name
                )
    # ---------------------------------------------------------
    # نمایش بخش مرهوناتی
    # ---------------------------------------------------------
    def show_mortgage_section(self):
        self.mortgage_frame.pack(
            pady=5
        )
# =============================================================
# تابع باز کردن فرم
# =============================================================
def open_policy_form(policy, parent=None):
    form = PolicyForm(
        policy,
        parent
    )
    form.window.wait_window()
    return form.saved