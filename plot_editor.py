import tkinter.messagebox as mb
import pandas as pd
import seaborn as sns
import dataframe_image as dfi
from tkinter import filedialog as fd


class PlotEditor:
    def __init__(self):
        self.selection_editor = None
        self.figure = None
        self.total_size = 0
        self.objects_data = None

    def init(self, selection_editor):
        self.selection_editor = selection_editor
        self.create_plot_figure()

    def create_plot_figure(self):
        self.objects_data = pd.DataFrame(
            self.selection_editor.objects_manager.lines,
            columns=['structure type', 'bound figure type', 'radius',
                     'size'])
        xlabel = "Sizes of structures ($" + self.selection_editor.unit_type + "^2$)"

        plt = sns.displot(x='size', stat='percent', data=self.objects_data,
                          hue='structure type', multiple='dodge')
        plt.set(xlabel=xlabel)
        self.figure = plt.fig

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

    def save_table(self):
        if self.figure is None:
            mb.showwarning("Warning", "Build the graph first.\n" +
                           "Use \"Show graph\" function")
            return

        table_pass = fd.asksaveasfilename(
            filetypes=(("Image files", "*.png *.csv"),))

        if table_pass is None or '.' not in table_pass:
            return

        format = table_pass.split('.')[-1]
        if format == 'png':
            lines = list()
            for st, bound, rad, sz in self.selection_editor.objects_manager.lines:
                print((st, bound, rad.replace('\t', ' '), sz))
                lines.append((st, bound, rad.replace('\t', ' '), sz))
            sdata = pd.DataFrame(lines, columns=['structure type',
                                                 'bound figure type', 'radius',
                                                 'size'])
            dfi.export(self.objects_data, table_pass)
        elif format == 'csv':
            self.objects_data.to_csv(table_pass)
