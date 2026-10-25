import tkinter as tk
from tkinter import filedialog, messagebox
from gui.styles import COLORS
from insurance_types import (
    import_insurance_types_from_excel
)
class InsuranceTypesAdminPage(tk.Frame):
    def __init__(
        self,
        parent,
        current_user_role,
    ):
        super().__init__(
            parent,
            bg=COLORS["background"]
        )
        self.current_user_role = current_user_role
        self._create_page()
    def _create_page(self):
        # -----------------------------
        # Header
        # -----------------------------
        tk.Label(
            self,
            text="رشته‌های بیمه و کارمزد",
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=("Tahoma", 16, "bold"),
            anchor="e",
        ).pack(
            fill="x",
            padx=30,
            pady=(25, 10),
        )
        tk.Label(
            self,
            text=(
                "اطلاعات رشته‌های بیمه، نام نمایشی، "
                "نام‌های Excel و کارمزدها از فایل Excel "
                "وارد یا به‌روزرسانی می‌شوند."
            ),
            bg=COLORS["background"],
            fg=COLORS["muted_text"],
            font=("Tahoma", 10),
            justify="right",
            anchor="e",
        ).pack(
            fill="x",
            padx=30,
            pady=(0, 20),
        )
        # -----------------------------
        # Main Card
        # -----------------------------
        card = tk.Frame(
            self,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        card.pack(
            fill="x",
            padx=30,
            pady=10,
        )
        tk.Label(
            card,
            text="به‌روزرسانی اطلاعات از Excel",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Tahoma", 12, "bold"),
            anchor="e",
        ).pack(
            fill="x",
            padx=25,
            pady=(25, 10),
        )
        tk.Label(
            card,
            text=(
                "فایل Excel شامل اطلاعات رشته‌های بیمه، "
                "نام‌های نمایشی، نام‌های Excel و کارمزدها "
                "را انتخاب کنید."
            ),
            bg=COLORS["surface"],
            fg=COLORS["muted_text"],
            font=("Tahoma", 10),
            justify="right",
            anchor="e",
        ).pack(
            fill="x",
            padx=25,
            pady=(0, 20),
        )
        self.import_button = tk.Button(
            card,
            text="ورود / به‌روزرسانی از Excel",
            command=self._import_from_excel,
            bg=COLORS["primary"],
            fg="white",
            activebackground=COLORS["primary_dark"],
            activeforeground="white",
            font=("Tahoma", 10, "bold"),
            padx=20,
            pady=10,
            relief="flat",
            cursor="hand2",
        )
        self.import_button.pack(
            anchor="e",
            padx=25,
            pady=(0, 25),
        )
        # -----------------------------
        # Status
        # -----------------------------
        self.status_label = tk.Label(
            self,
            text="",
            bg=COLORS["background"],
            fg=COLORS["success"],
            font=("Tahoma", 10),
            anchor="e",
        )
        self.status_label.pack(
            fill="x",
            padx=30,
            pady=10,
        )
    def _import_from_excel(self):
        if self.current_user_role != "مدیر سیستم":
            return
        file_path = filedialog.askopenfilename(
            title="انتخاب فایل رشته‌های بیمه و کارمزد",
            parent=self.winfo_toplevel(),
            filetypes=[
                ("فایل‌های Excel", "*.xlsx"),
                ("همه فایل‌ها", "*.*"),
            ],
        )
        # اگر کاربر پنجره را ببندد، عملیات لغو می‌شود.
        if not file_path:
            return
        try:
            self.import_button.config(state="disabled")
            self.status_label.config(
                text="در حال به‌روزرسانی اطلاعات..."
            )
            self.update_idletasks()
            import_insurance_types_from_excel(file_path)
            self.status_label.config(
                text=(
                    "اطلاعات رشته‌های بیمه و کارمزد "
                    "با موفقیت به‌روزرسانی شد."
                ),
                fg=COLORS["success"],
            )
            messagebox.showinfo(
                "موفق",
                (
                    "اطلاعات رشته‌های بیمه و کارمزد "
                    "با موفقیت وارد / به‌روزرسانی شد."
                ),
                parent=self.winfo_toplevel(),
            )
        except Exception as e:
            self.status_label.config(
                text="به‌روزرسانی اطلاعات انجام نشد.",
                fg=COLORS["danger"],
            )
            messagebox.showerror(
                "خطا",
                f"ورود اطلاعات رشته‌های بیمه انجام نشد:\n{e}",
                parent=self.winfo_toplevel(),
            )
        finally:
            self.import_button.config(state="normal")