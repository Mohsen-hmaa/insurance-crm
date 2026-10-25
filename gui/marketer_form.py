import tkinter as tk
from tkinter import ttk
from gui.styles import COLORS, set_title_bar_color
from services.marketer_service import register_marketer,update_marketer
class MarketerForm:
    def __init__(
        self,
        parent=None,
        callback=None,
        marketer_name=None,
        marketer=None
    ):
        self.parent = parent
        self.callback = callback
        self.marketer_name = marketer_name
        self.marketer = marketer
        if parent:
            self.window = tk.Toplevel(parent)
        else:
            self.window = tk.Tk()
        self.window.title(
                "ویرایش بازاریاب"
                if marketer
                else "ثبت بازاریاب"
            )
        self.window.geometry("400x400")
        self.create_widgets()
        self.window.after(
            200,
            lambda: set_title_bar_color(
                self.window,
                COLORS["primary"],
            ),
        )
    def create_widgets(self):
        tk.Label(
            self.window,
            text="نام و نام خانوادگی"
        ).pack()
        self.name_entry=tk.Entry(
            self.window,
            width=40
        )
        self.name_entry.pack(pady=5)
        if self.marketer_name:
            self.name_entry.insert(0, self.marketer_name)
        tk.Label(
            self.window,
            text="درصد کارمزد بیمه شخص ثالث"
        ).pack()
        self.third_party_commission_entry=tk.Entry(
            self.window,
            width=40
        )
        self.third_party_commission_entry.pack(pady=5)
        tk.Label(
            self.window,
            text="درصد کارمزد سایر بیمه ها"
        ).pack()
        self.other_commission_entry=tk.Entry(
            self.window,
            width=40
        )
        self.other_commission_entry.pack(pady=5)
        if self.marketer:
            self.name_entry.insert(
                0,
                self.marketer.name
            )
            self.third_party_commission_entry.insert(
                0,
                str(self.marketer.third_party_commission)
            )
            self.other_commission_entry.insert(
                0,
                str(self.marketer.other_commission)
            )
        self.save_button=tk.Button(
            self.window,
            text="ذخیره",
            width=20,
            command=self.save_marketer
        )
        self.save_button.pack(pady=10)
    def save_marketer(self):
        data={
            "name":self.name_entry.get(),
            "third_party_commission":float(self.third_party_commission_entry.get()),
            "other_commission":float(self.other_commission_entry.get())
        }
        if self.marketer:
            marketer = update_marketer(
                self.marketer.id,
                data
            )
        else:
            marketer = register_marketer(data)
        if self.callback:
            self.callback(marketer)
            self.window.destroy()
            return
        self.clear_form()
    def clear_form(self):
        self.name_entry.delete(0, tk.END)
        self.third_party_commission_entry.delete(0, tk.END)
        self.other_commission_entry.delete(0, tk.END)
def open_marketer_form():
    form=MarketerForm()
    form.window.mainloop()
if __name__=="__main__":
    open_marketer_form()