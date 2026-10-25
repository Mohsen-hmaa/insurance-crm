import tkinter as tk
from tkinter import ttk, messagebox
from gui.styles import (
    COLORS,
    FONTS,
    set_title_bar_color,
)
from services.user_service import (
    create_user,
    update_user,
    get_manageable_roles,
)
class UserForm:
    def __init__(
        self,
        parent,
        callback,
        actor_role,
        actor_user_id,
        user=None,
    ):
        self.parent = parent
        self.callback = callback
        self.actor_role = actor_role
        self.actor_user_id = actor_user_id
        self.user = user
        self.window = tk.Toplevel(parent)
        self.window.title(
            "ثبت کاربر جدید"
            if user is None
            else "ویرایش کاربر"
        )
        self.window.resizable(
            False,
            False,
        )
        self.window.protocol(
            "WM_DELETE_WINDOW",
            self.window.destroy,
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
        self.username_entry.focus_set()
    def _create_widgets(self):
        container = tk.Frame(
            self.window,
            bg=COLORS["surface"],
            padx=35,
            pady=30,
        )
        container.pack(
            fill="both",
            expand=True,
        )
        # ---------------------------------
        # Title
        # ---------------------------------
        tk.Label(
            container,
            text=(
                "ثبت کاربر جدید"
                if self.user is None
                else "ویرایش کاربر"
            ),
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=FONTS["title"],
            anchor="e",
        ).pack(
            fill="x",
            pady=(0, 20),
        )
        # ---------------------------------
        # Full Name
        # ---------------------------------
        tk.Label(
            container,
            text="نام و نام خانوادگی",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=FONTS["normal_bold"],
            anchor="e",
        ).pack(
            fill="x",
            pady=(0, 5),
        )
        self.full_name_entry = ttk.Entry(
            container,
            width=35,
            justify="right",
        )
        self.full_name_entry.pack(
            fill="x",
            ipady=5,
            pady=(0, 15),
        )
        # ---------------------------------
        # Username
        # ---------------------------------
        tk.Label(
            container,
            text="نام کاربری",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=FONTS["normal_bold"],
            anchor="e",
        ).pack(
            fill="x",
            pady=(0, 5),
        )
        self.username_entry = ttk.Entry(
            container,
            width=35,
            justify="right",
        )
        self.username_entry.pack(
            fill="x",
            ipady=5,
            pady=(0, 15),
        )
        # ---------------------------------
        # Password
        # ---------------------------------
        tk.Label(
            container,
            text=(
                "کلمه عبور"
                if self.user is None
                else "کلمه عبور جدید (اختیاری)"
            ),
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=FONTS["normal_bold"],
            anchor="e",
        ).pack(
            fill="x",
            pady=(0, 5),
        )
        self.password_entry = ttk.Entry(
            container,
            width=35,
            show="*",
            justify="right",
        )
        self.password_entry.pack(
            fill="x",
            ipady=5,
            pady=(0, 15),
        )
        # ---------------------------------
        # Confirm Password
        # ---------------------------------
        tk.Label(
            container,
            text=(
                "تکرار کلمه عبور"
                if self.user is None
                else "تکرار کلمه عبور جدید"
            ),
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=FONTS["normal_bold"],
            anchor="e",
        ).pack(
            fill="x",
            pady=(0, 5),
        )
        self.confirm_password_entry = ttk.Entry(
            container,
            width=35,
            show="*",
            justify="right",
        )
        self.confirm_password_entry.pack(
            fill="x",
            ipady=5,
            pady=(0, 15),
        )
        # ---------------------------------
        # Role
        # ---------------------------------
        tk.Label(
            container,
            text="نقش",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=FONTS["normal_bold"],
            anchor="e",
        ).pack(
            fill="x",
            pady=(0, 5),
        )
        manageable_roles = get_manageable_roles(
            self.actor_role
        )
        self.role_combo = ttk.Combobox(
            container,
            values=manageable_roles,
            state="readonly",
            width=32,
        )
        self.role_combo.pack(
            fill="x",
            ipady=4,
            pady=(0, 15),
        )
        # ---------------------------------
        # Active
        # ---------------------------------
        self.is_active_var = tk.BooleanVar(
            master=self.window,
            value=True,
        )
        tk.Checkbutton(
            container,
            text="کاربر فعال باشد",
            variable=self.is_active_var,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            activebackground=COLORS["surface"],
            activeforeground=COLORS["text"],
            anchor="e",
        ).pack(
            fill="x",
            pady=(0, 20),
        )
        # ---------------------------------
        # Buttons
        # ---------------------------------
        button_frame = tk.Frame(
            container,
            bg=COLORS["surface"],
        )
        button_frame.pack(
            fill="x",
        )
        ttk.Button(
            button_frame,
            text="ذخیره",
            style="Primary.TButton",
            command=self._save,
        ).pack(
            side="right",
            padx=5,
        )
        tk.Button(
            button_frame,
            text="انصراف",
            width=12,
            bg="#CDCCCC",
            command=self.window.destroy,
        ).pack(
            side="right",
            padx=5,
        )
        # ---------------------------------
        # Existing user data
        # ---------------------------------
        if self.user is not None:
            self.full_name_entry.insert(
                0,
                self.user.full_name,
            )
            self.username_entry.insert(
                0,
                self.user.username,
            )
            self.role_combo.set(
                self.user.role
            )
            self.is_active_var.set(
                self.user.is_active
            )
        else:
            if manageable_roles:
                self.role_combo.current(0)
    def _save(self):
        full_name = (
            self.full_name_entry
            .get()
            .strip()
        )
        username = (
            self.username_entry
            .get()
            .strip()
        )
        password = self.password_entry.get()
        confirm_password = (
            self.confirm_password_entry.get()
        )
        role = self.role_combo.get()
        is_active = self.is_active_var.get()
        # ---------------------------------
        # Full Name validation
        # ---------------------------------
        if not full_name:
            messagebox.showwarning(
                "هشدار",
                "نام و نام خانوادگی را وارد کنید.",
                parent=self.window,
            )
            return
        # ---------------------------------
        # Username validation
        # ---------------------------------
        if not username:
            messagebox.showwarning(
                "هشدار",
                "نام کاربری را وارد کنید.",
                parent=self.window,
            )
            return
        # ---------------------------------
        # Role validation
        # ---------------------------------
        if not role:
            messagebox.showwarning(
                "هشدار",
                "یک نقش انتخاب کنید.",
                parent=self.window,
            )
            return
        # ---------------------------------
        # Password validation
        # ---------------------------------
        # ثبت کاربر جدید
        if self.user is None:
            if not password:
                messagebox.showwarning(
                    "هشدار",
                    "کلمه عبور را وارد کنید.",
                    parent=self.window,
                )
                return
            if not confirm_password:
                messagebox.showwarning(
                    "هشدار",
                    "تکرار کلمه عبور را وارد کنید.",
                    parent=self.window,
                )
                return
        # ویرایش کاربر
        # اگر یکی از دو فیلد پر شده باشد،
        # هر دو باید پر باشند.
        if self.user is not None:
            if password and not confirm_password:
                messagebox.showwarning(
                    "هشدار",
                    "تکرار کلمه عبور جدید را وارد کنید.",
                    parent=self.window,
                )
                return
            if confirm_password and not password:
                messagebox.showwarning(
                    "هشدار",
                    "کلمه عبور جدید را وارد کنید.",
                    parent=self.window,
                )
                return
        # ---------------------------------
        # Password match
        # ---------------------------------
        if password or confirm_password:
            if password != confirm_password:
                messagebox.showerror(
                    "خطا",
                    "کلمه عبور و تکرار آن یکسان نیستند.",
                    parent=self.window,
                )
                return
        try:
            # =============================
            # Create
            # =============================
            if self.user is None:
                create_user(
                    full_name,
                    username,
                    password,
                    role,
                    self.actor_role,
                )
                messagebox.showinfo(
                    "ثبت کاربر",
                    "کاربر با موفقیت ثبت شد.",
                    parent=self.window,
                )
            # =============================
            # Update
            # =============================
            else:
                update_user(
                    self.user.id,
                    full_name,
                    username,
                    role,
                    is_active,
                    self.actor_role,
                    self.actor_user_id,
                    password or None,
                )
                messagebox.showinfo(
                    "ویرایش کاربر",
                    "اطلاعات کاربر با موفقیت ذخیره شد.",
                    parent=self.window,
                )
            self.window.destroy()
            self.callback()
        except Exception as e:
            messagebox.showerror(
                "خطا",
                str(e),
                parent=self.window,
            )
    def _center_window(self):
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        screen_width = (
            self.window.winfo_screenwidth()
        )
        screen_height = (
            self.window.winfo_screenheight()
        )
        x = (
            screen_width - width
        ) // 2
        y = (
            screen_height - height
        ) // 2
        self.window.geometry(
            f"+{x}+{y}"
        )
def open_user_form(
    parent,
    callback,
    actor_role,
    actor_user_id,
    user=None,
):
    UserForm(
        parent,
        callback,
        actor_role,
        actor_user_id,
        user,
    )
