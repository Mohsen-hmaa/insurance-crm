import tkinter as tk
from tkinter import ttk
from services.marketer_service import load_marketers
class PendingMarketerWindow:
    def __init__(
        self,
        parent,
        marketer_name,
        on_create,
        on_select,
        on_skip
    ):
        self.parent = parent
        self.marketer_name = marketer_name
        self.on_create = on_create
        self.on_select = on_select
        self.on_skip = on_skip
        self.window = tk.Toplevel(parent)
        self.window.title("بازاریاب پیدا نشد")
        self.window.geometry("450x300")
        self.create_widgets()
    def create_widgets(self):
        tk.Label(
            self.window,
            text=f"بازاریاب «{self.marketer_name}» پیدا نشد.",
            font=("Arial", 12, "bold")
        ).pack(pady=20)
        tk.Label(
            self.window,
            text="لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
        ).pack(pady=5)
        tk.Button(
            self.window,
            text="ایجاد بازاریاب جدید",
            width=30,
            command=self.create_marketer
        ).pack(pady=10)
        tk.Button(
            self.window,
            text="انتخاب بازاریاب موجود",
            width=30,
            command=self.select_marketer
        ).pack(pady=10)
        tk.Button(
            self.window,
            text="ثبت بدون بازاریاب",
            width=30,
            command=self.skip_marketer
        ).pack(pady=10)
    def create_marketer(self):
        self.on_create(self.window)
    def select_marketer(self):
        marketers = load_marketers()
        if not marketers:
            return
        self.show_marketer_selection(marketers)
    def show_marketer_selection(self, marketers):
        selection_window = tk.Toplevel(self.window)
        selection_window.title("انتخاب بازاریاب")
        selection_window.geometry("400x220")
        tk.Label(
            selection_window,
            text="بازاریاب موردنظر را انتخاب کنید:"
        ).pack(pady=20)
        marketer_combo = ttk.Combobox(
            selection_window,
            width=35,
            state="readonly",
            values=[
                marketer.name
                for marketer in marketers
            ]
        )
        marketer_combo.pack(pady=10)
        def confirm():
            selected_name = marketer_combo.get()
            if not selected_name:
                return
            selected_marketer = next(
                marketer
                for marketer in marketers
                if marketer.name == selected_name
            )
            selection_window.destroy()
            self.on_select(
                self.window,
                selected_marketer
            )
        tk.Button(
            selection_window,
            text="تأیید",
            width=20,
            command=confirm
        ).pack(pady=15)
    def skip_marketer(self):
        self.on_skip(self.window)