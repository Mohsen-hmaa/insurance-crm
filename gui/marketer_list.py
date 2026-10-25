import tkinter as tk
from tkinter import ttk, messagebox
from services.marketer_service import (
    load_marketers,
    has_commission_rules,
)
from gui.marketer_form import MarketerForm
from gui.marketer_commission_rule_form import (
    MarketerCommissionRuleForm,
)
from gui.agency_performance_report import AgencyPerformanceReport
from gui.styles import COLORS,schedule_title_bar_color
class MarketerList(tk.Frame):
    def __init__(self, parent, role="کاربر"):
        super().__init__(
            parent,
            bg=COLORS["background"],
        )
        self.parent = parent
        self.role = role
        self.create_widgets()
        self.load_data()
    # ==================================================
    # Main UI
    # ==================================================
    def create_widgets(self):
        # --------------------------------------------------
        # Header
        # --------------------------------------------------
        header_frame = tk.Frame(
            self,
            bg=COLORS["background"],
        )
        header_frame.pack(
            fill="x",
            pady=(0, 15),
        )
        title_label = tk.Label(
            header_frame,
            text="مدیریت بازاریاب‌ها",
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=("Tahoma", 18, "bold"),
            anchor="e",
        )
        title_label.pack(
            side="right",
        )
        # --------------------------------------------------
        # Buttons
        # --------------------------------------------------
        top_frame = tk.Frame(
            self,
            bg=COLORS["background"],
        )
        top_frame.pack(
            fill="x",
            pady=(0, 10),
        )
        new_button = tk.Button(
            top_frame,
            text="ثبت بازاریاب جدید",
            width=15,
            background="#CDCCCC",
            command=self.open_new_marketer,
        )
        new_button.pack(
            side="right",
            padx=5,
        )
        edit_button = tk.Button(
            top_frame,
            text="ویرایش",
            width=15,
            background="#CDCCCC",
            command=self.edit_marketer,
        )
        edit_button.pack(
            side="right",
            padx=5,
        )
        commission_rule_button = tk.Button(
            top_frame,
            text="قوانین کارمزد",
            width=15,
            background="#CDCCCC",
            command=self.open_commission_rules,
        )
        commission_rule_button.pack(
            side="right",
            padx=5,
        )
        report_button = tk.Button(
            top_frame,
            text="گزارش عملکرد",
            width=15,
            background="#CDCCCC",
            command=self.marketer_report,
        )
        report_button.pack(
            side="right",
            padx=5,
        )# دسترسی عملیاتی فقط برای مدیر و مدیر سیستم
        if self.role not in ("مدیر", "مدیر سیستم"):
            new_button.pack_forget()
            edit_button.pack_forget()
            commission_rule_button.pack_forget()
            report_button.pack_forget()
        # --------------------------------------------------
        # List
        # --------------------------------------------------
        list_frame = tk.Frame(
            self,
            bg=COLORS["background"],
        )
        list_frame.pack(
            fill="both",
            expand=True,
        )
        columns = (
            "status",
            "special_rules",
            "other_commission",
            "third_party_commission",
            "name",
            "id",
        )
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
        )
        self.tree.heading(
            "status",
            text="وضعیت",
        )
        self.tree.heading(
            "special_rules",
            text="قوانین خاص",
        )
        self.tree.heading(
            "other_commission",
            text="سایر کمیسیون",
        )
        self.tree.heading(
            "third_party_commission",
            text="کمیسیون ثالث",
        )
        self.tree.heading(
            "name",
            text="نام بازاریاب",
        )
        self.tree.heading(
            "id",
            text="شناسه",
        )
        self.tree.column(
            "status",
            width=70,
            anchor="e",
            stretch=True
        )
        self.tree.column(
            "special_rules",
            width=80,
            anchor="e",
            stretch=True
        )
        self.tree.column(
            "other_commission",
            width=100,
            anchor="e",
            stretch=True
        )
        self.tree.column(
            "third_party_commission",
            width=110,
            anchor="e",
            stretch=True
        )
        self.tree.column(
            "name",
            width=250,
            anchor="e",
            stretch=True
        )
        self.tree.column(
            "id",
            width=60,
            anchor="e",
            stretch=True
        )
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(
            yscrollcommand=scrollbar.set,
        )
        self.tree.pack(
            side="left",
            fill="both",
            expand=True,
        )
        scrollbar.pack(
            side="right",
            fill="y",
        )
        self.tree.bind(
            "<Double-1>",
            lambda event: self.edit_marketer(),
        )
    # ==================================================
    # Data
    # ==================================================
    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        marketers = load_marketers()
        for marketer in marketers:
            self.tree.insert(
                "",
                "end",
                values=(
                    "فعال"
                    if marketer.is_active
                    else "غیرفعال",
                    "✓"
                    if has_commission_rules(
                        marketer.id
                    )
                    else "-",
                    marketer.other_commission,
                    marketer.third_party_commission,
                    marketer.name,
                    marketer.id,
                ),
            )
    # ==================================================
    # Selection
    # ==================================================
    def get_selected_marketer(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning(
                "انتخاب بازاریاب",
                "لطفاً یک بازاریاب را انتخاب کنید.",
                parent=self,
            )
            return None
        values = self.tree.item(
            selection[0],
            "values",
        )
        marketer_id = int(values[5])
        marketers = load_marketers()
        for marketer in marketers:
            if marketer.id == marketer_id:
                return marketer
        return None
    # ==================================================
    # New Marketer
    # ==================================================
    def open_new_marketer(self):
        if self.role not in ("مدیر", "مدیر سیستم"):
            return
        MarketerForm(
            parent=self,
            callback=self.marketer_saved,
        )
    def marketer_saved(self, marketer):
        self.load_data()
    # ==================================================
    # Edit
    # ==================================================
    def edit_marketer(self):
        if self.role not in ("مدیر", "مدیر سیستم"):
            return
        marketer = self.get_selected_marketer()
        if not marketer:
            return
        MarketerForm(
            parent=self,
            marketer=marketer,
            callback=self.marketer_updated,
        )
    def marketer_updated(self, marketer):
        self.load_data()
    # ==================================================
    # Report
    # ==================================================
    def marketer_report(self):
        if self.role not in ("مدیر", "مدیر سیستم"):
            return
        marketer = self.get_selected_marketer()
        if not marketer:
            return
        marketer_value = marketer.name
        if not marketer_value:
            messagebox.showwarning(
                "گزارش عملکرد",
                "نام بازاریاب مشخص نیست.",
                parent=self,
            )
            return
        report_window = tk.Toplevel(
            self.winfo_toplevel()
        )
        report_window.title(
            f"گزارش عملکرد بازاریاب - {marketer.name}"
        )
        report_window.geometry("1200x850")
        schedule_title_bar_color(report_window)
        report = AgencyPerformanceReport(
            report_window,
            marketer_id=marketer.id,
            report_title=(
                f"گزارش عملکرد بازاریاب «{marketer.name}»"
            ),
            standalone=True,
        )
        report.pack(
            fill="both",
            expand=True,
        )
    # ==================================================
    # Commission Rules
    # ==================================================
    def open_commission_rules(self):
        if self.role not in ("مدیر", "مدیر سیستم"):
            return
        marketer = self.get_selected_marketer()
        if not marketer:
            return
        MarketerCommissionRuleForm(
            parent=self,
            marketer=marketer,
            on_saved=self.load_data,
        )
def open_marketer_list(parent):
    return MarketerList(parent)