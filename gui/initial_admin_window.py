
import tkinter as tk
from tkinter import ttk, messagebox

from gui.styles import COLORS, FONTS, configure_styles, set_title_bar_color
from services.user_service import create_initial_admin


class InitialAdminWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ایجاد حساب اولیه")
        self.root.resizable(False, False)
        self.created = False

        configure_styles()

        self.root.configure(
            background=COLORS["background"]
        )

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self._cancel,
        )

        self._create_widgets()
        self._center_window()

        self.root.after(
            100,
            lambda: set_title_bar_color(
                self.root,
                COLORS["primary"],
            ),
        )

    def _create_widgets(self):
        container = tk.Frame(
            self.root,
            background=COLORS["surface"],
            padx=35,
            pady=30,
        )
        container.pack(
            fill="both",
            expand=True,
        )

        tk.Label(
            container,
            text="ایجاد حساب مدیر سیستم",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            font=FONTS["title"],
        ).pack(pady=(0, 8))

        tk.Label(
            container,
            text="اطلاعات حساب اولیه را وارد کنید.",
            background=COLORS["surface"],
            foreground=COLORS["muted_text"],
            font=FONTS["normal"],
        ).pack(pady=(0, 20))

        self.full_name_entry = self._add_field(
            container,
            "نام و نام خانوادگی",
        )

        self.username_entry = self._add_field(
            container,
            "نام کاربری",
        )

        self.password_entry = self._add_field(
            container,
            "رمز عبور",
            show="*",
        )

        self.confirm_password_entry = self._add_field(
            container,
            "تکرار رمز عبور",
            show="*",
        )

        ttk.Button(
            container,
            text="ایجاد حساب",
            style="Primary.TButton",
            command=self._create_account,
        ).pack(
            fill="x",
            pady=(10, 0),
        )

        self.full_name_entry.focus_set()

    def _add_field(self, parent, label_text, show=None):
        tk.Label(
            parent,
            text=label_text,
            anchor="e",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            font=FONTS["normal_bold"],
        ).pack(
            fill="x",
            pady=(0, 5),
        )

        entry = ttk.Entry(
            parent,
            width=36,
            justify="right",
            show=show,
        )
        entry.pack(
            fill="x",
            ipady=5,
            pady=(0, 12),
        )

        return entry

    def _create_account(self):
        full_name = self.full_name_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        if not all(
            (full_name, username, password, confirm_password)
        ):
            messagebox.showwarning(
                "اطلاعات ناقص",
                "تمام فیلدها را تکمیل کنید.",
                parent=self.root,
            )
            return

        if password != confirm_password:
            messagebox.showerror(
                "خطا",
                "رمز عبور و تکرار آن یکسان نیستند.",
                parent=self.root,
            )
            return

        try:
            create_initial_admin(
                full_name=full_name,
                username=username,
                password=password,
            )

            messagebox.showinfo(
                "موفقیت",
                "حساب مدیر سیستم ایجاد شد.",
                parent=self.root,
            )

            self.created = True
            self.root.destroy()

        except Exception as exc:
            messagebox.showerror(
                "خطا در ایجاد حساب",
                str(exc),
                parent=self.root,
            )

    def _center_window(self):
        self.root.update_idletasks()

        width = 430
        height = self.root.winfo_reqheight()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.root.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    def _cancel(self):
        self.root.destroy()

    def run(self):
        self.root.mainloop()
        return self.created


def run_initial_admin_setup():
    window = InitialAdminWindow()
    return window.run()
