import ctypes
import tkinter as tk
from tkinter import ttk
COLORS = {
    "primary": "#1F4E78",
    "primary_dark": "#163A5C",
    "secondary": "#5B9BD5",
    "background": "#F4F6F8",
    "surface": "#FFFFFF",
    "text": "#263238",
    "muted_text": "#6B7280",
    "border": "#D9DEE5",
    "success": "#2E7D32",
    "danger": "#C62828",
    # ---- مخصوص صفحه‌های گزارش ----
    "card": "#F7F9FC",                 # پس‌زمینه کارت‌های KPI
    "combo_button": "#E3EAF2",         # دکمه‌ی فلش Combobox
    "combo_button_hover": "#CBD7E4",
    "combo_button_pressed": "#B7C7D9",
    "combo_border": "#B7C4D1",
    "disabled": "#9AA5B1",
}
FONTS = {
    "title": ("Tahoma", 20, "bold"),
    "subtitle": ("Tahoma", 12),
    "normal": ("Tahoma", 10),
    "normal_bold": ("Tahoma", 10, "bold"),
    "button": ("Tahoma", 10, "bold"),
}
# =============================================================
# استایل عمومی برنامه
# =============================================================
def configure_styles():
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(
        "App.TFrame",
        background=COLORS["background"],
    )
    style.configure(
        "Card.TFrame",
        background=COLORS["surface"],
    )
    style.configure(
        "Primary.TButton",
        font=FONTS["button"],
        foreground="white",
        background=COLORS["primary"],
        padding=(20, 10),
        borderwidth=0,
    )
    style.map(
        "Primary.TButton",
        background=[
            ("active", COLORS["primary_dark"]),
            ("pressed", COLORS["primary_dark"]),
        ],
    )
    style.configure(
        "App.TLabel",
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=FONTS["normal"],
    )
    style.configure(
        "Title.TLabel",
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=FONTS["title"],
    )
    style.configure(
        "Subtitle.TLabel",
        background=COLORS["background"],
        foreground=COLORS["muted_text"],
        font=FONTS["subtitle"],
    )
    style.configure(
        "Treeview",
        rowheight=27,
        font=("Tahoma", 9),
        background=COLORS["surface"],
        foreground=COLORS["text"],
        fieldbackground=COLORS["surface"],
    )
    style.configure(
        "Treeview.Heading",
        rowheight=27,
        font=("Tahoma", 9, "bold"),
        foreground="white",
        background=COLORS["primary"],
        anchor="e",
    )
    # حفظ رنگ سرستون هنگام قرار گرفتن موس روی آن
    style.map(
        "Treeview.Heading",
        background=[
            ("pressed", COLORS["primary_dark"]),
            ("active", COLORS["primary_dark"]),
        ],
        foreground=[
            ("pressed", "#FFFFFF"),
            ("active", "#FFFFFF"),
        ],
    )
# =============================================================
# استایل صفحه‌ها و پنجره‌های گزارش (کارمزد، عملکرد نمایندگی، ...)
#
# دکمه‌ها استایل استاندارد برنامه (Primary.TButton) را می‌گیرند و استایل جدایی ندارند.
# بقیه‌ی استایل‌ها با پیشوند Commission. تعریف می‌شوند و فقط روی ویجت‌هایی
# اعمال می‌شوند که صریحاً این استایل را بگیرند؛ پس روی بقیه‌ی برنامه
# اثری ندارند. هر تغییری در ظاهر گزارش‌ها فقط از همین‌جا انجام می‌شود.
# =============================================================
def configure_report_styles():
    style = ttk.Style()
    # اگر configure_styles() قبلاً اجرا شده باشد این خط بی‌اثر است
    if style.theme_use() != "clam":
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
    surface = COLORS["surface"]
    text = COLORS["text"]
    primary = COLORS["primary"]
    style.configure("Commission.TFrame", background=surface)
    style.configure(
        "Commission.TLabel",
        background=surface,
        foreground=text,
        font=FONTS["normal"],
    )
    style.configure(
        "CommissionTitle.TLabel",
        background=surface,
        foreground=primary,
        font=("Tahoma", 14, "bold"),
    )
    style.configure(
        "Commission.TLabelframe",
        background=surface,
        bordercolor=COLORS["border"],
        relief="solid",
        borderwidth=1,
    )
    style.configure(
        "Commission.TLabelframe.Label",
        background=surface,
        foreground=text,
        font=FONTS["normal_bold"],
    )
    style.configure(
        "Commission.TEntry",
        fieldbackground=surface,
        foreground=text,
        padding=5,
    )
    # Combobox: فلش با arrowcolor رسم می‌شود و دکمه‌ی فلش از background
    # پر می‌شود؛ پس این دو باید با هم تضاد داشته باشند.
    style.configure(
        "Commission.TCombobox",
        fieldbackground=surface,
        background=COLORS["combo_button"],
        foreground=text,
        arrowcolor=primary,
        bordercolor=COLORS["combo_border"],
        lightcolor=surface,
        darkcolor=surface,
        arrowsize=14,
        padding=5,
    )
    style.map(
        "Commission.TCombobox",
        fieldbackground=[("readonly", surface)],
        foreground=[("readonly", text)],
        background=[
            ("pressed", COLORS["combo_button_pressed"]),
            ("active", COLORS["combo_button_hover"]),
            ("readonly", COLORS["combo_button"]),
        ],
        arrowcolor=[
            ("disabled", COLORS["disabled"]),
            ("!disabled", primary),
        ],
        selectbackground=[("readonly", surface)],
        selectforeground=[("readonly", text)],
    )
    style.configure(
        "Commission.TRadiobutton",
        background=surface,
        foreground=text,
        font=FONTS["normal"],
    )
    style.map(
        "Commission.TRadiobutton",
        background=[("active", surface)],
        indicatorcolor=[("selected", primary), ("!selected", surface)],
    )
    # لیست بازشونده‌ی Combobox (tk.Listbox و بیرون از ttk است)
    root = style.master
    root.option_add("*TCombobox*Listbox.background", surface)
    root.option_add("*TCombobox*Listbox.foreground", text)
    root.option_add("*TCombobox*Listbox.selectBackground", primary)
    root.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")
    root.option_add("*TCombobox*Listbox.font", FONTS["normal"])
