import math
from tkinter import ttk
from tkinter import END


class SizesTable:
    def __init__(self):
        self.selection_editor = None
        self.frame = None
        self.lines = list()
        self.tree = None

    def init(self, selection_editor, frame):
        self.selection_editor = selection_editor
        self.frame = frame
        self.configure_style()
        self.selection_editor.objects_manager.group_objects(
            self.selection_editor.pixel_proportion)
        self.create_table()

    def configure_style(self):
        style = ttk.Style()
        style.configure("mystyle.Treeview", highlightthickness=0, bd=0,
                        font=('Calibri', 11))  # Modify the font of the body
        style.configure("mystyle.Treeview.Heading", font=(
            'Calibri', 13, 'bold'))  # Modify the font of the headings
        style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {
            'sticky': 'nswe'})])  # Remove the borders

    def create_table(self):
        columns = ("type", "bound", "radius", "area")

        self.tree = ttk.Treeview(self.frame, columns=columns, height=20)

        self.tree.heading('#0', text='Id')
        self.tree.heading("type", text="Structure Type")
        self.tree.heading("bound", text="Bounding Figure")
        self.tree.heading("radius", text=(
                "Radius" + ' (' + self.selection_editor.unit_type + ')'))
        self.tree.heading("area", text=(
                "Area" + ' (' + self.selection_editor.unit_type + ' ^ 2)'))

        self.tree.pack(padx=5, pady=5)

        for group in self.selection_editor.objects_manager.groups:
            self.add_group(group)

    def add_group(self, group):
        index = self.tree.insert('', END, text="Group " + str(group.id),
                                 values=('', '', '', group.total_size))
        self.add_subgroup(index, "64% - 88%", group.left_col)
        self.add_subgroup(index, "88% - 112%", group.main_col)
        self.add_subgroup(index, "112% - 136%", group.right_col)

    def add_subgroup(self, parent, text, subgroup):
        if len(subgroup) == 0:
            return

        total_size = 0
        for _, _, _, _, size in subgroup:
            total_size += float(size)
        id = self.tree.insert(parent, END, text=text,
                              values=('', '', '', total_size))
        for line in subgroup:
            self.tree.insert(id, END, text=line[0],
                             values=(line[1], line[2], line[3], line[4]))
