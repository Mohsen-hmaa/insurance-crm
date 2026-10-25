import tkinter as tk
from tkinter import messagebox
from gui.styles import COLORS
from gui.user_list import UserList
from gui.change_password import (
    open_change_password
)
class SettingsPage(tk.Frame):
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
        self._create_widgets()
    def _create_widgets(self):
        # ----------------------------------
        # Header
        # ----------------------------------
        header = tk.Frame(
            self,
            bg=COLORS["background"],
        )
        header.pack(
            fill="x",
            pady=(0, 20),
        )
        tk.Label(
            header,
            text="تنظیمات",
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=("Tahoma", 18, "bold"),
            anchor="e",
        ).pack(
            side="right",
        )
        # ----------------------------------
        # Change Password
        # ----------------------------------
        password_card = tk.Frame(
            self,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        password_card.pack(
            fill="x",
            pady=(0, 15),
        )
        tk.Label(
            password_card,
            text="امنیت حساب کاربری",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Tahoma", 12, "bold"),
            anchor="e",
        ).pack(
            fill="x",
            padx=20,
            pady=(20, 5),
        )
        tk.Label(
            password_card,
            text="تغییر کلمه عبور حساب کاربری",
            bg=COLORS["surface"],
            fg=COLORS["muted_text"],
            font=("Tahoma", 9),
            anchor="e",
        ).pack(
            fill="x",
            padx=20,
            pady=(0, 15),
        )
        tk.Button(
            password_card,
            text="تغییر کلمه عبور",
            width=24,
            bg="#CDCCCC",
            command=self._open_change_password,
        ).pack(
            anchor="e",
            padx=20,
            pady=(0, 20),
        )
        # ----------------------------------
        # User Management
        # ----------------------------------
        # فقط مدیر سیستم و مدیر این بخش را می‌بینند
        if self.current_user_role not in (
            "مدیر سیستم",
            "مدیر",
        ):
            return
        card = tk.Frame(
            self,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        card.pack(
            fill="x",
        )
        tk.Label(
            card,
            text="مدیریت کاربران",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Tahoma", 12, "bold"),
            anchor="e",
        ).pack(
            fill="x",
            padx=20,
            pady=(20, 5),
        )
        tk.Label(
            card,
            text=(
                "تعریف کاربران، تعیین نقش "
                "و مدیریت حساب‌های کاربری"
            ),
            bg=COLORS["surface"],
            fg=COLORS["muted_text"],
            font=("Tahoma", 9),
            anchor="e",
        ).pack(
            fill="x",
            padx=20,
            pady=(0, 15),
        )
        tk.Button(
            card,
            text="کاربران و دسترسی‌ها",
            width=24,
            bg="#CDCCCC",
            command=self._open_users,
        ).pack(
            anchor="e",
            padx=20,
            pady=(0, 20),
        )
    def _open_users(self):
        # بررسی امنیتی دوم
        if self.current_user_role not in (
            "مدیر سیستم",
            "مدیر",
        ):
            messagebox.showwarning(
                "عدم دسترسی",
                "شما مجوز مدیریت کاربران را ندارید.",
                parent=self,
            )
            return
        for widget in self.winfo_children():
            widget.destroy()
        user_page = UserList(
            self,
            self.current_user_role,
            self.current_user_id,
        )
        user_page.pack(
            fill="both",
            expand=True,
        )
    def _open_change_password(self):
        open_change_password(
            self.winfo_toplevel(),
            self.current_user_id,
        )