import tkinter as tk
from tkinter import messagebox
from gui.styles import COLORS,schedule_title_bar_color
from services.user_service import change_password
class ChangePasswordDialog:
    def __init__(
        self,
        parent,
        user_id,
    ):
        self.user_id = user_id
        self.window = tk.Toplevel(
            parent
        )
        self.window.title(
            "تغییر کلمه عبور"
        )
        self.window.geometry(
            "430x330"
        )
        schedule_title_bar_color(self.window)
        self.window.resizable(
            False,
            False
        )
        self.window.transient(
            parent
        )
        self.window.grab_set()
        self.window.configure(
            bg=COLORS["background"]
        )
        self._create_widgets()
    def _create_widgets(self):
        tk.Label(
            self.window,
            text="تغییر کلمه عبور",
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=("Tahoma", 14, "bold"),
        ).pack(
            pady=(25, 20)
        )
        # رمز فعلی
        tk.Label(
            self.window,
            text="کلمه عبور فعلی",
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=("Tahoma", 10),
            anchor="e",
        ).pack(
            fill="x",
            padx=40,
        )
        self.current_password_entry = tk.Entry(
            self.window,
            show="*",
            justify="left",
            font=("Tahoma", 11),
        )
        self.current_password_entry.pack(
            fill="x",
            padx=40,
            pady=(5, 15),
        )
        # رمز جدید
        tk.Label(
            self.window,
            text="کلمه عبور جدید",
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=("Tahoma", 10),
            anchor="e",
        ).pack(
            fill="x",
            padx=40,
        )
        self.new_password_entry = tk.Entry(
            self.window,
            show="*",
            justify="left",
            font=("Tahoma", 11),
        )
        self.new_password_entry.pack(
            fill="x",
            padx=40,
            pady=(5, 15),
        )
        # تکرار رمز جدید
        tk.Label(
            self.window,
            text="تکرار کلمه عبور جدید",
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=("Tahoma", 10),
            anchor="e",
        ).pack(
            fill="x",
            padx=40,
        )
        self.confirm_password_entry = tk.Entry(
            self.window,
            show="*",
            justify="left",
            font=("Tahoma", 11),
        )
        self.confirm_password_entry.pack(
            fill="x",
            padx=40,
            pady=(5, 20),
        )
        button_frame = tk.Frame(
            self.window,
            bg=COLORS["background"]
        )
        button_frame.pack(
            fill="x",
            padx=40,
        )
        tk.Button(
            button_frame,
            text="تغییر کلمه عبور",
            command=self._save,
            bg=COLORS["primary"],
            fg="white",
            activebackground=COLORS["primary_dark"],
            activeforeground="white",
            font=("Tahoma", 10, "bold"),
            relief="flat",
            padx=15,
            pady=8,
            cursor="hand2",
        ).pack(
            side="right"
        )
        tk.Button(
            button_frame,
            text="انصراف",
            command=self.window.destroy,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Tahoma", 10),
            relief="flat",
            padx=15,
            pady=8,
            cursor="hand2",
        ).pack(
            side="right",
            padx=(0, 8),
        )
        self.current_password_entry.focus_set()
    def _save(self):
        current_password = (
            self.current_password_entry
            .get()
        )
        new_password = (
            self.new_password_entry
            .get()
        )
        confirm_password = (
            self.confirm_password_entry
            .get()
        )
        try:
            change_password(
                user_id=self.user_id,
                current_password=current_password,
                new_password=new_password,
                confirm_password=confirm_password,
            )
            messagebox.showinfo(
                "موفق",
                "کلمه عبور با موفقیت تغییر کرد.",
                parent=self.window,
            )
            self.window.destroy()
        except ValueError as e:
            messagebox.showwarning(
                "خطا",
                str(e),
                parent=self.window,
            )
        except Exception as e:
            messagebox.showerror(
                "خطا",
                f"تغییر کلمه عبور انجام نشد:\n{e}",
                parent=self.window,
            )
def open_change_password(
    parent,
    user_id,
):
    ChangePasswordDialog(
        parent,
        user_id,
    )