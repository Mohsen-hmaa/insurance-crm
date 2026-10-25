import math
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from gui.styles import COLORS, configure_report_styles
from services.date_service import convert_shamsi_to_date
from services.agency_performance_service import get_agency_performance_report
BG = COLORS["surface"]
BORDER = COLORS["border"]
TEXT = COLORS["text"]
ACCENT = COLORS["primary"]
CARD_BG = COLORS["card"]
class AgencyPerformanceReport(tk.Frame):
    def __init__(
        self,
        parent,
        current_agent=None,
        report_title=None,
        standalone=False,
        marketer_id=None,
    ):
        super().__init__(parent, bg=BG)
        self.current_agent = current_agent
        self.marketer_id = marketer_id
        self.report_title = (
            report_title or "گزارش عملکرد نمایندگی"
        )
        self.standalone = standalone
        configure_report_styles()
        self.create_widgets()
    # =========================================================
    # رابط اصلی
    # =========================================================
    def create_widgets(self):
        # -----------------------------------------------------
        # نوار بالا: عنوان و دکمه بازگشت
        # -----------------------------------------------------
        header_frame = ttk.Frame(self, style="Commission.TFrame")
        header_frame.pack(fill="x", padx=20, pady=(10, 0))
        ttk.Button(
            header_frame,
            text=(
                "بستن گزارش"
                if self.standalone
                else "بازگشت به گزارش‌ها"
            ),
            style="Primary.TButton",
            command=(
                self.close_report
                if self.standalone
                else self.go_back
            ),
        ).pack(side="right")
        ttk.Label(
            header_frame,
            text=self.report_title,
            style="CommissionTitle.TLabel",
        ).pack(side="left")
        # -----------------------------------------------------
        # بازه گزارش
        # -----------------------------------------------------
        date_frame = ttk.LabelFrame(
            self,
            text="بازه گزارش",
            labelanchor="ne",
            style="Commission.TLabelframe",
            padding=(10, 8),
        )
        date_frame.pack(fill="x", padx=20, pady=(12, 8))
        # تاریخ شروع
        start_frame = ttk.Frame(date_frame, style="Commission.TFrame")
        ttk.Label(
            start_frame,
            text="تاریخ شروع",
            style="Commission.TLabel",
        ).pack(side="right", padx=(0, 5))
        self.start_entry = ttk.Entry(
            start_frame,
            style="Commission.TEntry",
            width=14,
            justify="center",
        )
        self.start_entry.pack(side="right")
        # تاریخ پایان
        end_frame = ttk.Frame(date_frame, style="Commission.TFrame")
        ttk.Label(
            end_frame,
            text="تاریخ پایان",
            style="Commission.TLabel",
        ).pack(side="right", padx=(0, 5))
        self.end_entry = ttk.Entry(
            end_frame,
            style="Commission.TEntry",
            width=14,
            justify="center",
        )
        self.end_entry.pack(side="right")
        # دکمه نمایش گزارش
        self.show_button = ttk.Button(
            date_frame,
            text="نمایش گزارش",
            style="Primary.TButton",
            command=self.load_report,
        )
        start_frame.pack(side="right", padx=(20, 0))
        end_frame.pack(side="right", padx=(20, 0))
        self.show_button.pack(side="right")
        # ترتیب Tab
        self.start_entry.bind("<Tab>", self._focus_end)
        self.end_entry.bind("<Tab>", self._focus_button)
        self.show_button.bind("<Tab>", self._focus_start)
        self.end_entry.bind("<Shift-Tab>", self._focus_start)
        self.show_button.bind("<Shift-Tab>", self._focus_end)
        self.start_entry.bind("<Shift-Tab>", self._focus_button)
        # -----------------------------------------------------
        # محدوده اسکرول
        # -----------------------------------------------------
        outer_frame = ttk.Frame(self, style="Commission.TFrame")
        outer_frame.pack(fill="both", expand=True, padx=20, pady=(0, 8))
        self.canvas = tk.Canvas(
            outer_frame,
            highlightthickness=0,
            bg=BG,
        )
        scrollbar = ttk.Scrollbar(
            outer_frame,
            orient="vertical",
            command=self.canvas.yview,
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.report_content = tk.Frame(self.canvas, bg=BG)
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.report_content,
            anchor="nw",
        )
        self.report_content.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        # اسکرول با موس روی کل صفحه فعال باشد
        self.bind("<Enter>", self._enable_mousewheel)
        self.bind("<Leave>", self._disable_mousewheel)
        self.bind("<Destroy>", self._on_destroy)
    # =========================================================
    # کنترل Tab
    # =========================================================
    def _focus_end(self, event=None):
        self.end_entry.focus_set()
        return "break"
    def _focus_button(self, event=None):
        self.show_button.focus_set()
        return "break"
    def _focus_start(self, event=None):
        self.start_entry.focus_set()
        return "break"
    # =========================================================
    # اسکرول با موس
    # =========================================================
    def _enable_mousewheel(self, event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    def _disable_mousewheel(self, event=None):
        # ورود به ویجت‌های داخلی هم رویداد Leave می‌سازد؛
        # فقط وقتی اسکرول را غیرفعال می‌کنیم که موس واقعاً بیرون رفته باشد.
        if event is not None:
            widget = self.winfo_containing(event.x_root, event.y_root)
            if widget is not None and str(widget).startswith(str(self)):
                return
        self.canvas.unbind_all("<MouseWheel>")
    def _on_destroy(self, event=None):
        if event is not None and event.widget is not self:
            return
        try:
            self.canvas.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass
    def _on_mousewheel(self, event):
        if event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    # =========================================================
    # تنظیم محدوده اسکرول
    # =========================================================
    def _on_content_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    # =========================================================
    # بارگذاری گزارش
    # =========================================================
    def load_report(self):
        parent = self.winfo_toplevel()
        start_shamsi = self.start_entry.get().strip()
        end_shamsi = self.end_entry.get().strip()
        if not start_shamsi or not end_shamsi:
            messagebox.showwarning(
                "هشدار",
                "تاریخ شروع و پایان را وارد کنید.",
                parent=parent,
            )
            return
        try:
            start_date = convert_shamsi_to_date(start_shamsi)
            end_date = convert_shamsi_to_date(end_shamsi)
        except Exception:
            messagebox.showerror(
                "خطا",
                "فرمت تاریخ وارد شده صحیح نیست.",
                parent=parent,
            )
            return
        if start_date > end_date:
            messagebox.showwarning(
                "هشدار",
                "تاریخ شروع نمی‌تواند بعد از تاریخ پایان باشد.",
                parent=parent,
            )
            return
        try:
            report = get_agency_performance_report(
                start_date,
                end_date,
                current_agent=self.current_agent,
                marketer_id=self.marketer_id,
            )
        except Exception as e:
            messagebox.showerror(
                "خطا",
                f"خطا در تهیه گزارش:\n{e}",
                parent=parent,
            )
            return
        self.display_report(report)
    # =========================================================
    # نمایش گزارش
    # =========================================================
    def display_report(self, report):
        for widget in self.report_content.winfo_children():
            widget.destroy()
        # ردیف اول KPI
        row1 = self._create_kpi_row(self.report_content, pady=(5, 3))
        self.create_kpi_box(
            row1, 3, "فروش خالص",
            self.format_money(report.get("net_sales", 0)),
        )
        self.create_kpi_box(
            row1, 2, "فروش ناخالص",
            self.format_money(report.get("gross_sales", 0)),
        )
        self.create_kpi_box(
            row1, 1, "وصولی ناخالص",
            self.format_money(report.get("collected_amount", 0)),
        )
        self.create_kpi_box(
            row1, 0, "تعداد بیمه‌نامه",
            f"{report.get('policy_count', 0):,}",
        )
        # ردیف دوم KPI
        row2 = self._create_kpi_row(self.report_content, pady=3)
        self.create_kpi_box(
            row2, 3, "حق‌بیمه بیمه‌نامه‌های اصلی",
            self.format_money(report.get("policy_premium", 0)),
        )
        self.create_kpi_box(
            row2, 2, "حق‌بیمه الحاقیه‌های افزایشی",
            self.format_money(report.get("additional_endorsement_premium", 0)),
        )
        self.create_kpi_box(
            row2, 1, "حق‌بیمه الحاقیه‌های برگشتی",
            self.format_money(report.get("return_endorsement_premium", 0)),
        )
        self.create_growth_box(
            row2,
            0,
            report.get("premium_growth"),
            report.get("policy_count_growth"),
        )
        # نمودار
        chart_frame = ttk.LabelFrame(
            self.report_content,
            text="ترکیب فروش بر اساس رشته بیمه",
            labelanchor="ne",
            style="Commission.TLabelframe",
            padding=8,
        )
        chart_frame.pack(fill="both", expand=True, padx=10, pady=(8, 5))
        self.create_pie_chart(
            chart_frame,
            report.get("sales_by_insurance_type", {}),
        )
    @staticmethod
    def _create_kpi_row(parent, pady):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", padx=10, pady=pady)
        for i in range(4):
            row.grid_columnconfigure(i, weight=1, uniform="kpi")
        return row
    # =========================================================
    # کادر KPI
    # =========================================================
    @staticmethod
    def _create_card(parent, column):
        box = tk.Frame(
            parent,
            bg=CARD_BG,
            highlightthickness=1,
            highlightbackground=BORDER,
            padx=10,
            pady=8,
        )
        box.grid(row=0, column=column, sticky="nsew", padx=4)
        return box
    def create_kpi_box(self, parent, column, title, value):
        box = self._create_card(parent, column)
        tk.Label(
            box,
            text=title,
            font=("Tahoma", 9, "bold"),
            anchor="e",
            justify="right",
            bg=CARD_BG,
            fg=TEXT,
        ).pack(fill="x")
        tk.Label(
            box,
            text=value,
            font=("Tahoma", 11, "bold"),
            anchor="e",
            justify="right",
            bg=CARD_BG,
            fg=ACCENT,
        ).pack(fill="x", pady=(5, 0))
    # =========================================================
    # کادر رشد
    # =========================================================
    def create_growth_box(self, parent, column, premium_growth,
                          policy_count_growth):
        box = self._create_card(parent, column)
        tk.Label(
            box,
            text="رشد نسبت به دوره مشابه سال قبل",
            font=("Tahoma", 9, "bold"),
            anchor="e",
            justify="right",
            bg=CARD_BG,
            fg=TEXT,
        ).pack(fill="x")
        premium_text = (
            "بدون سابقه"
            if premium_growth is None
            else f"{premium_growth:+.1f}%"
        )
        count_text = (
            "بدون سابقه"
            if policy_count_growth is None
            else f"{policy_count_growth:+.1f}%"
        )
        tk.Label(
            box,
            text=f"ریالی: {premium_text}",
            font=("Tahoma", 9),
            anchor="e",
            justify="right",
            bg=CARD_BG,
            fg=TEXT,
        ).pack(fill="x", pady=(4, 0))
        tk.Label(
            box,
            text=f"تعدادی: {count_text}",
            font=("Tahoma", 9),
            anchor="e",
            justify="right",
            bg=CARD_BG,
            fg=TEXT,
        ).pack(fill="x", pady=(2, 0))
    # =========================================================
    # نمودار دایره‌ای و راهنمای رشته‌ها
    # =========================================================
    @staticmethod
    def _show_empty(parent):
        tk.Label(
            parent,
            text="اطلاعاتی برای نمایش وجود ندارد.",
            font=("Tahoma", 11),
            bg=BG,
            fg=TEXT,
        ).pack(expand=True)
    def create_pie_chart(self, parent, sales_by_type):
        if not sales_by_type:
            self._show_empty(parent)
            return
        # فقط مقادیر مثبت برای نمودار دایره‌ای
        items = sorted(
            sales_by_type.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        items = [item for item in items if float(item[1]) > 0]
        if not items:
            self._show_empty(parent)
            return
        labels = [item[0] for item in items]
        values = [float(item[1]) for item in items]
        total = sum(values)
        if total <= 0:
            self._show_empty(parent)
            return
        percentages = [value / total * 100 for value in values]
        # -----------------------------------------------------
        # تقسیم فضا: راهنما 65 درصد (راست)، نمودار 35 درصد (چپ)
        # -----------------------------------------------------
        chart_container = tk.Frame(parent, bg=BG)
        chart_container.pack(fill="both", expand=True)
        chart_container.grid_columnconfigure(
            0, weight=65, uniform="chart_columns"
        )
        chart_container.grid_columnconfigure(
            1, weight=35, uniform="chart_columns"
        )
        chart_container.grid_rowconfigure(0, weight=1)
        # قاب نمودار
        chart_area = tk.Frame(chart_container, bg=BG)
        chart_area.grid(
            row=0, column=0, sticky="nsew", padx=(0, 6), pady=5
        )
        # قاب راهنما
        legend_area = tk.Frame(
            chart_container,
            bg=BG,
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        legend_area.grid(
            row=0, column=1, sticky="nsew", padx=(6, 2), pady=5
        )
        # -----------------------------------------------------
        # نمودار
        # -----------------------------------------------------
        fig = Figure(figsize=(4, 4), dpi=100, facecolor=BG)
        ax = fig.add_subplot(111)
        wedges, _ = ax.pie(
            values,
            labels=None,
            startangle=90,
            counterclock=False,
            radius=0.88,
            wedgeprops={"linewidth": 1, "edgecolor": "white"},
        )
        ax.set_aspect("equal")
        ax.set_position([0.02, 0.02, 0.96, 0.96])
        # نمایش درصدهای 3 درصد و بیشتر روی نمودار
        for wedge, percentage in zip(wedges, percentages):
            if percentage < 3:
                continue
            angle_rad = math.radians((wedge.theta1 + wedge.theta2) / 2)
            ax.text(
                0.60 * math.cos(angle_rad),
                0.60 * math.sin(angle_rad),
                f"{percentage:.1f}%",
                ha="center",
                va="center",
                fontsize=9,
                fontweight="bold",
            )
        fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
        canvas = FigureCanvasTkAgg(fig, master=chart_area)
        canvas.draw()
        canvas.get_tk_widget().configure(bg=BG, highlightthickness=0)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        # نگه داشتن ارجاع برای جلوگیری از آزاد شدن زودهنگام
        self.pie_figure = fig
        self.pie_canvas = canvas
        # -----------------------------------------------------
        # عنوان راهنما
        # -----------------------------------------------------
        tk.Label(
            legend_area,
            text="رشته‌های بیمه",
            font=("Tahoma", 10, "bold"),
            anchor="e",
            justify="right",
            bg=BG,
            fg=ACCENT,
        ).pack(fill="x", padx=10, pady=(8, 6))
        ttk.Separator(legend_area, orient="horizontal").pack(
            fill="x", padx=8, pady=(0, 4)
        )
        # -----------------------------------------------------
        # ردیف‌های راهنما: چپ درصد، وسط نام رشته، راست رنگ
        # -----------------------------------------------------
        legend_rows = tk.Frame(legend_area, bg=BG)
        legend_rows.pack(fill="both", expand=True, padx=8, pady=4)
        for label, percentage, wedge in zip(labels, percentages, wedges):
            row = tk.Frame(legend_rows, bg=BG)
            row.pack(fill="x", pady=2)
            tk.Label(
                row,
                text=f"{percentage:.1f}%",
                width=8,
                anchor="w",
                justify="left",
                font=("Tahoma", 9, "bold"),
                bg=BG,
                fg=TEXT,
            ).pack(side="left")
            color_canvas = tk.Canvas(
                row,
                width=18,
                height=18,
                highlightthickness=0,
                bd=0,
                bg=BG,
            )
            color_canvas.pack(side="right", padx=(5, 0))
            color_canvas.create_rectangle(
                2, 2, 16, 16,
                fill=self._rgba_to_hex(wedge.get_facecolor()),
                outline="",
            )
            tk.Label(
                row,
                text=label,
                anchor="e",
                justify="right",
                font=("Tahoma", 9),
                bg=BG,
                fg=TEXT,
            ).pack(side="right", fill="x", expand=True, padx=8)
    # =========================================================
    # تبدیل رنگ RGBA به HEX
    # =========================================================
    @staticmethod
    def _rgba_to_hex(rgba):
        r = int(rgba[0] * 255)
        g = int(rgba[1] * 255)
        b = int(rgba[2] * 255)
        return f"#{r:02x}{g:02x}{b:02x}"
    # =========================================================
    # فرمت مبلغ
    # =========================================================
    @staticmethod
    def format_money(value):
        if value is None:
            value = 0
        return f"{value:,.0f}"
    def close_report(self):
        self.winfo_toplevel().destroy()
    # =========================================================
    # بازگشت به صفحه گزارش‌ها
    # =========================================================
    def go_back(self):
        from gui.reports_page import ReportsPage
        parent = self.master
        # بازیابی نقش از صفحه گزارش‌ها
        role = getattr(parent, "role", None)
        for widget in parent.winfo_children():
            widget.destroy()
        reports_page = ReportsPage(
            parent,
            role=role,
        )
        reports_page.pack(
            fill="both",
            expand=True,
        )
