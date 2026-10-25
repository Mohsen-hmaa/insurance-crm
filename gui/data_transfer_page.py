import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from database import SessionLocal
from models import Customer
from gui.pending_marketer import PendingMarketerWindow
from gui.marketer_form import MarketerForm
from gui.policy_assignment import open_policy_assignment
from gui.styles import COLORS
from services.policy_import_service import (
    import_policies_from_excel,
    group_pending_marketer_policies,
    process_pending_marketer_policies,
)
from services.collection_import_service import (
    import_collections_from_excel,
)
from services.policy_assignment_service import (
    get_assignment_candidates_for_new_policies,
)
Excel="Excel"
class DataTransferPage(tk.Frame):
    """صفحه ورود اطلاعات از فایل Excel."""
    def __init__(self, parent):
        super().__init__(
            parent,
            bg=COLORS["background"],
        )
        self.import_result = None
        self.policy_import_error = None
        self.collection_import_result = None
        self.collection_import_error = None
        self.loading_window = None
        self._create_widgets()
    # ==================================================
    # UI
    # ==================================================
    def _create_widgets(self):
        header = tk.Frame(
            self,
            bg=COLORS["background"],
        )
        header.pack(
            fill="x",
            pady=(0, 20),
        )
        tk.Label(
            header,
            text="ورود اطلاعات",
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=("Tahoma", 18, "bold"),
            anchor="e",
        ).pack(
            side="right",
        )
        tk.Label(
            header,
            text=f"{Excel} انتخاب نوع اطلاعات برای ورود از فایل",
            bg=COLORS["background"],
            fg=COLORS["muted_text"],
            font=("Tahoma", 10),
            anchor="e",
        ).pack(
            side="right",
            padx=(20, 0),
        )
        cards = tk.Frame(
            self,
            bg=COLORS["background"],
        )
        cards.pack(
            fill="x",
        )
        cards.grid_columnconfigure(0, weight=1)
        cards.grid_columnconfigure(1, weight=1)
        self._create_import_card(
            cards,
            row=0,
            column=1,
            title="ورود بیمه‌نامه‌ها از اکسل",
            description=(
                "ثبت بیمه‌نامه‌ها و الحاقیه‌ها از فایل "
                "و انجام فرآیندهای تکمیلی مربوط به بازاریاب و تخصیص"
            ),
            command=self.import_policies,
        )
        self._create_import_card(
            cards,
            row=0,
            column=0,
            title="ورود وصولی‌ها از اکسل",
            description=(
                "ثبت اطلاعات وصولی و تسویه حق بیمه از فایل  "
                "و بررسی تغییرات شماره موبایل بیمه‌گذاران"
            ),
            command=self.import_collections,
        )
    def _create_import_card(
        self,
        parent,
        row,
        column,
        title,
        description,
        command,
    ):
        card = tk.Frame(
            parent,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        card.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=8,
            pady=8,
        )
        tk.Label(
            card,
            text=title,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Tahoma", 12, "bold"),
            anchor="e",
        ).pack(
            fill="x",
            padx=20,
            pady=(22, 10),
        )
        tk.Label(
            card,
            text=description,
            bg=COLORS["surface"],
            fg=COLORS["muted_text"],
            font=("Tahoma", 9),
            anchor="e",
            justify="right",
            wraplength=420,
        ).pack(
            fill="x",
            padx=20,
            pady=(0, 18),
        )
        button = tk.Button(
            card,
            text=f"{Excel} انتخاب فایل  ←",
            command=command,
            bg="#CDCCCC",
            fg=COLORS["text"],
            activebackground="#E8EEF5",
            activeforeground=COLORS["primary"],
            relief="flat",
            bd=0,
            font=("Tahoma", 9),
            cursor="hand2",
            padx=14,
            pady=8,
        )
        button.pack(
            anchor="e",
            padx=20,
            pady=(0, 20),
        )
        # نگه داشتن دکمه‌ها برای غیرفعال کردن هنگام Loading
        if title == "ورود بیمه‌نامه‌ها از اکسل":
            self.policy_import_button = button
        elif title == "ورود وصولی‌ها از اکسل":
            self.collection_import_button = button
    # ==================================================
    # Helpers
    # ==================================================
    def _parent_window(self):
        return self.winfo_toplevel()
    # ==================================================
    # Loading
    # ==================================================
    def show_loading(
        self,
        text="در حال بارگذاری اطلاعات...",
    ):
        if (
            self.loading_window
            and self.loading_window.winfo_exists()
        ):
            return
        self.loading_window = tk.Toplevel(
            self._parent_window()
        )
        self.loading_window.title(
            "لطفاً صبر کنید"
        )
        self.loading_window.geometry(
            "350x140"
        )
        self.loading_window.transient(
            self._parent_window()
        )
        self.loading_window.resizable(
            False,
            False,
        )
        # جلوگیری از بسته شدن Loading
        self.loading_window.protocol(
            "WM_DELETE_WINDOW",
            lambda: None,
        )
        tk.Label(
            self.loading_window,
            text=text,
            font=("Tahoma", 11, "bold"),
        ).pack(
            pady=(30, 10)
        )
        tk.Label(
            self.loading_window,
            text="لطفاً تا پایان عملیات صبر کنید...",
        ).pack()
        self.policy_import_button.config(
            state="disabled"
        )
        self.collection_import_button.config(
            state="disabled"
        )
        self.loading_window.grab_set()
        self.loading_window.lift()
        self.loading_window.focus_force()
        self._parent_window().update_idletasks()
    def hide_loading(self):
        if (
            self.loading_window
            and self.loading_window.winfo_exists()
        ):
            try:
                self.loading_window.grab_release()
            except tk.TclError:
                pass
            self.loading_window.destroy()
        self.loading_window = None
        self.policy_import_button.config(
            state="normal"
        )
        self.collection_import_button.config(
            state="normal"
        )
    # ==================================================
    # Policy Import
    # ==================================================
    def import_policies(self):
        file_path = filedialog.askopenfilename(
            parent=self._parent_window(),
            title="انتخاب فایل بیمه‌نامه‌ها",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
            ],
        )
        if not file_path:
            return
        self.show_loading(
            "در حال بارگذاری اطلاعات بیمه‌نامه‌ها..."
        )
        thread = threading.Thread(
            target=self._import_policies_worker,
            args=(file_path,),
            daemon=True,
        )
        thread.start()
        self._parent_window().after(
            100,
            self._check_policy_import_thread,
            thread,
        )
    def _import_policies_worker(
        self,
        file_path,
    ):
        try:
            result = import_policies_from_excel(
                file_path
            )
            self.import_result = result
            self.policy_import_error = None
        except Exception as e:
            self.import_result = None
            self.policy_import_error = e
    def _check_policy_import_thread(
        self,
        thread,
    ):
        if thread.is_alive():
            self._parent_window().after(
                100,
                self._check_policy_import_thread,
                thread,
            )
            return
        self.hide_loading()
        if self.policy_import_error:
            messagebox.showerror(
                "خطا",
                f"ورود اطلاعات بیمه‌نامه‌ها انجام نشد:\n"
                f"{self.policy_import_error}",
                parent=self._parent_window(),
            )
            return
        result = self.import_result
        pending_marketer_policies = result.get(
            "pending_marketer_policies",
            [],
        )
        if pending_marketer_policies:
            grouped_pending_marketers = (
                group_pending_marketer_policies(
                    pending_marketer_policies,
                )
            )
            self.process_pending_marketer_groups(
                grouped_pending_marketers
            )
        else:
            self.finish_policy_import()
    # ==================================================
    # Pending Marketers
    # ==================================================
    def process_pending_marketer_groups(
        self,
        grouped_pending_marketers,
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
            self._parent_window(),
            marketer_name,
            on_create=lambda pending_window:
                self.create_marketer_for_pending(
                    pending_window,
                    marketer_name,
                    policies,
                    grouped_pending_marketers,
                ),
            on_select=lambda pending_window,
                selected_marketer:
                self.assign_existing_marketer(
                    pending_window,
                    selected_marketer,
                    policies,
                    grouped_pending_marketers,
                ),
            on_skip=lambda pending_window:
                self.skip_pending_marketer(
                    pending_window,
                    policies,
                    grouped_pending_marketers,
                ),
        )
    def create_marketer_for_pending(
        self,
        pending_window,
        marketer_name,
        policies,
        remaining_groups,
    ):
        MarketerForm(
            parent=pending_window,
            callback=lambda marketer:
                self.finish_pending_marketer(
                    pending_window,
                    marketer,
                    policies,
                    remaining_groups,
                ),
            marketer_name=marketer_name,
        )
    def assign_existing_marketer(
        self,
        pending_window,
        marketer,
        policies,
        remaining_groups,
    ):
        db = SessionLocal()
        try:
            created_policies = (
                process_pending_marketer_policies(
                    db,
                    policies,
                    marketer,
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
                parent=pending_window,
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
        remaining_groups,
    ):
        db = SessionLocal()
        try:
            created_policies = (
                process_pending_marketer_policies(
                    db,
                    policies,
                    None,
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
                parent=pending_window,
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
        remaining_groups,
    ):
        db = SessionLocal()
        try:
            created_policies = (
                process_pending_marketer_policies(
                    db,
                    policies,
                    marketer,
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
                parent=pending_window,
            )
            return
        finally:
            db.close()
        pending_window.destroy()
        self.process_pending_marketer_groups(
            remaining_groups
        )
    # ==================================================
    # Finish Policy Import
    # ==================================================
    def finish_policy_import(self):
        result = self.import_result
        try:
            assignment_candidates = (
                get_assignment_candidates_for_new_policies(
                    result["new_policies"]
                )
            )
            result[
                "assignment_candidates"
            ] = assignment_candidates
        except Exception as e:
            messagebox.showerror(
                "خطا",
                "ورود بیمه‌نامه‌ها انجام شد، "
                "اما در بررسی تخصیص بیمه‌نامه‌ها خطایی رخ داد:\n\n"
                f"{e}",
                parent=self._parent_window(),
            )
            return
        messagebox.showinfo(
            "موفق",
            f"ورود اطلاعات بیمه‌نامه‌ها انجام شد.\n\n"
            f"جدید: {result['imported']}\n"
            f"تکراری: {result['duplicates']}\n"
            f"خطا: {result['errors']}",
            parent=self._parent_window(),
        )
        if result["assignment_candidates"]:
            open_policy_assignment(
                self._parent_window(),
                result["assignment_candidates"],
            )
    # ==================================================
    # Collection Import
    # ==================================================
    def import_collections(self):
        file_path = filedialog.askopenfilename(
            parent=self._parent_window(),
            title="انتخاب فایل وصولی‌ها",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
            ],
        )
        if not file_path:
            return
        self.show_loading(
            "در حال بارگذاری اطلاعات وصولی‌ها..."
        )
        thread = threading.Thread(
            target=self._import_collections_worker,
            args=(file_path,),
            daemon=True,
        )
        thread.start()
        self._parent_window().after(
            100,
            self._check_collection_thread,
            thread,
        )
    def _import_collections_worker(
        self,
        file_path,
    ):
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
    def _check_collection_thread(
        self,
        thread,
    ):
        if thread.is_alive():
            self._parent_window().after(
                100,
                self._check_collection_thread,
                thread,
            )
            return
        self.hide_loading()
        if self.collection_import_error:
            messagebox.showerror(
                "خطا",
                f"ورود اطلاعات وصولی‌ها انجام نشد:\n"
                f"{self.collection_import_error}",
                parent=self._parent_window(),
            )
            return
        result = self.collection_import_result
        phone_changes = result.get(
            "phone_changes",
            [],
        )
        if phone_changes:
            self.show_phone_changes(
                phone_changes
            )
        messagebox.showinfo(
            "موفق",
            f"ورود اطلاعات وصولی‌ها انجام شد.\n\n"
            f"جدید: {result['imported']}\n"
            f"تکراری: {result['duplicates']}\n"
            f"خطا: {result['errors']}",
            parent=self._parent_window(),
        )
    # ==================================================
    # Phone Changes
    # ==================================================
    def show_phone_changes(
        self,
        phone_changes,
    ):
        if not phone_changes:
            return
        change = phone_changes[0]
        customer_name = (
            f"{change.get('customer_name', '')} "
            f"{change.get('customer_family', '')}"
        ).strip()
        customer_code = change.get("customer_code", "")
        window = tk.Toplevel(
            self._parent_window()
        )
        window.title(
            "تغییر شماره موبایل"
        )
        window.geometry(
            "400x250"
        )
        window.transient(
            self._parent_window()
        )
        window.grab_set()
        window.lift()
        window.focus_force()
        tk.Label(
            window,
            text=f"{customer_name}  {customer_code}".strip(),
            font=("Tahoma", 10, "bold"),
        ).pack(
            pady=12
        )
        tk.Label(
            window,
            text=f"شماره فعلی: {change['old_phone']}",
        ).pack(
            pady=5
        )
        tk.Label(
            window,
            text=f"شماره جدید: {change['new_phone']}",
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
                    phone_changes,
                ),
        ).pack(
            pady=10
        )
        tk.Button(
            window,
            text="عدم تغییر",
            command=lambda:
                self.skip_phone_change(
                    phone_changes,
                    window,
                ),
        ).pack(
            pady=5
        )
    def confirm_phone_change(
        self,
        change,
        window,
        phone_changes,
    ):
        new_phone = change["new_phone"]
        db = SessionLocal()
        try:
            customer_db = (
                db.query(Customer)
                .filter(
                    Customer.id == change["customer_id"]
                )
                .first()
            )
            if not customer_db:
                raise ValueError("بیمه‌گذار در دیتابیس پیدا نشد.")
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
                f"تغییر شماره موبایل انجام نشد:\n{e}",
                parent=window,
            )
        finally:
            db.close()
    def skip_phone_change(
        self,
        phone_changes,
        window,
    ):
        window.destroy()
        phone_changes.pop(0)
        if phone_changes:
            self.show_phone_changes(
                phone_changes
            )
