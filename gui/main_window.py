import tkinter as tk
from tkinter import ttk, messagebox
from tkinter_icons import LucideIcon
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from gui.login_window import LoginWindow
from gui.customer_list import CustomerList
from gui.policy_list import PolicyList
from gui.settings_page import SettingsPage
from gui.basic_data_page import BasicDataPage
from gui.marketer_list import (
    MarketerList,
)
from gui.data_transfer_page import DataTransferPage
from services.permissions_service import can_access_menu
from gui.reports_page import ReportsPage
from gui.styles import (
    COLORS,
    FONTS,
    configure_styles,
    set_title_bar_color,
)
from services.dashboard_service import (
    get_dashboard_data,
)
from services.system_config_service import (
    get_current_agent,
)
from services.date_service import (
    convert_date_to_shamsi,
)
from services.policy_assignment_service import (
    get_all_assignment_candidates,
)
from gui.policy_assignment import (
    open_policy_assignment,
)
class MainWindow:
    def __init__(self):
        self.current_username = None
        self.current_role = None
        self.current_user_id = None
        self.current_full_name = None
        self.window = tk.Tk()
        self.active_menu = None
        # داده‌های داشبورد بعد از اولین بارگذاری
        self.dashboard_data = None
        self.window.title(
            "Insurance CRM"
        )
        self.window.configure(
            background=COLORS["background"]
        )
        self.window.protocol(
            "WM_DELETE_WINDOW",
            self._on_close,
        )
        set_title_bar_color(
            self.window,
            COLORS["primary"],
        )
        configure_styles()
        self._create_widgets()
        self._set_full_window()
    # ==================================================
    # Window
    # ==================================================
    def _set_full_window(self):
        self.window.state("zoomed")
    # ==================================================
    # Main UI
    # ==================================================
    def _create_widgets(self):
        self._create_header()
        self._create_content()
    def _create_header(self):
        current_agent = get_current_agent()
        self.header = tk.Frame(
            self.window,
            bg=COLORS["primary"],
            height=78,
        )
        self.header.pack(
            side="top",
            fill="x",
        )
        self.header.pack_propagate(False)
        title = tk.Label(
            self.header,
            text="Insurance CRM",
            bg=COLORS["primary"],
            fg="white",
            font=("Tahoma", 18, "bold"),
            anchor="e",
        )
        title.pack(
            side="right",
            padx=(30, 15),
        )
        subtitle = tk.Label(
            self.header,
            text=(
                f"سیستم مدیریت ارتباط با مشتری "
                f"نمایندگی {current_agent}"
            ),
            bg=COLORS["primary"],
            fg="#DCE6F1",
            font=("Tahoma", 10),
            anchor="e",
        )
        subtitle.pack(
            side="right",
            padx=(0, 30),
        )
    def _create_content(self):
        self.content = tk.Frame(
            self.window,
            bg=COLORS["background"],
        )
        self.content.pack(
            fill="both",
            expand=True,
        )
        self._create_sidebar()
        self._create_main_area()
    # ==================================================
    # Sidebar
    # ==================================================
    def _create_sidebar(self):
        self.sidebar = tk.Frame(
            self.content,
            bg=COLORS["surface"],
            width=250,
        )
        self.sidebar.pack(
            side="right",
            fill="y",
        )
        self.sidebar.pack_propagate(False)
        sidebar_title = tk.Label(
            self.sidebar,
            text="منوی اصلی",
            bg=COLORS["surface"],
            fg=COLORS["muted_text"],
            font=("Tahoma", 10, "bold"),
            anchor="e",
        )
        sidebar_title.pack(
            fill="x",
            padx=20,
            pady=(25, 15),
        )
        self.menu_buttons = {}
        self._create_menu_button(
            text="داشبورد",
            icon="layout-dashboard",
            command=self._show_dashboard,
        )
        self._create_menu_button(
            text="بیمه‌گذاران",
            icon="users",
            command=self._open_customers,
        )
        self._create_menu_button(
            text="بیمه‌نامه‌ها",
            icon="file-text",
            command=self._open_policies,
        )
        self.menu_buttons["marketers"] = self._create_menu_button(
            text="بازاریابان",
            icon="briefcase-business",
            command=self._open_marketers,
        )
        self.menu_buttons["assignment"] = self._create_menu_button(
            text="تکمیل و بررسی بیمه‌نامه‌ها",
            icon="clipboard-check",
            command=self.open_manual_assignment,
        )
        self._create_menu_button(
            text="گزارش‌ها",
            icon="chart-column",
            command=self._open_reports,
        )
        self.menu_buttons["import"] = self._create_menu_button(
            text="ورود اطلاعات",
            icon="upload",
            command=self._open_import,
        )
        self.menu_buttons["basic_data"] = self._create_menu_button(
            text="اطلاعات پایه",
            icon="database",
            command=self._open_basic_data,
        )
        self.settings_button = self._create_menu_button(
            text="تنظیمات",
            icon="settings",
            command=self._open_settings,
        )
        spacer = tk.Frame(
            self.sidebar,
            bg=COLORS["surface"],
        )
        spacer.pack(
            fill="both",
            expand=True,
        )
        separator = tk.Frame(
            self.sidebar,
            bg=COLORS["border"],
            height=1,
        )
        separator.pack(
            fill="x",
            padx=15,
            pady=(10, 15),
        )
        self.user_label = tk.Label(
            self.sidebar,
            text="",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Tahoma", 10),
            anchor="e",
            justify="right",
        )
        self.user_label.pack(
            fill="x",
            padx=20,
            pady=(0, 10),
        )
        self._create_menu_button(
            text="خروج",
            icon="log-out",
            command=self._on_close,
            danger=True,
        )
    def _create_menu_button(
        self,
        text,
        icon,
        command,
        danger=False,
    ):
        normal_fg = (
            COLORS["danger"]
            if danger
            else COLORS["text"]
        )
        icon_color = (
            COLORS["danger"]
            if danger
            else COLORS["muted_text"]
        )
        normal_bg = COLORS["surface"]
        hover_bg = "#E8EEF5"
        active_bg = "#DCE6F1"
        active_fg = COLORS["primary"]
        button_frame = tk.Frame(
            self.sidebar,
            bg=normal_bg,
            height=44,
            cursor="hand2",
        )
        button_frame.pack(
            fill="x",
            padx=10,
            pady=2,
        )
        button_frame.pack_propagate(False)
        icon_image = LucideIcon(
            icon,
            size=19,
            color=icon_color,
        )
        icon_label = tk.Label(
            button_frame,
            image=icon_image,
            bg=normal_bg,
        )
        icon_label.image = icon_image
        icon_label.pack(
            side="right",
            padx=(15, 12),
        )
        text_label = tk.Label(
            button_frame,
            text=text,
            bg=normal_bg,
            fg=normal_fg,
            font=("Tahoma", 10),
            anchor="e",
            cursor="hand2",
        )
        text_label.pack(
            side="right",
            fill="both",
            expand=True,
        )
        def set_normal():
            button_frame.config(
                bg=normal_bg
            )
            icon_label.config(
                bg=normal_bg
            )
            text_label.config(
                bg=normal_bg,
                fg=normal_fg,
            )
        def set_active():
            button_frame.config(
                bg=active_bg
            )
            icon_label.config(
                bg=active_bg
            )
            text_label.config(
                bg=active_bg,
                fg=active_fg,
            )
        def on_click(event=None):
            if not danger:
                if self.active_menu is not None:
                    self.active_menu[
                        "set_normal"
                    ]()
                set_active()
                self.active_menu = {
                    "set_normal": set_normal,
                }
            command()
        def on_enter(event=None):
            if (
                self.active_menu is not None
                and self.active_menu.get(
                    "set_normal"
                )
                == set_normal
            ):
                return
            button_frame.config(
                bg=hover_bg
            )
            icon_label.config(
                bg=hover_bg
            )
            text_label.config(
                bg=hover_bg
            )
        def on_leave(event=None):
            if (
                self.active_menu is not None
                and self.active_menu.get(
                    "set_normal"
                )
                == set_normal
            ):
                set_active()
            else:
                set_normal()
        for widget in (
            button_frame,
            icon_label,
            text_label,
        ):
            widget.bind(
                "<Button-1>",
                on_click,
            )
            widget.bind(
                "<Enter>",
                on_enter,
            )
            widget.bind(
                "<Leave>",
                on_leave,
            )
        return button_frame
    # ==================================================
    # Main Area
    # ==================================================
    def _create_main_area(self):
        self.main_area = tk.Frame(
            self.content,
            bg=COLORS["background"],
        )
        self.main_area.pack(
            side="left",
            fill="both",
            expand=True,
        )
        self.dashboard_frame = tk.Frame(
            self.main_area,
            bg=COLORS["background"],
        )
        self.dashboard_frame.pack(
            fill="both",
            expand=True,
            padx=35,
            pady=25,
        )
        self.current_page = self.dashboard_frame
        self._create_dashboard_empty()
    # ==================================================
    # Dashboard
    # ==================================================
    def _create_dashboard(self):
        for widget in (
            self.dashboard_frame.winfo_children()
        ):
            widget.destroy()
        if self.dashboard_data is None:
            self.dashboard_data = (
                get_dashboard_data()
            )
        data = self.dashboard_data
        # ----------------------------------------------
        # Dashboard Header
        # ----------------------------------------------
        dashboard_header = tk.Frame(
            self.dashboard_frame,
            bg=COLORS["background"],
        )
        dashboard_header.pack(
            fill="x",
            pady=(0, 15),
        )
        refresh_button = tk.Button(
            dashboard_header,
            text="↻  به‌روزرسانی",
            command=self._refresh_dashboard,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            activebackground="#E8EEF5",
            activeforeground=COLORS["text"],
            relief="flat",
            bd=0,
            font=("Tahoma", 9),
            cursor="hand2",
            padx=12,
            pady=6,
        )
        refresh_button.pack(
            side="left",
        )
        # ----------------------------------------------
        # KPI Row
        # ----------------------------------------------
        kpi_frame = tk.Frame(
            self.dashboard_frame,
            bg=COLORS["background"],
        )
        kpi_frame.pack(
            fill="x",
            pady=(0, 10),
        )
        # تاریخ امروز
        self._create_kpi_card(
            kpi_frame,
            title="تاریخ",
            value=self._format_shamsi_date(
                data["today"]
            ),
            value_font_size=13,
        )
        # آخرین به‌روزرسانی
        self._create_kpi_card(
            kpi_frame,
            title="آخرین به‌روزرسانی اطلاعات",
            value=self._format_shamsi_date(
                data["latest_update_date"]
            ),
            value_font_size=13,
        )
        # تعداد بیمه‌گذاران
        self._create_kpi_card(
            kpi_frame,
            title="تعداد کل بیمه‌گذاران",
            value=self._format_number(
                data["customer_count"]
            ),
            value_font_size=15,
        )
        # تعداد بیمه‌نامه‌ها
        self._create_kpi_card(
            kpi_frame,
            title="بیمه‌نامه‌های صادره سال جاری",
            value=self._format_number(
                data["policy_count"]
            ),
            value_font_size=15,
        )
        # حق‌بیمه تولیدی
        self._create_kpi_card(
            kpi_frame,
            title="حق‌بیمه تولیدی سال جاری",
            value=self._format_money(
                data["production"]
            ),
            value_font_size=14,
        )
        # ----------------------------------------------
        # Middle
        # ----------------------------------------------
        middle_frame = tk.Frame(
            self.dashboard_frame,
            bg=COLORS["background"],
        )
        middle_frame.pack(
            fill="both",
            expand=True,
        )
        middle_frame.grid_columnconfigure(
            0,
            weight=1,
            uniform="dashboard",
        )
        middle_frame.grid_columnconfigure(
            1,
            weight=1,
            uniform="dashboard",
        )
        middle_frame.grid_rowconfigure(
            0,
            weight=1,
        )
        # ----------------------------------------------
        # Expiry Card
        # ----------------------------------------------
        expiry_card = tk.Frame(
            middle_frame,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        expiry_card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 5),
        )
        title = tk.Label(
            expiry_card,
            text="بیمه‌های نزدیک به انقضا",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Tahoma", 13, "bold"),
            anchor="e",
        )
        title.pack(
            fill="x",
            padx=20,
            pady=(20, 10),
        )
        self._create_expiry_section(
            expiry_card,
            "امروز",
            data["expiry_today"],
        )
        self._create_expiry_section(
            expiry_card,
            "فردا",
            data["expiry_tomorrow"],
        )
        self._create_expiry_section(
            expiry_card,
            "پس‌فردا",
            data["expiry_day_after"],
        )
        # ----------------------------------------------
        # Chart Card
        # ----------------------------------------------
        chart_card = tk.Frame(
            middle_frame,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        chart_card.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(5, 0),
        )
        title = tk.Label(
            chart_card,
            text="ترکیب فروش بر اساس رشته بیمه در سال جاری",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Tahoma", 13, "bold"),
            anchor="e",
        )
        title.pack(
            fill="x",
            padx=20,
            pady=(20, 0),
        )
        self._create_sales_chart(
            chart_card,
            data["sales_by_insurance_type"],
        )
    def _refresh_dashboard(self):
        self.dashboard_data = None
        self._create_dashboard()
    # ==================================================
    # Expiry Sections
    # ==================================================
    def _create_expiry_section(
        self,
        parent,
        title,
        policies,
    ):
        section = tk.Frame(
            parent,
            bg=COLORS["surface"],
        )
        section.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 8),
        )
        header = tk.Frame(
            section,
            bg=COLORS["surface"],
        )
        header.pack(
            fill="x",
            pady=(5, 5),
        )
        title_label = tk.Label(
            header,
            text=title,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Tahoma", 10, "bold"),
            anchor="e",
        )
        title_label.pack(
            side="right",
        )
        count_label = tk.Label(
            header,
            text=self._format_number(
                len(policies)
            ),
            bg=COLORS["surface"],
            fg=COLORS["primary"],
            font=("Tahoma", 9, "bold"),
            anchor="e",
        )
        count_label.pack(
            side="left",
        )
        if not policies:
            empty_label = tk.Label(
                section,
                text="موردی وجود ندارد",
                bg=COLORS["surface"],
                fg=COLORS["muted_text"],
                font=("Tahoma", 9),
                anchor="e",
            )
            empty_label.pack(
                fill="x",
                pady=(2, 8),
            )
            return
        table_frame = tk.Frame(
            section,
            bg=COLORS["surface"],
        )
        table_frame.pack(
            fill="both",
            expand=True,
        )
        # ----------------------------------------------
        # Columns
        # ----------------------------------------------
        columns = (
            "policy_number",
            "insurance_type",
            "customer",
        )
        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=3,
        )
        # ----------------------------------------------
        # Headers
        # ----------------------------------------------
        tree.heading(
            "policy_number",
            text="ش بیمه",
            anchor="center",
        )
        tree.heading(
            "insurance_type",
            text="رشته",
            anchor="e",
        )
        tree.heading(
            "customer",
            text="بیمه‌گذار",
            anchor="e",
        )
        # ----------------------------------------------
        # Column widths / alignment
        # ----------------------------------------------
        tree.column(
            "policy_number",
            width=90,
            anchor="center",
            stretch=False,
        )
        tree.column(
            "insurance_type",
            width=150,
            anchor="e",
        )
        tree.column(
            "customer",
            width=190,
            anchor="e",
        )
        # ----------------------------------------------
        # Scrollbar
        # ----------------------------------------------
        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=tree.yview,
        )
        tree.configure(
            yscrollcommand=scrollbar.set
        )
        scrollbar.pack(
            side="right",
            fill="y",
        )
        tree.pack(
            side="left",
            fill="both",
            expand=True,
        )
        # ----------------------------------------------
        # Data
        # ----------------------------------------------
        for policy in policies:
            customer_name = "—"
            if policy.customer:
                first_name = (
                    policy.customer.name
                    or ""
                )
                family = (
                    policy.customer.family
                    or ""
                )
                customer_name = (
                    f"{first_name} {family}"
                ).strip()
            insurance_type = "—"
            if policy.insurance_type:
                insurance_type = (
                    policy.insurance_type.display_name
                    or "—"
                )
            tree.insert(
                "",
                "end",
                values=(
                    self._to_persian_digits(
                        policy.policy_number
                    ),
                    insurance_type,
                    customer_name,
                ),
            )
    # ==================================================
    # Sales Chart
    # ==================================================
    def _create_sales_chart(
        self,
        parent,
        sales_by_type,
    ):
        sorted_items = sorted(
            (
                (name, value)
                for name, value
                in sales_by_type.items()
                if value > 0
            ),
            key=lambda item: item[1],
            reverse=True,
        )
        if not sorted_items:
            empty_label = tk.Label(
                parent,
                text="اطلاعاتی برای نمایش وجود ندارد.",
                bg=COLORS["surface"],
                fg=COLORS["muted_text"],
                font=("Tahoma", 10),
            )
            empty_label.pack(
                expand=True,
            )
            return
        labels = [
            item[0]
            for item in sorted_items
        ]
        values = [
            float(item[1])
            for item in sorted_items
        ]
        figure = Figure(
            figsize=(7, 5),
            dpi=100,
        )
        ax = figure.add_subplot(111)
        wedges, _, _ = ax.pie(
            values,
            autopct=lambda pct: (
                self._to_persian_digits(
                    f"{pct:.0f}%"
                )
                if pct >= 3
                else ""
            ),
            startangle=90,
        )
        ax.axis("equal")
        # نام رشته‌ها زیر نمودار
        # مرتب‌شده از بیشترین فروش به کمترین فروش
        ax.legend(
            wedges,
            labels,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.02),
            ncol=2,
            prop={
                "family": "Tahoma",
                "size": 8,
            },
            frameon=False,
        )
        figure.subplots_adjust(
            left=0.05,
            right=0.95,
            top=0.95,
            bottom=0.30,
        )
        canvas = FigureCanvasTkAgg(
            figure,
            master=parent,
        )
        canvas.draw()
        canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0, 10),
        )
    def _clear_main_area(self):
        for widget in self.main_area.winfo_children():
            widget.destroy()
        self.current_page = None
        self.dashboard_frame = None
    # ==================================================
    # Menu Actions
    # ==================================================
    def _show_dashboard(self):
        self._clear_main_area()
        self.dashboard_frame = tk.Frame(
            self.main_area,
            bg=COLORS["background"],
        )
        self.dashboard_frame.pack(
            fill="both",
            expand=True,
            padx=35,
            pady=25,
        )
        self.current_page = self.dashboard_frame
        self._create_dashboard()
    def _open_customers(self):
        self._clear_main_area()
        customer_page = CustomerList(
            self.main_area,
            role=self.current_role
        )
        customer_page.pack(
            fill="both",
            expand=True,
            padx=35,
            pady=25
        )
        self.current_page = customer_page
    def _open_policies(self):
        self._clear_main_area()
        policy_page = PolicyList(
            self.main_area,
            role=self.current_role
        )
        policy_page.pack(
            fill="both",
            expand=True,
            padx=35,
            pady=25
        )
        self.current_page = policy_page
    def _open_marketers(self):
        if not can_access_menu(self.current_role, "marketers"):
            return
        self._clear_main_area()
        marketer_page = MarketerList(
            self.main_area,
            role=self.current_role
        )
        marketer_page.pack(
            fill="both",
            expand=True,
            padx=35,
            pady=25,
        )
        self.current_page = marketer_page
    def open_manual_assignment(self):
        if not can_access_menu(self.current_role, "assignment"):
            return
        candidates = get_all_assignment_candidates()
        if not candidates:
            messagebox.showinfo(
                "بررسی بیمه‌نامه‌ها",
                "در حال حاضر بیمه‌نامه‌ای برای تکمیل اطلاعات وجود ندارد.",
                parent=self.window,
            )
            return
        open_policy_assignment(
            self.window,
            candidates,
        )
    def _open_reports(self):
        self._clear_main_area()
        reports_page = ReportsPage(
            self.main_area,
            role=self.current_role,
        )
        reports_page.pack(
            fill="both",
            expand=True,
            padx=35,
            pady=25,
        )
        self.current_page = reports_page
    def _open_import(self):
        if not can_access_menu(self.current_role, "import"):
            return
        self._clear_main_area()
        data_transfer_page = DataTransferPage(
            self.main_area
        )
        data_transfer_page.pack(
            fill="both",
            expand=True,
            padx=35,
            pady=25,
        )
        self.current_page = data_transfer_page
    def _open_settings(self):
        self._clear_main_area()
        settings_page = SettingsPage(
            self.main_area,
            self.current_role,
            self.current_user_id,
        )
        settings_page.pack(
            fill="both",
            expand=True,
            padx=35,
            pady=25,
        )
        self.current_page = settings_page
    def _open_basic_data(self):
        if not can_access_menu(self.current_role, "basic_data"):
            return
        self._clear_main_area()
        basic_data_page = BasicDataPage(
            self.main_area,
            self.current_role,
            self.current_user_id,
        )
        basic_data_page.pack(
            fill="both",
            expand=True,
            padx=35,
            pady=25,
        )
        self.current_page = basic_data_page
    # ==================================================
    # Login
    # ==================================================
    def show(self):
        self.window.deiconify()
        self._set_full_window()
        self.window.lift()
    def run(self):
        self.window.after(
            100,
            self._show_login,
        )
        self.window.mainloop()
    def _show_login(self):
        self.show()
        self.login_window = LoginWindow(
            parent=self.window,
            on_success=self._login_success,
            on_cancel=self._login_cancel,
        )
    def _login_success(
        self,
        user_id,
        username,
        full_name,
        role,
    ):
        self.current_user_id = user_id
        self.current_username = username
        self.current_full_name = full_name
        self.current_role = role
        self._apply_menu_permissions()
        self.user_label.config(
            text=(
                f"کاربر: {full_name}\n"
                f"نقش: {role}"
            )
        )
        self._show_dashboard()
    def _login_cancel(self):
        self._on_close()
    def _on_close(self):
        self.window.destroy()
    # ==================================================
    # KPI Card
    # ==================================================
    def _create_kpi_card(
        self,
        parent,
        title,
        value,
        value_font_size=15,
    ):
        card = tk.Frame(
            parent,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            height=90,
        )
        card.pack(
            side="right",
            fill="both",
            expand=True,
            padx=5,
        )
        card.pack_propagate(False)
        title_label = tk.Label(
            card,
            text=title,
            bg=COLORS["surface"],
            fg=COLORS["muted_text"],
            font=("Tahoma", 9),
            anchor="e",
        )
        title_label.pack(
            fill="x",
            padx=15,
            pady=(18, 5),
        )
        value_label = tk.Label(
            card,
            text=value,
            bg=COLORS["surface"],
            fg=COLORS["primary"],
            font=(
                "Tahoma",
                value_font_size,
                "bold",
            ),
            anchor="e",
        )
        value_label.pack(
            fill="x",
            padx=15,
        )
    # ==================================================
    # Formatting
    # ==================================================
    def _to_persian_digits(
        self,
        value,
    ):
        """
        تبدیل ارقام انگلیسی به ارقام فارسی.
        """
        if value is None:
            return "—"
        return str(value).translate(
            str.maketrans(
                "0123456789",
                "۰۱۲۳۴۵۶۷۸۹",
            )
        )
    def _format_number(
        self,
        value,
    ):
        if value is None:
            return "۰"
        formatted = f"{int(value):,}".replace(
            ",",
            "٬",
        )
        return self._to_persian_digits(
            formatted
        )
    def _format_money(
        self,
        value,
    ):
        if value is None:
            return "۰"
        formatted = f"{int(value):,}".replace(
            ",",
            "٬",
        )
        return self._to_persian_digits(
            formatted
        )
    def _format_date(
        self,
        value,
    ):
        if value is None:
            return "—"
        formatted = value.strftime(
            "%Y/%m/%d"
        )
        return self._to_persian_digits(
            formatted
        )
    def _format_shamsi_date(
        self,
        value,
    ):
        if value is None:
            return "—"
        shamsi_date = convert_date_to_shamsi(
            value
        )
        return self._to_persian_digits(
            shamsi_date
        )
    def _apply_menu_permissions(self):
        for menu, button in self.menu_buttons.items():
            if not can_access_menu(self.current_role, menu):
                button.pack_forget()
    # ==================================================
    # Empty Dashboard
    # ==================================================
    def _create_dashboard_empty(self):
        for widget in (
            self.dashboard_frame.winfo_children()
        ):
            widget.destroy()