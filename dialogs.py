from tkinter import *
from tkinter import simpledialog
from tkinter.ttk import Combobox
import tkinter.messagebox as mb


def ask_unit_len():
    values = ['millimeters', 'micrometers', 'nanometers']
    top = Toplevel()
    top.geometry('200x100')
    top.resizable(False, False)
    top.focus_set()
    top.grab_set()
    top.title('Enter length and units')

    label_length = Label(top, text='Length:')
    label_length.grid(row=0, column=0, padx=3, pady=3)

    units_type = StringVar()
    length = StringVar()

    answer_entry = Entry(top, textvariable=length, width=10)
    answer_entry.grid(row=0, column=1, padx=3, pady=3)

    label_units = Label(top, text='Units:')
    label_units.grid(row=1, column=0, padx=3, pady=3)

    combo = Combobox(top, width=10, textvariable=units_type,
                     values=values)
    combo.grid(row=1, column=1, padx=3, pady=3)

    button = Button(top, text='Enter',
                    command=lambda:
                    mb.showwarning("Warning",
                                   "Enter all parameters correctly")
                    if (units_type.get() == "" or not length.get().isdigit()
                        or length.get() == '' or int(length.get()) <= 0)
                    else [top.grab_release(), top.destroy()])
    button.grid(row=2, column=0, columnspan=2, padx=3, pady=3)

    top.wait_window(top)
    answer_entry.destroy()
    combo.destroy()
    if length.get() == '':
        return None, None
    return int(length.get()), units_type.get()


def ask_bounding_figure(options):
    top = Toplevel()
    top.geometry('200x60')
    # top.protocol("WM_DELETE_WINDOW", lambda: ())
    top.resizable(False, False)
    top.focus_set()
    top.grab_set()
    bound_type = StringVar()
    box = Combobox(top, values=options, textvariable=bound_type)
    # box.current(1)
    box.place(relx=0.5, rely=0, anchor="n")
    button = Button(top, text='Enter',
                    command=lambda:
                    mb.showwarning("Warning",
                                   "Enter all parameters correctly")
                    if box.get() not in options
                    else [top.grab_release(), top.destroy()])
    button.place(relx=0.5, rely=0.9, anchor="s")
    top.wait_window(top)
    box.destroy()
    return bound_type.get()


def ask_detect_method(options):
    top = Toplevel()
    top.geometry('200x60')
    # top.protocol("WM_DELETE_WINDOW", lambda: ())
    top.resizable(False, False)
    top.focus_set()
    top.grab_set()
    bound_type = StringVar()
    box = Combobox(top, values=options, textvariable=bound_type)
    # box.current(1)
    box.place(relx=0.5, rely=0, anchor="n")
    button = Button(top, text='Enter',
                    command=lambda:
                    mb.showwarning("Warning",
                                   "Enter all parameters correctly")
                    if box.get() not in options
                    else [top.grab_release(), top.destroy()])
    button.place(relx=0.5, rely=0.9, anchor="s")
    top.wait_window(top)
    box.destroy()
    return bound_type.get()


class UnitLineDialog(simpledialog.Dialog):
    def body(self, master):
        values = ['millimeters', 'micrometers', 'nanometers']

        Label(master, text="Length:").grid(row=0)
        Label(master, text="Units:").grid(row=1)

        self.units_type = StringVar()
        self.length = StringVar()

        self.entry = Entry(master, textvariable=self.length)
        self.combo = Combobox(master, textvariable=self.units_type,
                              values=values)

        self.entry.grid(row=0, column=1)
        self.combo.grid(row=1, column=1)
        return self.entry  # initial focus

    def apply(self):
        return self.units_type.get(), self.length.get()
