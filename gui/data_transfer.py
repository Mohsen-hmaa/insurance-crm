import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from services.policy_import_service import (
    import_policies_from_excel,
    group_pending_marketer_policies,
    process_pending_marketer_policies
)
from services.collection_import_service import (
    import_collections_from_excel
)
from insurance_types import (
    import_insurance_types_from_excel
)
from gui.policy_assignment import (
    open_policy_assignment
)
from gui.pending_marketer import (
    PendingMarketerWindow
)
from gui.marketer_form import (
    MarketerForm
)
from models import Customer
from database import SessionLocal
from services.policy_assignment_service import (
    get_assignment_candidates_for_new_policies
)
class DataTransfer:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("انتقال اطلاعات")
        self.window.geometry("400x300")
        tk.Label(
            self.window,
            text="انتقال اطلاعات",
            font=("Arial", 14, "bold")
        ).pack(pady=30)
        self.policy_import_button = tk.Button(
            self.window,
            text="انتقال اطلاعات بیمه‌نامه‌ها",
            width=30,
            command=self.import_policies
        )
        self.policy_import_button.pack(pady=10)
        self.insurance_type_import_button = tk.Button(
            self.window,
            text="انتقال اطلاعات رشته‌های بیمه",
            width=30,
            command=self.import_insurance_types
        )
        self.insurance_type_import_button.pack(pady=10)
        self.collection_import_button = tk.Button(
            self.window,
            text="انتقال اطلاعات تسویه حق بیمه",
            width=30,
            command=self.import_collections
        )
        self.collection_import_button.pack(pady=10)
    # --------------------------------------------------
    # Loading window
    # --------------------------------------------------
    def show_loading(self, text="در حال بارگذاری اطلاعات..."):
        self.loading_window = tk.Toplevel(self.window)
        self.loading_window.title("لطفاً صبر کنید")
        self.loading_window.geometry("350x140")
        self.loading_window.transient(self.window)
        self.loading_window.resizable(False, False)
        # جلوگیری از بستن پنجره Loading
        self.loading_window.protocol(
            "WM_DELETE_WINDOW",
            lambda: None
        )
        tk.Label(
            self.loading_window,
            text=text,
            font=("Arial", 11, "bold")
        ).pack(pady=(30, 10))
        tk.Label(
            self.loading_window,
            text="لطفاً تا پایان عملیات صبر کنید..."
        ).pack()
        # غیرفعال کردن دکمه‌های انتقال اطلاعات
        self.policy_import_button.config(
            state="disabled"
        )
        self.insurance_type_import_button.config(
            state="disabled"
        )
        self.collection_import_button.config(
            state="disabled"
        )
        self.loading_window.grab_set()
        self.window.update_idletasks()
    def hide_loading(self):
        if hasattr(self, "loading_window"):
            if self.loading_window.winfo_exists():
                self.loading_window.grab_release()
                self.loading_window.destroy()
        self.policy_import_button.config(
            state="normal"
        )
        self.insurance_type_import_button.config(
            state="normal"
        )
        self.collection_import_button.config(
            state="normal"
        )
    # --------------------------------------------------
    # Import Policies
    # --------------------------------------------------
    def import_policies(self):
        file_path = filedialog.askopenfilename(
            parent=self.window,
            title="انتخاب فایل بیمه‌نامه‌ها",
            filetypes=[
                ("Excel files", "*.xlsx *.xls")
            ]
        )
        if not file_path:
            return
        self.show_loading(
            "در حال بارگذاری اطلاعات بیمه‌نامه‌ها..."
        )
        thread = threading.Thread(
            target=self._import_policies_worker,
            args=(file_path,),
            daemon=True
        )
        thread.start()
        self.window.after(
            100,
            self._check_policy_import_thread,
            thread
        )
    def _import_policies_worker(self, file_path):
        try:
            result = import_policies_from_excel(
                file_path
            )
            self.import_result = result
            self.policy_import_error = None
        except Exception as e:
            self.import_result = None
            self.policy_import_error = e
    def _check_policy_import_thread(self, thread):
        if thread.is_alive():
            self.window.after(
                100,
                self._check_policy_import_thread,
                thread
            )
            return
        # Import تمام شده
        self.hide_loading()
        if self.policy_import_error:
            messagebox.showerror(
                "خطا",
                f"انتقال اطلاعات انجام نشد:\n"
                f"{self.policy_import_error}",
                parent=self.window
            )
            return
        result = self.import_result
        pending_marketer_policies = (
            result["pending_marketer_policies"]
        )
        if pending_marketer_policies:
            grouped_pending_marketers = (
                group_pending_marketer_policies(
                    pending_marketer_policies
                )
            )
            self.process_pending_marketer_groups(
                grouped_pending_marketers
            )
        else:
            self.finish_policy_import()
    # --------------------------------------------------
    # Pending Marketers
    # --------------------------------------------------
    def process_pending_marketer_groups(
        self,
        grouped_pending_marketers
    ):
        if not grouped_pending_marketers:
            self.finish_policy_import()
            return
        marketer_name = next(
            iter(grouped_pending_marketers)
        )
        policies = grouped_pending_marketers.pop(
            marketer_name
        )
        PendingMarketerWindow(
            self.window,
            marketer_name,
            on_create=lambda pending_window:
                self.create_marketer_for_pending(
                    pending_window,
                    marketer_name,
                    policies,
                    grouped_pending_marketers
                ),
            on_select=lambda pending_window,
                selected_marketer:
                self.assign_existing_marketer(
                    pending_window,
                    selected_marketer,
                    policies,
                    grouped_pending_marketers
                ),
            on_skip=lambda pending_window:
                self.skip_pending_marketer(
                    pending_window,
                    policies,
                    grouped_pending_marketers
                )
        )
    def create_marketer_for_pending(
        self,
        pending_window,
        marketer_name,
        policies,
        remaining_groups
    ):
        MarketerForm(
            parent=pending_window,
            callback=lambda marketer:
                self.finish_pending_marketer(
                    pending_window,
                    marketer,
                    policies,
                    remaining_groups
                ),
            marketer_name=marketer_name
        )
    def assign_existing_marketer(
        self,
        pending_window,
        marketer,
        policies,
        remaining_groups
    ):
        db = SessionLocal()
        try:
            created_policies = (
                process_pending_marketer_policies(
                    db,
                    policies,
                    marketer
                )
            )
            self.import_result[
                "new_policies"
            ].extend(
                created_policies
            )
            self.import_result[
                "imported"
            ] += len(
                created_policies
            )
        except Exception as e:
            db.rollback()
            messagebox.showerror(
                "خطا",
                f"ثبت بیمه‌نامه‌ها انجام نشد:\n{e}",
                parent=pending_window
            )
            return
        finally:
            db.close()
        pending_window.destroy()
        self.process_pending_marketer_groups(
            remaining_groups
        )
    def skip_pending_marketer(
        self,
        pending_window,
        policies,
        remaining_groups
    ):
        db = SessionLocal()
        try:
            created_policies = (
                process_pending_marketer_policies(
                    db,
                    policies,
                    None
                )
            )
            self.import_result[
                "new_policies"
            ].extend(
                created_policies
            )
            self.import_result[
                "imported"
            ] += len(
                created_policies
            )
        except Exception as e:
            db.rollback()
            messagebox.showerror(
                "خطا",
                f"ثبت بیمه‌نامه‌ها انجام نشد:\n{e}",
                parent=pending_window
            )
            return
        finally:
            db.close()
        pending_window.destroy()
        self.process_pending_marketer_groups(
            remaining_groups
        )
    def finish_pending_marketer(
        self,
        pending_window,
        marketer,
        policies,
        remaining_groups
    ):
        db = SessionLocal()
        try:
            created_policies = (
                process_pending_marketer_policies(
                    db,
                    policies,
                    marketer
                )
            )
            self.import_result[
                "new_policies"
            ].extend(
                created_policies
            )
            self.import_result[
                "imported"
            ] += len(
                created_policies
            )
        except Exception as e:
            db.rollback()
            messagebox.showerror(
                "خطا",
                f"ثبت بیمه‌نامه‌ها انجام نشد:\n{e}",
                parent=pending_window
            )
            return
        finally:
            db.close()
        pending_window.destroy()
        self.process_pending_marketer_groups(
            remaining_groups
        )
    # --------------------------------------------------
    # Finish Policy Import
    # --------------------------------------------------
    def finish_policy_import(self):
        result = self.import_result
        assignment_candidates = (
            get_assignment_candidates_for_new_policies(
                result["new_policies"]
            )
        )
        result[
            "assignment_candidates"
        ] = assignment_candidates
        messagebox.showinfo(
            "موفق",
            f"انتقال اطلاعات بیمه‌نامه‌ها انجام شد.\n\n"
            f"جدید: {result['imported']}\n"
            f"تکراری: {result['duplicates']}\n"
            f"خطا: {result['errors']}",
            parent=self.window
        )
        if result["assignment_candidates"]:
            open_policy_assignment(
                self.window,
                result["assignment_candidates"]
            )
    # --------------------------------------------------
    # Insurance Types
    # --------------------------------------------------
    def import_insurance_types(self):
        self.show_loading(
            "در حال بارگذاری رشته‌های بیمه..."
        )
        thread = threading.Thread(
            target=self._import_insurance_types_worker,
            daemon=True
        )
        thread.start()
        self.window.after(
            100,
            self._check_insurance_type_thread,
            thread
        )
    def _import_insurance_types_worker(self):
        try:
            import_insurance_types_from_excel()
            self.insurance_type_import_error = None
        except Exception as e:
            self.insurance_type_import_error = e
    def _check_insurance_type_thread(self, thread):
        if thread.is_alive():
            self.window.after(
                100,
                self._check_insurance_type_thread,
                thread
            )
            return
        self.hide_loading()
        if self.insurance_type_import_error:
            messagebox.showerror(
                "خطا",
                f"انتقال اطلاعات رشته‌های بیمه انجام نشد:\n"
                f"{self.insurance_type_import_error}",
                parent=self.window
            )
        else:
            messagebox.showinfo(
                "موفق",
                "انتقال اطلاعات رشته‌های بیمه با موفقیت انجام شد.",
                parent=self.window
            )
    # --------------------------------------------------
    # Import Collections
    # --------------------------------------------------
    def import_collections(self):
        file_path = filedialog.askopenfilename(
            parent=self.window,
            title="انتخاب فایل تسویه‌ها",
            filetypes=[
                ("Excel files", "*.xlsx *.xls")
            ]
        )
        if not file_path:
            return
        self.show_loading(
            "در حال بارگذاری اطلاعات تسویه‌ها..."
        )
        thread = threading.Thread(
            target=self._import_collections_worker,
            args=(file_path,),
            daemon=True
        )
        thread.start()
        self.window.after(
            100,
            self._check_collection_thread,
            thread
        )
    def _import_collections_worker(self, file_path):
        try:
            self.collection_import_result = (
                import_collections_from_excel(
                    file_path
                )
            )
            self.collection_import_error = None
        except Exception as e:
            self.collection_import_result = None
            self.collection_import_error = e
    def _check_collection_thread(self, thread):
        if thread.is_alive():
            self.window.after(
                100,
                self._check_collection_thread,
                thread
            )
            return
        self.hide_loading()
        if self.collection_import_error:
            messagebox.showerror(
                "خطا",
                f"انتقال اطلاعات تسویه‌ها انجام نشد:\n"
                f"{self.collection_import_error}",
                parent=self.window
            )
            return
        result = self.collection_import_result
        phone_changes = result[
            "phone_changes"
        ]
        if phone_changes:
            self.show_phone_changes(
                phone_changes
            )
        messagebox.showinfo(
            "موفق",
            f"انتقال اطلاعات تسویه‌ها انجام شد.\n\n"
            f"جدید: {result['imported']}\n"
            f"تکراری: {result['duplicates']}\n"
            f"خطا: {result['errors']}",
            parent=self.window
        )
    # --------------------------------------------------
    # Phone Changes
    # --------------------------------------------------
    def show_phone_changes(
        self,
        phone_changes
    ):
        if not phone_changes:
            messagebox.showinfo(
                "تغییر شماره موبایل",
                "بررسی شماره‌های موبایل به پایان رسید.",
                parent=self.window
            )
            return
        change = phone_changes[0]
        window = tk.Toplevel(
            self.window
        )
        window.title(
            "تغییر شماره موبایل"
        )
        window.geometry(
            "400x250"
        )
        window.transient(self.window)
        window.grab_set()
        window.lift()
        window.focus_force()
        tk.Label(
            window,
            text=(
                f"{change['customer_name']} "
                f"{change['customer_family'] or ''} "
                f"{change['customer_code']}"
            )
        ).pack(
            pady=10
        )
        tk.Label(
            window,
            text=f"شماره فعلی: {change['old_phone']}"
        ).pack(
            pady=5
        )
        tk.Label(
            window,
            text=f"شماره جدید: {change['new_phone']}"
        ).pack(
            pady=5
        )
        tk.Button(
            window,
            text="تأیید تغییر",
            command=lambda:
                self.confirm_phone_change(
                    change,
                    window,
                    phone_changes
                )
        ).pack(
            pady=10
        )
        tk.Button(
            window,
            text="عدم تغییر",
            command=lambda:
                self.skip_phone_change(
                    phone_changes,
                    window
                )
        ).pack(
            pady=5
        )
    def confirm_phone_change(self, change, window, phone_changes):
        customer_id = change["customer_id"]
        new_phone = change["new_phone"]
        db = SessionLocal()
        try:
            customer_db = (
                db.query(Customer)
                .filter(Customer.id == customer_id)
                .first()
            )
            if customer_db:
                customer_db.phone = new_phone
                db.commit()
            window.destroy()
            phone_changes.pop(0)
            if phone_changes:
                self.show_phone_changes(phone_changes)
        except Exception as e:
            db.rollback()
            messagebox.showerror(
                "خطا",
                f"خطا در تغییر شماره موبایل:\n{e}",
                parent=window
            )
        finally:
            db.close()
    def skip_phone_change(
        self,
        phone_changes,
        window
    ):
        window.destroy()
        phone_changes.pop(0)
        if phone_changes:
            self.show_phone_changes(
                phone_changes
            )
def open_data_transfer(parent):
    DataTransfer(parent)