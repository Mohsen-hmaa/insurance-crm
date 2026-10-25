import tkinter as tk
from tkinter import ttk, messagebox
from gui.styles import COLORS
from gui.user_form import open_user_form
from services.user_service import (
    load_users,
    get_user_by_id,
    can_manage_role,
    get_manageable_roles,
    delete_user,
)
class UserList(tk.Frame):
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
        self.create_widgets()
        self.load_data()
    def create_widgets(self):
        # ----------------------------------
        # Header
        # ----------------------------------
        header_frame = tk.Frame(
            self,
            bg=COLORS["background"],
        )
        header_frame.pack(
            fill="x",
            pady=(0, 15),
        )
        tk.Label(
            header_frame,
            text="کاربران و دسترسی‌ها",
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=("Tahoma", 18, "bold"),
            anchor="e",
        ).pack(
            side="right",
        )
        # ----------------------------------
        # Table
        # ----------------------------------
        table_frame = tk.Frame(
            self,
            bg=COLORS["background"],
        )
        table_frame.pack(
            fill="both",
            expand=True,
        )
        self.user_tree = ttk.Treeview(
            table_frame,
            columns=(
                "status",
                "role",
                "username",
            ),
            show="headings",
        )
        self.user_tree.heading(
            "status",
            text="وضعیت",
            anchor="center",
        )
        self.user_tree.heading(
            "role",
            text="نقش",
            anchor="e",
        )
        self.user_tree.heading(
            "username",
            text="نام کاربری",
            anchor="e",
        )
        self.user_tree.column(
            "status",
            width=100,
            minwidth=80,
            anchor="center",
            stretch=True,
        )
        self.user_tree.column(
            "role",
            width=180,
            minwidth=130,
            anchor="e",
            stretch=True,
        )
        self.user_tree.column(
            "username",
            width=200,
            minwidth=140,
            anchor="e",
            stretch=True,
        )
        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.user_tree.yview,
        )
        self.user_tree.configure(
            yscrollcommand=scrollbar.set,
        )
        self.user_tree.grid(
            row=0,
            column=0,
            sticky="nsew",
        )
        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )
        table_frame.grid_rowconfigure(
            0,
            weight=1,
        )
        table_frame.grid_columnconfigure(
            0,
            weight=1,
        )
        # ----------------------------------
        # Buttons
        # ----------------------------------
        button_frame = tk.Frame(
            self,
            bg=COLORS["background"],
        )
        button_frame.pack(
            fill="x",
            pady=(15, 0),
        )
        self.add_button = tk.Button(
            button_frame,
            text="ثبت کاربر جدید",
            command=self.add_user,
            width=20,
            bg="#CDCCCC",
        )
        self.add_button.pack(
            side="right",
            padx=5,
        )
        self.edit_button = tk.Button(
            button_frame,
            text="ویرایش کاربر",
            command=self.edit_user,
            width=20,
            bg="#CDCCCC",
        )
        self.edit_button.pack(
            side="right",
            padx=5,
        )
        if self.current_user_role == "مدیر سیستم":
            self.delete_button = tk.Button(
                button_frame,
                text="حذف کاربر",
                command=self.delete_user,
                width=20,
                bg="#CDCCCC",
            )
            self.delete_button.pack(
                side="right",
                padx=5,
            )
    def load_data(self):
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        users = load_users(
            self.current_user_role
        )
        for user in users:
            self.user_tree.insert(
                "",
                "end",
                iid=str(user.id),
                values=(
                    "فعال"
                    if user.is_active
                    else "غیرفعال",
                    user.role,
                    user.username,
                ),
            )
    def _get_selected_user(self):
        selected = self.user_tree.selection()
        if not selected:
            messagebox.showwarning(
                "هشدار",
                "لطفاً یک کاربر را انتخاب کنید.",
                parent=self,
            )
            return None
        try:
            user_id = int(selected[0])
        except (
            ValueError,
            TypeError,
        ):
            messagebox.showerror(
                "خطا",
                "شناسه کاربر معتبر نیست.",
                parent=self,
            )
            return None
        user = get_user_by_id(user_id)
        if not user:
            messagebox.showerror(
                "خطا",
                "کاربر پیدا نشد.",
                parent=self,
            )
            return None
        return user
    def add_user(self):
        if not get_manageable_roles(
            self.current_user_role
        ):
            messagebox.showwarning(
                "عدم دسترسی",
                "شما امکان ایجاد کاربر جدید ندارید.",
                parent=self,
            )
            return
        open_user_form(
            self,
            self.load_data,
            self.current_user_role,
            self.current_user_id,
        )
    def edit_user(self):
        user = self._get_selected_user()
        if not user:
            return
        # جلوگیری از ویرایش حساب خود کاربر
        if user.id == self.current_user_id:
            messagebox.showwarning(
                "عدم دسترسی",
                "نمی‌توانید حساب کاربری خودتان را از این بخش ویرایش کنید.",
                parent=self,
            )
            return
        # بررسی سطح دسترسی
        if not can_manage_role(
            self.current_user_role,
            user.role,
        ):
            messagebox.showwarning(
                "عدم دسترسی",
                "شما اجازه ویرایش این کاربر را ندارید.",
                parent=self,
            )
            return
        open_user_form(
            self,
            self.load_data,
            self.current_user_role,
            self.current_user_id,
            user,
        )
    def delete_user(self):
        if self.current_user_role != "مدیر سیستم":
            messagebox.showwarning(
                "عدم دسترسی",
                "فقط مدیر سیستم اجازه حذف کاربر را دارد.",
                parent=self,
            )
            return
        user = self._get_selected_user()
        if not user:
            return
        if user.id == self.current_user_id:
            messagebox.showwarning(
                "عدم دسترسی",
                "نمی‌توانید حساب کاربری خودتان را حذف کنید.",
                parent=self,
            )
            return
        confirm = messagebox.askyesno(
            "تأیید حذف",
            (
                f"آیا از حذف کاربر «{user.full_name}» "
                f"با نام کاربری «{user.username}» مطمئن هستید؟"
            ),
            parent=self,
        )
        if not confirm:
            return
        try:
            delete_user(
                user.id,
                self.current_user_role,
                self.current_user_id,
            )
            messagebox.showinfo(
                "موفق",
                "کاربر با موفقیت حذف شد.",
                parent=self,
            )
            self.load_data()
        except PermissionError as e:
            messagebox.showwarning(
                "عدم دسترسی",
                str(e),
                parent=self,
            )
        except ValueError as e:
            messagebox.showerror(
                "خطا",
                str(e),
                parent=self,
            )
        except Exception as e:
            messagebox.showerror(
                "خطا",
                f"حذف کاربر انجام نشد:\n{e}",
                parent=self,
            )
def open_user_list(
    parent,
    current_user_role,
    current_user_id,
):
    return UserList(
        parent,
        current_user_role,
        current_user_id,
    )
