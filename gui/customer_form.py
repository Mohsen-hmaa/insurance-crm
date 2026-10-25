import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from gui.styles import COLORS, set_title_bar_color
from services.customer_service import register_customer,update_customer
class CustomerForm:
    def __init__(self,parent=None, on_save=None,customer=None):
        self.parent=parent
        if parent:
            self.window=tk.Toplevel(parent)
        else:
            self.window=tk.Tk()
        self.on_save=on_save
        self.customer=customer
        self.window.geometry("400x400")
        if self.customer:
            self.window.title("ویرایش بیمه‌گذار")
        else:
            self.window.title("ثبت بیمه‌گذار")
        self.create_widgets()
        self.window.after(
            200,
            lambda: set_title_bar_color(
                self.window,
                COLORS["primary"],
            ),
        )
        if self.customer:
           self.fill_customer_data()
    def create_widgets(self):
        tk.Label(
            self.window,
            text="نام"
        ).pack()
        self.name_entry = tk.Entry(self.window)
        self.name_entry.pack()
        tk.Label(
            self.window,
            text="نام خانوادگی"
        ).pack()
        self.family_entry = tk.Entry(self.window)
        self.family_entry.pack()
        tk.Label(
            self.window,
            text=" تلفن همراه"
        ).pack()
        self.phone_entry = tk.Entry(self.window)
        self.phone_entry.pack()
        tk.Label(
            self.window,
            text="نوع مشتری"
        ).pack()
        self.customer_type =ttk.Combobox(
            self.window,
            values=["حقیقی", "حقوقی"],
            state="readonly"
        )
        self.customer_type.current(0)
        self.customer_type.pack()
        tk.Label(
            self.window,
            text=" کد ملی /شناسه ملی"
        ).pack()
        self.national_id_entry = tk.Entry(self.window)
        self.national_id_entry.pack()
        tk.Label(
            self.window,
            text="کد مشتری"
        ).pack()
        self.customer_code_entry = tk.Entry(
            self.window,
            state="readonly" if self.customer else "normal"
            )
        self.customer_code_entry.pack()
        self.save_button=tk.Button(
        self.window,
        width=20,
        background="#CDCCCC",
        text="ویرایش بیمه گذار" if self.customer else "ثبت بیمه گذار",
        command=self.save_customer    
        )
        self.save_button.pack(pady=20)
    def validate_form(self):
        if not self.name_entry.get():
            messagebox.showerror(
                "خطا",
                "مقدار نام را وارد کنید",
                parent=self.window
                )
            return False
        if not self.customer_type.get():
            messagebox.showerror(
                "خطا",
                "نوع مشتری را انتخاب کنید",
                parent=self.window
                )
            return False
        if not self.national_id_entry.get():
            messagebox.showerror(
                "خطا",
                "مقدار کد ملی/شناسه ملی را وارد کنید",
                parent=self.window
                )
            return False
        if self.customer_type.get()=="حقیقی":
            if len(self.national_id_entry.get())!=10 or not self.national_id_entry.get().isdigit():
                messagebox.showerror(
                    "خطا",
                    "فرمت کد ملی وارد شده صحیح نمی باشد ",
                    parent=self.window
                )
                return False
        else:
            if len(self.national_id_entry.get())!=11 or not self.national_id_entry.get().isdigit():
                messagebox.showerror(
                    "خطا",
                    "فرمت شناسه ملی وارد شده صحیح نمی باشد",
                    parent=self.window
                )
                return False
        if not self.customer_code_entry.get():
            messagebox.showerror(
                "خطا",
                "کد مشتری را وارد کنید",
                parent=self.window
                )
            return False
        return True
    def save_customer(self):
        if not self.validate_form():
            return       
        data={
            "name":self.name_entry.get(),
            "family":self.family_entry.get(),
            "phone":self.phone_entry.get(),
            "customer_type":self.customer_type.get(),
            "national_id":self.national_id_entry.get(),
            "customer_code":self.customer_code_entry.get()
        }
        try:
            if self.customer:
                customer=update_customer(
                    self.customer.id,
                    data
                )
                messagebox.showinfo("موفق"
                                     ,"اطلاعات مشتری با موفقیت ویرایش شد",
                                    parent=self.window
                                    )   
            else:
                customer=register_customer(data)
                messagebox.showinfo("موفق"
                                    ,"اطلاعات مشتری با موفقیت ثبت گردید",
                                    parent=self.window)
            if self.on_save:
                self.on_save(customer)
            if self.parent:
                self.window.destroy()
            else:
                self.clear_form()
        except Exception as e:
            messagebox.showerror(
                "خطا",
                str(e),
                parent=self.window
            )
    def clear_form(self):
        self.name_entry.delete(0,tk.END)
        self.family_entry.delete(0,tk.END)
        self.phone_entry.delete(0,tk.END)
        self.customer_type.set("")
        self.national_id_entry.delete(0,tk.END)
        self.customer_code_entry.delete(0,tk.END)
    def fill_customer_data(self):
        self.name_entry.insert(0, self.customer.name or "")
        self.family_entry.insert(0, self.customer.family or "")
        self.phone_entry.insert(0, self.customer.phone or "")
        self.customer_type.set(self.customer.customer_type or "")
        self.national_id_entry.insert(0, self.customer.national_id or "")
        self.customer_code_entry.config(state="normal")
        self.customer_code_entry.insert(
            0,
            self.customer.customer_code or ""
        )
        self.customer_code_entry.config(state="readonly")
def open_customer_form(parent=None,on_save=None,customer=None):
    form=CustomerForm(
        parent=parent,
        on_save=on_save,
        customer=customer
    )
    form.window.wait_window()
if __name__=="__main__":
    open_customer_form()