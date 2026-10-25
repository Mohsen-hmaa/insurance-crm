import tkinter as tk
from tkinter import ttk, messagebox
from gui.styles import COLORS, FONTS, set_title_bar_color
from services.user_service import authenticate_user
class LoginWindow:
    def __init__(
        self,
        parent,
        on_success,
        on_cancel,
    ):
        self.parent = parent
        self.on_success = on_success
        self.on_cancel = on_cancel
        self.window = tk.Toplevel(parent)
        self.window.title("ورود به سیستم")
        self.window.resizable(False, False)
        self.window.update_idletasks()
        self.window.protocol(
            "WM_DELETE_WINDOW",
            self._cancel,
        )
        self._create_widgets()
        self._center_window()
        self.window.after(
            100,
            lambda: set_title_bar_color(
                self.window,
                COLORS["primary"],
            ),
        )
        self.window.transient(parent)
        self.window.grab_set()
        self.username_entry.focus_set()
    def _create_widgets(self):
        self.container = tk.Frame(
            self.window,
            background=COLORS["surface"],
            padx=40,
            pady=35,
        )
        self.container.pack(
            fill="both",
            expand=True,
        )
        title = tk.Label(
            self.container,
            text="ورود به سیستم",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            font=FONTS["title"],
        )
        title.pack(
            pady=(0, 8),
        )
        subtitle = tk.Label(
            self.container,
            text="اطلاعات خود را وارد کنید",
            background=COLORS["surface"],
            foreground=COLORS["muted_text"],
            font=FONTS["normal"],
        )
        subtitle.pack(
            pady=(0, 25),
        )
        username_label = tk.Label(
            self.container,
            text="نام کاربری",
            anchor="e",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            font=FONTS["normal_bold"],
        )
        username_label.pack(
            fill="x",
            pady=(0, 5),
        )
        self.username_entry = ttk.Entry(
            self.container,
            width=35,
            justify="right",
        )
        self.username_entry.pack(
            ipady=6,
            pady=(0, 15),
        )
        password_label = tk.Label(
            self.container,
            text="کلمه عبور",
            anchor="e",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            font=FONTS["normal_bold"],
        )
        password_label.pack(
            fill="x",
            pady=(0, 5),
        )
        self.password_entry = ttk.Entry(
            self.container,
            width=35,
            show="*",
            justify="right",
        )
        self.password_entry.pack(
            ipady=6,
            pady=(0, 25),
        )
        self.login_button = ttk.Button(
            self.container,
            text="ورود",
            style="Primary.TButton",
            command=self._login,
        )
        self.login_button.pack(
            fill="x",
        )
        self.username_entry.bind(
            "<Return>",
            lambda event: self._login(),
        )
        self.password_entry.bind(
            "<Return>",
            lambda event: self._login(),
        )
    def _center_window(self):
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.window.geometry(
            f"+{x}+{y}"
        )
    def _login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showwarning(
                "ورود به سیستم",
                "نام کاربری و کلمه عبور را وارد کنید.",
                parent=self.window,
            )
            return
        user = authenticate_user(
            username,
            password,
        )
        if not user:
            messagebox.showerror(
                "ورود به سیستم",
                "نام کاربری یا کلمه عبور اشتباه است.",
                parent=self.window,
            )
            return
        self._success(user)
    def _success(self, user):
        self.window.grab_release()
        self.window.destroy()
        self.on_success(
            user["id"],
            user["username"],
            user["full_name"],
            user["role"],
        )
    def _cancel(self):
        self.window.grab_release()
        self.window.destroy()
        self.on_cancel()