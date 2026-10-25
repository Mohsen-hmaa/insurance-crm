import tkinter as tk
from tkinter import ttk,messagebox
from services.policy_assignment_service import (
    assign_marketer,
    assign_referrer
)
from services.date_service import convert_date_to_shamsi
class PolicyAssignment:
    def __init__(self, parent, assignment_candidates):
        self.window = tk.Toplevel(parent)
        self.window.title("تکمیل اطلاعات بیمه‌نامه‌ها")
        self.window.geometry("1200x600")
        self.assignment_candidates = assignment_candidates
        self.current_index = 0
        # وضعیت انتخاب هر ردیف
        self.selected_items = {}
        self.item_policy_map = {}
        # وضعیت انتخاب همه
        self.select_all_var = tk.BooleanVar(value=False)
        self.create_widgets()
    def create_widgets(self):
        self.customer_label = tk.Label(
            self.window,
            text="",
            font=("Arial", 14, "bold")
        )
        self.customer_label.pack(pady=15)
        table_frame = tk.Frame(self.window)
        table_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )
        columns = (
            "suggestion",
            "referrer",
            "marketer",
            "issue_date",
            "policy_number",
            "customer",
            "computer_code",
            "select"
        )
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )
        headers = {
            "suggestion": "پیشنهاد",
            "referrer": "معرف",
            "marketer": "بازاریاب",
            "issue_date": "تاریخ صدور",
            "policy_number": "شماره بیمه",
            "customer": "بیمه‌گذار",
            "computer_code": "کد رایانه",
            "select": "انتخاب همه"
        }
        widths = {
            "suggestion": 250,
            "referrer": 10,
            "marketer": 10,
            "issue_date": 50,
            "policy_number": 50,
            "customer": 220,
            "computer_code": 50,
            "select": 50
        }
        for column, text in headers.items():
            if column == "select":
                self.tree.heading(
                    column,
                    text="☐ انتخاب همه",
                    anchor="center"
                )
            else:
                self.tree.heading(
                    column,
                    text=text,
                    anchor="e"
                )
            self.tree.column(
                column,
                width=widths[column],
                anchor="center" if column == "select" else "e"
            )
        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(
            yscrollcommand=scrollbar.set
        )
        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )
        scrollbar.pack(
            side="right",
            fill="y"
        )
        # کلیک روی جدول
        self.tree.bind(
            "<Button-1>",
            self.on_tree_click
        )
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=10)
        self.next_button = tk.Button(
            button_frame,
            text="تأیید و ادامه",
            background="#CDCCCC",
            width=18,
            command=self.confirm_selection
        )
        self.next_button.pack(
            side="right",
            padx=20
        )
        self.cancel_button = tk.Button(
            button_frame,
            text="انصراف",
            background="#CDCCCC",
            width=18,
            command=self.window.destroy
        )
        self.cancel_button.pack(
            side="right",
            padx=20
        )
        self.show_current_customer()
    def on_tree_click(self, event):
        region = self.tree.identify(
            "region",
            event.x,
            event.y
        )
        column = self.tree.identify_column(event.x)
        # کلیک روی سرتیتر ستون انتخاب
        if region == "heading" and column == "#8":
            new_value = not self.select_all_var.get()
            self.select_all_var.set(new_value)
            self.toggle_select_all()
            return
        # از اینجا به بعد فقط کلیک روی سلول‌ها
        if region != "cell":
            return
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        # کلیک روی ستون انتخاب
        if column == "#8":
            current_value = self.selected_items.get(
                item_id,
                False
            )
            new_value = not current_value
            self.selected_items[item_id] = new_value
            self.tree.set(
                item_id,
                "select",
                "☑" if new_value else "☐"
            )
            self.update_select_all_state()
    def update_select_all_state(self):
        items = self.tree.get_children()
        if not items:
            return
        all_selected = all(
            self.selected_items.get(item_id, False)
            for item_id in items
        )
        self.select_all_var.set(all_selected)
        self.tree.heading(
            "select",
            text="☑ انتخاب همه" if all_selected else "☐ انتخاب همه",
            anchor="center"
        )
    def toggle_select_all(self):
        value = self.select_all_var.get()
        for item_id in self.tree.get_children():
            self.selected_items[item_id] = value
            self.tree.set(
                item_id,
                "select",
                "☑" if value else "☐"
            )
        self.tree.heading(
            "select",
            text="☑ انتخاب همه" if value else "☐ انتخاب همه",
            anchor="center"
        )
    def show_current_customer(self):
        if not self.assignment_candidates:
            self.customer_label.config(
                text="مشتری‌ای برای بررسی وجود ندارد"
            )
            return
        customer_data = self.assignment_candidates[
            self.current_index
        ]
        policies = [
            item["policy"]
            for item in customer_data["marketer_candidates"]
        ] + [
            item["policy"]
            for item in customer_data["referrer_candidates"]
        ]
        if policies:
            customer_name = policies[0].customer.name
            customer_family=policies[0].customer.family
            customer_code=policies[0].customer.customer_code
        else:
            customer_name = "نامشخص"
        self.customer_label.config(
            text=f"بیمه‌گذار: {customer_name} {customer_family or ""}   |    کد مشتری: {customer_code}"
        )
        # پاک کردن اطلاعات قبلی جدول
        for item in self.tree.get_children():
            self.tree.delete(item)
        # پاک کردن وضعیت چک‌باکس‌ها
        self.selected_items.clear()
        self.item_policy_map.clear()
        self.select_all_var.set(False)
        self.tree.heading(
            "select",
            text="☐ انتخاب همه",
            anchor="center"
        )
        # فعلاً همه بیمه‌نامه‌های این مشتری را نمایش می‌دهیم
        for policy in policies:
            suggestion = ""
            for item in customer_data["marketer_candidates"]:
                if item["policy"].id == policy.id:
                    suggestion = (
                        f"بازاریاب: {item['suggested_marketer'].name}"
                    )
                    break
            if not suggestion:
                for item in customer_data["referrer_candidates"]:
                    if item["policy"].id == policy.id:
                        suggestion = (
                            f"معرف: {item['suggested_referrer']}"
                        )
                        break
            item_id = self.tree.insert(
                "",
                "end",
                values=(
                    suggestion,
                    policy.referrer or "",
                    policy.marketer.name if policy.marketer else "",
                    convert_date_to_shamsi(policy.issue_date) or "",
                    policy.policy_number or "",
                    f" {policy.customer.name} {policy.customer.family or ''} {policy.customer.customer_code}"
                    if policy.customer else "",
                    policy.computer_code or "",
                    "☐"
                )
            )
            self.item_policy_map[item_id] = policy.id
    def confirm_selection(self):
        selected_policies = []
        for item_id, selected in self.selected_items.items():
            if not selected:
                continue
            policy_id = self.item_policy_map.get(item_id)
            if policy_id is None:
                continue
            policy = next(
                (
                    policy
                    for policy in self.assignment_candidates[
                        self.current_index
                    ]["policies"]
                    if policy.id == policy_id
                ),
                None
            )
            if policy is None:
                continue
            suggestion = ""
            for item in self.assignment_candidates[
                self.current_index
            ]["marketer_candidates"]:
                if item["policy"].id == policy.id:
                    suggestion = (
                        "marketer",
                        item["suggested_marketer"]
                    )
                    break
            if not suggestion:
                for item in self.assignment_candidates[
                    self.current_index
                ]["referrer_candidates"]:
                    if item["policy"].id == policy.id:
                        suggestion = (
                            "referrer",
                            item["suggested_referrer"]
                        )
                        break
            selected_policies.append((policy, suggestion))
        for policy, suggestion in selected_policies:
            if not suggestion:
                continue
            suggestion_type, suggestion_value = suggestion
            if suggestion_type == "marketer":
                assign_marketer([policy], suggestion_value)
            elif suggestion_type == "referrer":
                assign_referrer([policy], suggestion_value)
        self.current_index += 1
        if self.current_index >= len(self.assignment_candidates):
            messagebox.showinfo(
                "پایان بررسی",
                "تمام بیمه‌نامه‌های نیازمند تکمیل بررسی شدند.",
                parent=self.window,
            )
            self.window.destroy()
            return
        self.show_current_customer()
def open_policy_assignment(parent, assignment_candidates):
    return PolicyAssignment(
        parent,
        assignment_candidates
    )