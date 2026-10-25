import tkinter as tk
from tkinter import messagebox
from gui.styles import COLORS
from gui.commission_config_page import (
    CommissionConfigPage,
)
from services.system_config_service import (
    get_current_agent,
    update_current_agent,
)
from gui.insurance_types_admin_page import (
    InsuranceTypesAdminPage
)
from gui.styles import COLORS, schedule_title_bar_color
class BasicDataPage(tk.Frame):
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
            pady=(0, 20),
        )
        tk.Label(
            header_frame,
            text="اطلاعات پایه",
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=("Tahoma", 18, "bold"),
            anchor="e",
        ).pack(
            side="right",
        )
        # ----------------------------------
        # Cards
        # ----------------------------------
        cards_frame = tk.Frame(
            self,
            bg=COLORS["background"],
        )
        cards_frame.pack(
            fill="x",
        )
        self._create_card(
            cards_frame,
            title="نمایندگی جاری",
            description=(
                "تعیین نمایندگی جاری سیستم و "
                "اطلاعات مرتبط با آن"
            ),
            command=self._open_current_agent,
        )
        self._create_card(
            cards_frame,
            title="تنظیمات مالی و کارمزد",
            description=(
                "مدیریت مالیات ارزش افزوده، کارمزد پایه و "
                "تاریخ اثر تنظیمات مالی"
            ),
            command=self._open_financial_settings,
        )
        self._create_card(
            cards_frame,
            title="رشته‌های بیمه و کارمزد",
            description=(
                "انتقال و به‌روزرسانی اطلاعات رشته‌های "
                "بیمه و کارمزد آن‌ها"
            ),
            command=self._open_insurance_types,
        )
    def _create_card(
        self,
        parent,
        title,
        description,
        command,
    ):
        card = tk.Frame(
            parent,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            cursor="hand2",
        )
        card.pack(
            fill="x",
            pady=6,
        )
        content = tk.Frame(
            card,
            bg=COLORS["surface"],
            cursor="hand2",
        )
        content.pack(
            fill="x",
            padx=20,
            pady=18,
        )
        title_label = tk.Label(
            content,
            text=title,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Tahoma", 12, "bold"),
            anchor="e",
            cursor="hand2",
        )
        title_label.pack(
            fill="x",
        )
        description_label = tk.Label(
            content,
            text=description,
            bg=COLORS["surface"],
            fg=COLORS["muted_text"],
            font=("Tahoma", 9),
            anchor="e",
            justify="right",
            cursor="hand2",
        )
        description_label.pack(
            fill="x",
            pady=(6, 0),
        )
        for widget in (
            card,
            content,
            title_label,
            description_label,
        ):
            widget.bind(
                "<Button-1>",
                lambda event: command(),
            )
    # ----------------------------------
    # Menu Actions
    # ----------------------------------
    def _open_current_agent(self):
        if self.current_user_role != "مدیر سیستم":
            return
        dialog = tk.Toplevel(self)
        dialog.title("نمایندگی جاری")
        dialog.geometry("450x220")
        schedule_title_bar_color(dialog)
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(
            bg=COLORS["background"]
        )
        # ----------------------------------
        # Title
        # ----------------------------------
        tk.Label(
            dialog,
            text="نمایندگی جاری",
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=("Tahoma", 14, "bold"),
            anchor="e",
        ).pack(
            fill="x",
            padx=30,
            pady=(25, 15),
        )
        # ----------------------------------
        # Current agent
        # ----------------------------------
        current_agent = get_current_agent()
        tk.Label(
            dialog,
            text="نام نمایندگی",
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=("Tahoma", 10),
            anchor="e",
        ).pack(
            fill="x",
            padx=30,
        )
        agent_entry = tk.Entry(
            dialog,
            font=("Tahoma", 11),
            justify="right",
        )
        agent_entry.pack(
            fill="x",
            padx=30,
            pady=(6, 20),
        )
        if current_agent:
            agent_entry.insert(
                0,
                current_agent,
            )
        # ----------------------------------
        # Buttons
        # ----------------------------------
        button_frame = tk.Frame(
            dialog,
            bg=COLORS["background"],
        )
        button_frame.pack(
            fill="x",
            padx=30,
        )
        def save():
            new_agent = agent_entry.get().strip()
            if not new_agent:
                messagebox.showwarning(
                    "ورودی نامعتبر",
                    "نام نمایندگی نمی‌تواند خالی باشد.",
                    parent=dialog,
                )
                return
            try:
                update_current_agent(
                    new_agent
                )
                messagebox.showinfo(
                    "موفق",
                    "نمایندگی جاری با موفقیت تغییر کرد.",
                    parent=dialog,
                )
                dialog.destroy()
            except ValueError as e:
                messagebox.showwarning(
                    "خطا",
                    str(e),
                    parent=dialog,
                )
            except Exception as e:
                messagebox.showerror(
                    "خطا",
                    f"ذخیره نمایندگی انجام نشد:\n{e}",
                    parent=dialog,
                )
        tk.Button(
            button_frame,
            text="ذخیره",
            command=save,
            width=12,
            bg=COLORS["primary"],
            fg="white",
            activebackground=COLORS["primary_dark"],
            activeforeground="white",
            relief="flat",
            bd=0,
            font=("Tahoma", 10),
            cursor="hand2",
        ).pack(
            side="right",
            padx=(5, 0),
        )
        tk.Button(
            button_frame,
            text="انصراف",
            command=dialog.destroy,
            width=12,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            activebackground="#E8EEF5",
            relief="flat",
            bd=0,
            font=("Tahoma", 10),
            cursor="hand2",
        ).pack(
            side="right",
        )
        agent_entry.focus_set()
    def _open_financial_settings(self):
        if self.current_user_role != "مدیر سیستم":
            return
        for widget in self.winfo_children():
            widget.destroy()
        page = CommissionConfigPage(
            self,
            self.current_user_role,
            self.current_user_id,
        )
        page.pack(
            fill="both",
            expand=True,
        )
    def _open_insurance_types(self):
        if self.current_user_role != "مدیر سیستم":
            return
        window = tk.Toplevel(
            self.winfo_toplevel()
        )
        window.title(
            "رشته‌های بیمه و کارمزد"
        )
        window.geometry(
            "750x500"
        )
        window.resizable(
            False,
            False
        )
        schedule_title_bar_color(window)
        window.transient(
            self.winfo_toplevel()
        )
        window.grab_set()
        window.configure(
            bg=COLORS["background"]
        )
        page = InsuranceTypesAdminPage(
            window,
            self.current_user_role,
        )
        page.pack(
            fill="both",
            expand=True,
        )