def apply_report_window_style(window):
    """اعمال استایل گزارش روی همه‌ی ویجت‌های ttk داخل یک پنجره."""
    def apply_to_children(parent):
        for widget in parent.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.configure(style="Primary.TButton")
            elif isinstance(widget, ttk.LabelFrame):
                widget.configure(style="Commission.TLabelframe")
            elif isinstance(widget, ttk.Frame):
                widget.configure(style="Commission.TFrame")
            # Combobox زیرکلاس Entry است؛ پس باید قبل از Entry بررسی شود.
            elif isinstance(widget, ttk.Combobox):
                widget.configure(style="Commission.TCombobox")
            elif isinstance(widget, ttk.Entry):
                widget.configure(style="Commission.TEntry")
            elif isinstance(widget, ttk.Radiobutton):
                widget.configure(style="Commission.TRadiobutton")
            elif isinstance(widget, ttk.Label):
                if widget.cget("style") != "CommissionTitle.TLabel":
                    widget.configure(style="Commission.TLabel")
            apply_to_children(widget)
    apply_to_children(window)
def finalize_report_window(window):
    """استایل گزارش + رنگ نوار عنوان؛ بعد از ساخته شدن همه‌ی ویجت‌ها صدا زده شود."""
    apply_report_window_style(window)
    window.after(
        200,
        lambda w=window: set_title_bar_color(w, COLORS["primary"]),
    )
# =============================================================
# نوار عنوان ویندوز 11
# =============================================================
def get_real_window_hwnd(window):
    """شناسه‌ی واقعی پنجره‌ی اصلی، نه ناحیه‌ی داخلی Tkinter."""
    window.update_idletasks()
    user32 = ctypes.windll.user32
    user32.GetAncestor.restype = ctypes.c_void_p
    user32.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    GA_ROOT = 2
    return user32.GetAncestor(window.winfo_id(), GA_ROOT)
def set_title_bar_color(window, hex_color, text_color="#FFFFFF"):
    """تغییر رنگ نوار عنوان (و رنگ نوشته‌ها). در سیستم‌های غیر ویندوز بی‌اثر است."""
    try:
        if window.tk.call("tk", "windowingsystem") != "win32":
            return False
        hwnd = get_real_window_hwnd(window)
        if not hwnd:
            return False
        def to_colorref(value):
            value = value.lstrip("#")
            r = int(value[0:2], 16)
            g = int(value[2:4], 16)
            b = int(value[4:6], 16)
            return ctypes.c_int(r | (g << 8) | (b << 16))
        DWMWA_CAPTION_COLOR = 35
        DWMWA_TEXT_COLOR = 36
        dwmapi = ctypes.windll.dwmapi
        caption = to_colorref(hex_color)
        result = dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd),
            DWMWA_CAPTION_COLOR,
            ctypes.byref(caption),
            ctypes.sizeof(caption),
        )
        if text_color:
            text = to_colorref(text_color)
            dwmapi.DwmSetWindowAttribute(
                ctypes.c_void_p(hwnd),
                DWMWA_TEXT_COLOR,
                ctypes.byref(text),
                ctypes.sizeof(text),
            )
        return result == 0
    except Exception as e:
        return False
def schedule_title_bar_color(window, delay=300):
    """تغییر رنگ نوار عنوان پس از آماده‌شدن پنجره."""
    def apply_color():
        try:
            if not window.winfo_exists():
                return
            window.update_idletasks()
            set_title_bar_color(
                window,
                COLORS["primary"],
            )
        except tk.TclError:
            pass
    return window.after(delay, apply_color)
