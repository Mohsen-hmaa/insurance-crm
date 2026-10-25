import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation
from gui.styles import COLORS
from services.date_service import (
    convert_shamsi_to_date,
    convert_date_to_shamsi,
)
from database import SessionLocal
from models import CommissionConfig
class CommissionConfigPage(tk.Frame):
    def __init__(
        self,
        parent,
        current_user_role,
        current_user_id,
    ):
        super().__init__(
            parent,
            bg=COLORS["background"],
        )
        self.current_user_role = current_user_role
        self.current_user_id = current_user_id
        self.selected_config_id = None
        self.create_widgets()
        self.load_data()
    # ==================================================
    # UI
    # ==================================================
    def create_widgets(self):
        # ----------------------------------------------
        # Header
        # ----------------------------------------------
        header_frame = tk.Frame(
            self,
            bg=COLORS["background"],
        )
        header_frame.pack(
            fill="x",
            pady=(0, 20),
        )
        tk.Label(
            header_frame,
            text="تنظیمات مالی و کارمزد",
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=("Tahoma", 18, "bold"),
            anchor="e",
        ).pack(
            side="right",
        )
        # ----------------------------------------------
        # Form
        # ----------------------------------------------
        form_card = tk.Frame(
            self,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        form_card.pack(
            fill="x",
            pady=(0, 15),
        )
        form = tk.Frame(
            form_card,
            bg=COLORS["surface"],
        )
        form.pack(
            fill="x",
            padx=20,
            pady=20,
        )
        # تاریخ اثر
        tk.Label(
            form,
            text="تاریخ اثر",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Tahoma", 10),
            anchor="e",
        ).grid(
            row=0,
            column=2,
            padx=8,
            pady=5,
            sticky="e",
        )
        self.effective_date_entry = tk.Entry(
            form,
            font=("Tahoma", 10),
            justify="right",
            width=18,
        )
        self.effective_date_entry.grid(
            row=1,
            column=2,
            padx=8,
            pady=(0, 10),
            sticky="e",
        )
        # VAT
        tk.Label(
            form,
            text="VAT (%)",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Tahoma", 10),
            anchor="e",
        ).grid(
            row=0,
            column=1,
            padx=8,
            pady=5,
            sticky="e",
        )
        self.vat_entry = tk.Entry(
            form,
            font=("Tahoma", 10),
            justify="right",
            width=18,
        )
        self.vat_entry.grid(
            row=1,
            column=1,
            padx=8,
            pady=(0, 10),
            sticky="e",
        )
        # پله اول کارمزد
        tk.Label(
            form,
            text="پله اول کارمزد",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Tahoma", 10),
            anchor="e",
        ).grid(
            row=0,
            column=0,
            padx=8,
            pady=5,
            sticky="e",
        )
        self.first_step_entry = tk.Entry(
            form,
            font=("Tahoma", 10),
            justify="right",
            width=22,
        )
        self.first_step_entry.grid(
            row=1,
            column=0,
            padx=8,
            pady=(0, 10),
            sticky="e",
        )
        # ----------------------------------------------
        # Buttons
        # ----------------------------------------------
        button_frame = tk.Frame(
            form_card,
            bg=COLORS["surface"],
        )
        button_frame.pack(
            fill="x",
            padx=20,
            pady=(0, 15),
        )
        self.save_button = tk.Button(
            button_frame,
            text="ثبت تنظیمات",
            command=self.save_config,
            width=16,
            bg=COLORS["primary"],
            fg="white",
            activebackground=COLORS["primary_dark"],
            activeforeground="white",
            relief="flat",
            bd=0,
            font=("Tahoma", 10),
            cursor="hand2",
        )
        self.save_button.pack(
            side="right",
            padx=5,
        )
        self.clear_button = tk.Button(
            button_frame,
            text="پاک کردن فرم",
            command=self.clear_form,
            width=16,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            activebackground="#E8EEF5",
            relief="flat",
            bd=0,
            font=("Tahoma", 10),
            cursor="hand2",
        )
        self.clear_button.pack(
            side="right",
            padx=5,
        )
        # ----------------------------------------------
        # Table
        # ----------------------------------------------
        table_card = tk.Frame(
            self,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        table_card.pack(
            fill="both",
            expand=True,
        )
        table_header = tk.Label(
            table_card,
            text="سوابق تنظیمات مالی",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Tahoma", 12, "bold"),
            anchor="e",
        )
        table_header.pack(
            fill="x",
            padx=20,
            pady=(15, 10),
        )
        tree_frame = tk.Frame(
            table_card,
            bg=COLORS["surface"],
        )
        tree_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20),
        )
        columns = (
            "effective_date",
            "vat",
            "first_step_commission",
        )
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        self.tree.heading(
            "effective_date",
            text="تاریخ اثر",
            anchor="center",
        )
        self.tree.heading(
            "vat",
            text="VAT",
            anchor="center",
        )
        self.tree.heading(
            "first_step_commission",
            text="پله اول کارمزد",
            anchor="center",
        )
        self.tree.column(
            "effective_date",
            width=150,
            anchor="center",
        )
        self.tree.column(
            "vat",
            width=120,
            anchor="center",
        )
        self.tree.column(
            "first_step_commission",
            width=220,
            anchor="center",
        )
        scrollbar = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(
            yscrollcommand=scrollbar.set,
        )
        scrollbar.pack(
            side="right",
            fill="y",
        )
        self.tree.pack(
            side="left",
            fill="both",
            expand=True,
        )
        self.tree.bind(
            "<Double-1>",
            self.on_row_double_click,
        )
    # ==================================================
    # Data
    # ==================================================
    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        db = SessionLocal()
        try:
            configs = (
                db.query(CommissionConfig)
                .order_by(
                    CommissionConfig.effective_date.desc()
                )
                .all()
            )
            for config in configs:
                self.tree.insert(
                    "",
                    "end",
                    iid=str(config.id),
                    values=(
                        self._to_persian_digits(
                            convert_date_to_shamsi(
                                config.effective_date
                            )
                        ),
                        self._format_decimal(
                            config.vat
                        ),
                        self._format_number(
                            config.first_step_commission
                        ),
                    ),
                )
        finally:
            db.close()
    # ==================================================
    # Save
    # ==================================================
    def save_config(self):
        if self.current_user_role != "مدیر سیستم":
            messagebox.showwarning(
                "عدم دسترسی",
                "فقط مدیر سیستم اجازه تغییر این تنظیمات را دارد.",
                parent=self,
            )
            return
        effective_date_text = (
            self.effective_date_entry
            .get()
            .strip()
        )
        vat_text = (
            self.vat_entry
            .get()
            .strip()
        )
        first_step_text = (
            self.first_step_entry
            .get()
            .strip()
        )
        # ----------------------------------------------
        # Date
        # ----------------------------------------------
        try:
            effective_date = (
                convert_shamsi_to_date(
                    effective_date_text
                )
            )
            if not effective_date:
                raise ValueError
        except Exception:
            messagebox.showwarning(
                "تاریخ نامعتبر",
                "تاریخ اثر را به صورت ۱۴۰۵/۰۷/۰۱ وارد کنید.",
                parent=self,
            )
            return
        # ----------------------------------------------
        # VAT
        # ----------------------------------------------
        try:
            vat = Decimal(
                vat_text.replace(",", "")
            )
        except (InvalidOperation, ValueError):
            messagebox.showwarning(
                "VAT نامعتبر",
                "مقدار VAT را به صورت عددی وارد کنید.",
                parent=self,
            )
            return
        if vat < 0 or vat > 100:
            messagebox.showwarning(
                "VAT نامعتبر",
                "VAT باید بین صفر تا ۱۰۰ درصد باشد.",
                parent=self,
            )
            return
        # ----------------------------------------------
        # First step commission
        # ----------------------------------------------
        try:
            first_step_commission = int(
                first_step_text.replace(",", "")
            )
        except ValueError:
            messagebox.showwarning(
                "مبلغ نامعتبر",
                "پله اول کارمزد باید یک عدد صحیح باشد.",
                parent=self,
            )
            return
        if first_step_commission <= 0:
            messagebox.showwarning(
                "مبلغ نامعتبر",
                "پله اول کارمزد باید بیشتر از صفر باشد.",
                parent=self,
            )
            return
        db = SessionLocal()
        try:
            existing = (
                db.query(CommissionConfig)
                .filter(
                    CommissionConfig.effective_date
                    == effective_date
                )
                .first()
            )
            # ------------------------------------------
            # Edit
            # ------------------------------------------
            if self.selected_config_id is not None:
                config = (
                    db.query(CommissionConfig)
                    .filter(
                        CommissionConfig.id
                        == self.selected_config_id
                    )
                    .first()
                )
                if not config:
                    raise ValueError(
                        "رکورد انتخاب‌شده پیدا نشد."
                    )
                if (
                    existing
                    and existing.id
                    != config.id
                ):
                    raise ValueError(
                        "برای این تاریخ اثر قبلاً تنظیماتی ثبت شده است."
                    )
                config.effective_date = (
                    effective_date
                )
                config.vat = vat
                config.first_step_commission = (
                    first_step_commission
                )
            # ------------------------------------------
            # New
            # ------------------------------------------
            else:
                if existing:
                    raise ValueError(
                        "برای این تاریخ اثر قبلاً تنظیماتی ثبت شده است."
                    )
                config = CommissionConfig(
                    effective_date=effective_date,
                    vat=vat,
                    first_step_commission=(
                        first_step_commission
                    ),
                )
                db.add(config)
            db.commit()
            messagebox.showinfo(
                "موفق",
                "تنظیمات مالی با موفقیت ذخیره شد.",
                parent=self,
            )
            self.clear_form()
            self.load_data()
        except ValueError as e:
            db.rollback()
            messagebox.showwarning(
                "خطا",
                str(e),
                parent=self,
            )
        except Exception as e:
            db.rollback()
            messagebox.showerror(
                "خطا",
                f"ذخیره تنظیمات انجام نشد:\n{e}",
                parent=self,
            )
        finally:
            db.close()
    # ==================================================
    # Edit
    # ==================================================
    def on_row_double_click(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        config_id = int(selected[0])
        db = SessionLocal()
        try:
            config = (
                db.query(CommissionConfig)
                .filter(
                    CommissionConfig.id
                    == config_id
                )
                .first()
            )
            if not config:
                return
            self.selected_config_id = config.id
            # ------------------------------------------
            # تاریخ اثر
            # ------------------------------------------
            self.effective_date_entry.delete(
                0,
                tk.END,
            )
            self.effective_date_entry.insert(
                0,
                convert_date_to_shamsi(
                    config.effective_date
                ),
            )
            # ------------------------------------------
            # VAT
            # ------------------------------------------
            self.vat_entry.delete(
                0,
                tk.END,
            )
            self.vat_entry.insert(
                0,
                str(config.vat),
            )
            # ------------------------------------------
            # پله اول کارمزد
            # ------------------------------------------
            self.first_step_entry.delete(
                0,
                tk.END,
            )
            self.first_step_entry.insert(
                0,
                str(config.first_step_commission),
            )
            self.save_button.config(
                text="ویرایش تنظیمات"
            )
        finally:
            db.close()
    # ==================================================
    # Form
    # ==================================================
    def clear_form(self):
        self.selected_config_id = None
        self.effective_date_entry.delete(
            0,
            tk.END,
        )
        self.vat_entry.delete(
            0,
            tk.END,
        )
        self.first_step_entry.delete(
            0,
            tk.END,
        )
        self.save_button.config(
            text="ثبت تنظیمات"
        )
        self.tree.selection_remove(
            self.tree.selection()
        )
    # ==================================================
    # Formatting
    # ==================================================
    def _format_number(self, value):
        if value is None:
            return "۰"
        formatted = f"{int(value):,}".replace(
            ",",
            "٬",
        )
        return self._to_persian_digits(
            formatted
        )
    def _format_decimal(self, value):
        if value is None:
            return "۰"
        value = Decimal(str(value))
        if value == value.to_integral():
            text = str(
                int(value)
            )
        else:
            text = format(
                value,
                "f",
            ).rstrip("0").rstrip(".")
        return self._to_persian_digits(
            text
        )
    def _to_persian_digits(self, value):
        if value is None:
            return ""
        return str(value).translate(
            str.maketrans(
                "0123456789",
                "۰۱۲۳۴۵۶۷۸۹",
            )
        )