import os
from tkinter import *
from tkinter import filedialog as fd
from tkinter.ttk import Notebook
import tkinter.messagebox as mb

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from selection_editor import SelectionEditor
from plot_editor import PlotEditor
from sizes_table import SizesTable
from interface_config import InterfaceConfig


class MicrostructurePhotoEditor:
    def __init__(self):
        self.root = Tk()
        self.root.attributes('-fullscreen', True)
        self.root.state('zoomed')
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        self.menu = None

        self.image_tabs = Notebook(self.root)
        self.graph_tab = None
        self.table_tab = None
        self.plot_editor = PlotEditor()
        self.selection_editor = SelectionEditor()
        self.sizes_table = SizesTable()
        self.interface_config = InterfaceConfig(self.root.winfo_fpixels('1i'),
                                                self.screen_width,
                                                self.screen_height)
        self.init()

    def init(self):
        self.root.title("Microstructure Photo Editor")
        self.image_tabs.enable_traversal()
        self.root.bind("<Escape>", self._close)

    def run(self):
        self.draw_menu()
        self.create_main_page()
        self.root.mainloop()

    def draw_menu(self):
        if self.menu is not None:
            self.root.forget(self.menu)

        menu_bar = Menu(self.root)

        file_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open",
                              command=self.open_new_image)

        selection_menu = Menu(menu_bar, tearoff=0)
        creating_selection_menu = Menu(selection_menu, tearoff=0)
        creating_selection_menu.add_command(label="Сircle selection",
                                            command=self.selection_editor.start_circle_area_selection)
        creating_selection_menu.add_command(
            label="Сircle selection with auto-detection",
            command=self.selection_editor.start_circle_area_selection_with_detect)
        creating_selection_menu.add_command(label="Ellipse selection",
                                            command=self.selection_editor.start_ellipse_area_selection)
        creating_selection_menu.add_command(label="Polyhedron selection",
                                            command=self.selection_editor.start_polyhedron_area_selection)
        creating_selection_menu.add_command(label="Amorphous area selection",
                                            command=self.selection_editor.start_custom_area_selection)
        # creating_selection_menu.add_command(label="Generate markup",
        #                                     command=self.selection_editor.generate_markup)
        creating_selection_menu.add_command(label="Select unit line",
                                            command=self.selection_editor.start_unit_line_selection)
        selection_menu.add_cascade(label="Create selection",
                                   menu=creating_selection_menu)

        editing_selection_menu = Menu(selection_menu, tearoff=0)
        editing_selection_menu.add_command(label="Move selection",
                                           command=self.selection_editor.move_selection)
        editing_selection_menu.add_command(label="Remove selection",
                                           command=self.selection_editor.start_removing_selection)
        editing_selection_menu.add_command(label="Remove all",
                                           command=self.selection_editor.remove_all_selection)
        selection_menu.add_cascade(label="Edit selection",
                                   menu=editing_selection_menu)

        menu_bar.add_cascade(label="Selection", menu=selection_menu)

        plot_menu = Menu(menu_bar, tearoff=0)
        plot_menu.add_command(label="Build graph and table",
                              command=self.build_plot_and_table)
        plot_menu.add_command(label="Save graph",
                              command=self.plot_editor.save_plot)
        menu_bar.add_cascade(label="Statistics", menu=plot_menu)

        self.root.configure(menu=menu_bar)

    def create_main_page(self):
        self.image_tabs.pack(fill="both", expand=1)
        contacts_tab = Frame(self.image_tabs)
        contacts_canvas = Canvas(contacts_tab, width=400,
                                 height=200, bd=0,
                                 highlightthickness=0)
        contacts_canvas.pack(expand="yes")
        contacts_canvas.create_text(10, 10,
                                    text="by Uspenskiy Dmitry\ntelegram: @black_chick\n" +
                                         "mail: uspenskiydmitry@gmail.com",
                                    anchor=NW, font="Verdana 14")

        contacts_canvas.create_text(390, 190,
                                    text="HSE University, 2022",
                                    anchor=SE, font="Verdana 14", fill="grey")

        self.image_tabs.add(contacts_tab)

    def open_new_image(self):
        path = fd.askopenfilename(
            filetypes=(("Images", "*.bmp *.png *.jpg *.jpeg"),))
        if not path:
            return

        while self.image_tabs.select():
            self.image_tabs.forget(self.image_tabs.select())
            self.graph_tab = None

        image_tab = Frame(self.image_tabs,
                          width=self.screen_width,
                          height=self.screen_height)

        self.selection_editor = SelectionEditor()
        self.selection_editor.init(path, image_tab, self.interface_config)

        self.image_tabs.add(image_tab, text=path.split("/")[-1])
        self.image_tabs.select(image_tab)

        self.draw_menu()

    def build_plot_and_table(self):
        if self.selection_editor.selection_canvas is None:
            mb.showwarning("Warning", "No image opened")
            return

        if len(self.selection_editor.objects_manager.created_items) == 0:
            mb.showwarning("Warning", "Create markup first")
            return

        if self.selection_editor.drawing_tools.unit_line_tag is None:
            mb.showwarning("Warning", "Select unit line first")
            return

        self.selection_editor.unbind_canvas()

        if self.graph_tab is not None:
            self.image_tabs.forget(self.graph_tab)

        if self.table_tab is not None:
            self.image_tabs.forget(self.table_tab)

        self.table_tab = Frame(self.image_tabs)
        self.sizes_table.init(self.selection_editor, self.table_tab)
        self.image_tabs.add(self.table_tab, text="Table")

        self.graph_tab = Frame(self.image_tabs)
        self.plot_editor.init(self.selection_editor)

        canvas = FigureCanvasTkAgg(self.plot_editor.figure,
                                   master=self.graph_tab)
        canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        canvas.draw()

        self.image_tabs.add(self.graph_tab, text="Plot")
        self.image_tabs.select(self.graph_tab)

    def _close(self, event):
        self.root.attributes('-fullscreen', False)


if __name__ == "__main__":
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        os.chdir(sys._MEIPASS)
    MicrostructurePhotoEditor().run()
