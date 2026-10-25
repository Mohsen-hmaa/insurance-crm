"""
نگهداری «یک پنجره برای هر گزارش».

هر گزارش با یک کلید (مثلاً "commission_period") ثبت می‌شود. اگر دوباره
همان گزارش باز شود و پنجره‌اش هنوز باز باشد، به‌جای ساختن پنجره‌ی تکراری،
همان پنجره از حالت کوچک‌شده بیرون می‌آید و جلو می‌آید.
"""

import tkinter as tk


# کلید گزارش -> پنجره‌ی باز آن گزارش
_windows = {}


def _is_alive(window):
    try:
        return window is not None and bool(window.winfo_exists())
    except tk.TclError:
        return False


def focus_existing(key):
    """
    اگر پنجره‌ی این گزارش باز است آن را جلو می‌آورد و True برمی‌گرداند.
    در غیر این صورت False.
    """
    window = _windows.get(key)

    if not _is_alive(window):
        _windows.pop(key, None)
        return False

    window.deiconify()      # از حالت minimize یا مخفی بیرون می‌آید
    window.lift()
    window.focus_force()
    return True


def register_window(key, window):
    """پنجره را برای این گزارش ثبت می‌کند؛ با بسته شدن پنجره، ثبت پاک می‌شود."""
    _windows[key] = window

    def on_destroy(event, key=key, window=window):
        # این رویداد برای ویجت‌های داخل پنجره هم می‌آید؛ فقط خود پنجره مهم است
        if event.widget is window and _windows.get(key) is window:
            del _windows[key]

    window.bind("<Destroy>", on_destroy, add="+")


class SingleWindowMixin:
    """
    برای کلاس‌های گزارش (که خودشان tk.Toplevel هستند) استفاده می‌شود:

        class CommissionReports(SingleWindowMixin, tk.Toplevel): ...

    صفحه‌ی گزارش‌ها برای هر باز کردن یک Toplevel مخفی از همین کلاس می‌سازد.
    اگر پنجره‌ی گزارش از قبل باز باشد، آن Toplevel مخفی دیگر لازم نیست و
    بسته می‌شود تا با هر کلیک اضافه روی هم جمع نشود.
    """

    def reuse_window(self, key):
        if not focus_existing(key):
            return False

        try:
            if self.state() == "withdrawn":
                self.destroy()
        except tk.TclError:
            pass

        return True
