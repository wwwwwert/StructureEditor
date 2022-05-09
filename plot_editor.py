import math
import tkinter.messagebox as mb
import numpy as np
from matplotlib.figure import Figure
from scipy import interpolate
from tkinter import filedialog as fd


class PlotEditor:
    def __init__(self):
        self.selection_editor = None
        self.figure = None
        self.total_size = 0

    def init(self, selection_editor):
        self.selection_editor = selection_editor
        self.create_plot_figure()

    def create_plot_figure(self):
        # figure = Figure(figsize=(5, 4), dpi=100)
        self.figure = Figure()

        for group in self.selection_editor.objects_manager.groups:
            self.total_size += group.total_size

        for group in self.selection_editor.objects_manager.groups:
            self.add_group(group)

        self.figure.tight_layout()


    def add_group(self, group):
        plt = self.figure.add_subplot(3, 3, group.id)
        plt.set_ylim([0, 100])

        width = 0.24 * group.main_size

        total_left_size = 0
        for line in group.left_col:
            total_left_size += float(line[-1])
        left_center = (0.64 + 0.24 / 2) * group.main_size
        percentage = total_left_size / self.total_size * 100
        plt.bar(left_center, percentage, width=width, color="skyblue",
                     label="64% - 88%")

        total_main_size = 0
        for line in group.main_col:
            total_main_size += float(line[-1])
        percentage = total_main_size / self.total_size * 100
        plt.bar(group.main_size, percentage, width=width, color="forestgreen",
                     label="88% - 112%")
        plt.annotate("Group " + str(group.id),
                          (group.main_size - width / 4, percentage + 2),
                          fontsize=10)

        total_right_size = 0
        for line in group.right_col:
            total_right_size += float(line[-1])
        right_center = (1.12 + 0.24 / 2) * group.main_size
        percentage = total_right_size / self.total_size * 100
        plt.bar(right_center, percentage, width=width, color="darkkhaki",
                     label="112% - 136%")

        xlabel = "Sizes of structures ($" + self.selection_editor.unit_type + "^2$)"
        plt.set_xlabel(xlabel)
        plt.set_ylabel("Area percentage")
        plt.legend(loc='upper left')


    def save_plot(self):
        if self.figure is None:
            mb.showwarning("Warning", "Build the graph first.\n" +
                           "Use \"Show graph\" function")
            return

        graph_pass = fd.asksaveasfilename(
            filetypes=(("Image files", "*.png *.bmp *.jpg *.jpeg"),))

        if graph_pass is None:
            return

        self.figure.savefig(graph_pass)
