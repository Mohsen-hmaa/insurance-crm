import tkinter as tk
from tkinter import ttk
from gui.styles import schedule_title_bar_color
class InsuranceSelector(tk.Toplevel):
    def __init__(self,parent,root_types,callback):
        super().__init__(parent)
        self.title("انتخاب رشته بیمه")
        self.geometry("600x500")
        schedule_title_bar_color(self)
        self.callback=callback
        self.current_types=root_types
        self.level_stack=[root_types]
        self.selected_path=[]
        self.create_widgets()
        self.show_current_types()
    def create_widgets(self):
        tk.Label(
            self,
            text="مسیر_انتخاب:"
        ).pack(pady=5)
        self.path_label=tk.Label(
            self,
            text="",
            width=75,
            anchor="e"
        )
        self.path_label.pack(pady=5)
        tk.Label(
            self,
            text="انتخاب رشته"
        ).pack(pady=5)
        self.type_list=tk.Listbox(
            self,
            height=20,
            width=75,
            justify="right"
        )
        self.type_list.pack(pady=5)
        self.type_list.bind(
            "<<ListboxSelect>>",
            self.select_type
        )
        button_frame=tk.Frame(self)
        button_frame.pack(pady=15)
        self.back_button=tk.Button(
            button_frame,
            text="بازگشت",
            command=self.go_back
        )
        self.back_button.pack(
            side="left",
            padx=10
        )
        self.confirm_button=tk.Button(
            button_frame,
            text="تایید",
            command=self.confirm_selection
        )
        self.confirm_button.pack(
            side="right",
            padx=10
        )
        self.confirm_button.config(state="disabled")
    def go_back(self):
        if len(self.level_stack)<=1:
            self.selected_path.clear()
            self.path_label.config(
                text=""
            )
            self.current_types=self.level_stack[0]
            self.show_current_types()
            return
        self.level_stack.pop()
        self.current_types=self.level_stack[-1]
        self.selected_path=self.selected_path[:len(self.level_stack)-1]
        self.path_label.config(
            text=" > ".join(item.name for item in self.selected_path)
        )
        self.type_list.selection_clear(0, tk.END)
        self.confirm_button.config(state="disabled")
        self.show_current_types()
    def confirm_selection(self):
        if not self.selected_path:
            return
        last_item=self.selected_path[-1]
        if last_item.children:
            return
        self.callback(self.selected_path)
        self.destroy()
    def show_current_types(self):
        self.type_list.delete(
            0,
            tk.END
        )
        for item in self.current_types:
            self.type_list.insert(
                tk.END,
                item.name
            )
    def select_type(self, event=None):
        index = self.type_list.curselection()
        if not index:
            return
        selected = self.current_types[index[0]]
        current_level=len(self.level_stack)-1
        if len(self.selected_path)>current_level:
            self.selected_path[current_level]=selected
            self.selected_path=self.selected_path[:current_level+1]
        else:
            self.selected_path.append(selected)
        self.path_label.config(
            text=" > ".join(
                item.name for item in self.selected_path
            )
        )
        if selected.children:
            self.level_stack.append(selected.children)
            self.current_types=self.level_stack[-1]
            self.show_current_types()
        else:
            self.confirm_button.config(state="normal")