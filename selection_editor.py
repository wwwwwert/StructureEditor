import tkinter.messagebox as mb
from tkinter import *
import cv2
from PIL import Image, ImageTk
from drawing_tools import DrawingTools
import dialogs
import detecting_circles
from objects_manager import ObjectsManager


def check_circle_on_canvas(items, x0, y0, og_radius):
    for circle in items.keys():
        type, x, y, radius = items[circle]
        if (int(x0) // 5, int(y0) // 5, int(og_radius) // 5) == (
                int(x) // 5, int(y) // 5, int(radius) // 5):
            return True
    return False


class SelectionEditor:
    def __init__(self):
        self.image_path = None
        self.image_tab = None
        self.image = Image.Image
        self.unit_type = None
        self.pixel_proportion = 0
        self.image_proportion = 0
        self.highlightthickness = 5

        self.screen_width = None
        self.screen_height = None

        self.selection_canvas = None
        self.markup_canvas = None

        self.objects_manager = ObjectsManager()
        self.dnd_item = None
        self.markup_is_generated = False

        self.drawing_tools = None
        self.config = None

    def init(self, image_path, image_tab, interface_config):
        self.config = interface_config.config
        self.image_path = image_path
        self.image_tab = image_tab
        self.image = Image.open(self.image_path, mode='r')
        self.screen_width = image_tab.winfo_screenwidth()
        self.screen_height = image_tab.winfo_screenheight()

        og_width, og_height = self.image.size
        if og_width >= og_height:
            size = int((self.screen_width - 60) / 2)
            self.image = self.image.resize(
                (size, int(og_height / og_width * size)),
                Image.ANTIALIAS)
            self.image_proportion = size / og_width
        else:
            size = int(self.screen_height - 70)
            self.image = self.image.resize(
                (int(og_width / og_height * size), size),
                Image.ANTIALIAS)
            self.image_proportion = size / og_height

        image_tk = ImageTk.PhotoImage(self.image)

        self.selection_canvas = Canvas(image_tab, width=image_tk.width(),
                                       height=image_tk.height(), bd=0,
                                       highlightthickness=5,
                                       highlightbackground="black")
        self.selection_canvas.image = image_tk
        self.selection_canvas.create_image(5, 5, image=image_tk, anchor="nw")
        self.selection_canvas.pack(side="left", expand="yes")

        self.markup_canvas = Canvas(image_tab, width=image_tk.width(),
                                    height=image_tk.height(), bd=0,
                                    highlightthickness=5,
                                    highlightbackground="black")
        self.markup_canvas.pack(side="right", expand="yes")

        self.drawing_tools = DrawingTools(self.selection_canvas,
                                          self.markup_canvas, interface_config)

        self.markup_is_generated = False

    def start_ellipse_area_selection(self):
        if self.selection_canvas is None:
            mb.showwarning("Warning", "No image opened")
            return

        def func():
            self.add_drawn_item()
            self.start_ellipse_area_selection()

        self.drawing_tools.func_to_call = func
        self.drawing_tools.draw_ellipse()

    def start_circle_area_selection(self):
        if self.selection_canvas is None:
            mb.showwarning("Warning", "No image opened")
            return

        def func():
            self.add_drawn_item()
            self.start_circle_area_selection()

        self.drawing_tools.func_to_call = func
        self.drawing_tools.draw_circle()

    def start_circle_area_selection_with_detect(self):
        if self.selection_canvas is None:
            mb.showwarning("Warning", "No image opened")
            return

        def func():
            self.add_drawn_item()
            fig_type, id_tag, radius, x, y = self.drawing_tools.created_object_specs
            self.find_circles_with_radius(radius)
            self.start_circle_area_selection_with_detect()

        self.drawing_tools.func_to_call = func
        self.drawing_tools.draw_circle()

    def find_circles_with_radius(self, radius):
        method = dialogs.ask_detect_method(
            ["DistanceTransform", "Filter2D", "HoughCircles"])
        circles = list()
        if method == "DistanceTransform":
            circles = detecting_circles.find_circles_with_radius_distance(
                self.image_path,
                radius / self.image_proportion)
        elif method == "Filter2D":
            circles = detecting_circles.find_circles_with_radius_filter2d(
                self.image_path,
                radius / self.image_proportion)
        elif method == "HoughCircles":
            circles = detecting_circles.find_circles_with_radius_hough(
                self.image_path,
                radius / self.image_proportion)
        dash = (self.config["dash"]["dash"], self.config["dash"]["space"])
        outline = self.config["circle_outline"]
        # outline = '#' + hex(random.randint(273, 4095))[2:]

        width = self.config["line_width"]
        for x_img, y_img, radius_img in circles:
            item = self.drawing_tools.get_id_tag()
            radius = radius_img * self.image_proportion
            x = x_img * self.image_proportion
            y = y_img * self.image_proportion
            x += self.highlightthickness
            y += self.highlightthickness
            if check_circle_on_canvas(self.objects_manager.created_items, x, y,
                                      radius):
                continue
            self.selection_canvas.create_oval(x + radius, y + radius,
                                              x - radius, y - radius,
                                              dash=dash, fill='',
                                              tags=("draggable", item),
                                              outline=outline, width=width)
            self.markup_canvas.create_oval(x + radius, y + radius,
                                           x - radius, y - radius,
                                           dash=dash, fill='',
                                           tags=("draggable", item),
                                           outline=outline, width=width)
            self.drawing_tools.created_object_specs = (
                "circle", item, radius, x, y)
            self.add_drawn_item()

    def start_polyhedron_area_selection(self):
        if self.selection_canvas is None:
            mb.showwarning("Warning", "No image opened")
            return
        self.drawing_tools.func_to_call = self.add_drawn_item

        def create_polyhedron(button):
            button.destroy()
            self.drawing_tools.create_polyhedron()

        finish_btn = Button(self.image_tab,
                            text="Finish",
                            command=lambda: create_polyhedron(finish_btn),
                            font="Arial 30")

        finish_btn.place(relx=0.5, rely=0.05, anchor=CENTER)
        self.drawing_tools.finish_btn = finish_btn
        self.drawing_tools.draw_polyhedron()

    def start_custom_area_selection(self):
        if self.selection_canvas is None:
            mb.showwarning("Warning", "No image opened")
            return

        def func():
            self.add_drawn_item()
            self.start_custom_area_selection()

        self.drawing_tools.func_to_call = func
        self.drawing_tools.draw_custom_area()

    def add_drawn_item(self):
        specs = self.drawing_tools.created_object_specs
        if specs is None:
            return
        print(specs)
        if specs[0] == "circle":
            self.objects_manager.add_circle(specs)
        elif specs[0] == "ellipse":
            self.objects_manager.add_ellipse(specs)
        elif specs[0] == "polyhedron":
            self.objects_manager.add_polyhedron(specs)
        elif specs[0] == "amorphous":
            self.objects_manager.add_amorphous(specs)

    def start_unit_line_selection(self):
        if self.selection_canvas is None:
            mb.showwarning("Warning", "No image opened")
            return
        if self.drawing_tools.unit_line_tag is not None:
            self.selection_canvas.delete(self.drawing_tools.unit_line_tag)
            self.markup_canvas.delete(self.drawing_tools.unit_line_tag)
            self.drawing_tools.unit_line_tag = None
        self.drawing_tools.func_to_call = self.get_unit_line_size
        self.drawing_tools.draw_unit_line()

    def get_unit_line_size(self, unit_len):
        self.unbind_canvas()
        length, self.unit_type = dialogs.ask_unit_len()
        # length_dialog = simpledialog.askinteger(title="Input unit length",
        #                                                          prompt="length:")
        if length is None:
            self.selection_canvas.delete(self.drawing_tools.unit_line_tag)
            self.markup_canvas.delete(self.drawing_tools.unit_line_tag)
            self.drawing_tools.unit_line_tag = None
            return
        self.pixel_proportion = length / unit_len

    def move_selection(self):
        if self.selection_canvas is None:
            mb.showwarning("Warning", "No image opened")
            return

        if len(self.objects_manager.created_items) == 0:
            mb.showwarning("Warning", "Create markup first")
            return

        self.unbind_canvas()

        self.selection_canvas.tag_bind("draggable", "<ButtonPress-1>",
                                       self.move_selection_button_press)
        self.selection_canvas.tag_bind("draggable", "<Button1-Motion>",
                                       self.move_selection_button_motion)

    def move_selection_button_press(self, event):
        item = self.selection_canvas.find_withtag(CURRENT)
        for tag in self.selection_canvas.gettags(item[0]):
            if tag.find("tag") == 0:
                self.dnd_item = (tag, event.x, event.y)

    def move_selection_button_motion(self, event):
        x, y = event.x, event.y
        item, x0, y0 = self.dnd_item
        self.selection_canvas.move(item, x - x0, y - y0)
        self.markup_canvas.move(item, x - x0, y - y0)
        self.dnd_item = (item, x, y)

    def start_removing_selection(self):
        if self.selection_canvas is None:
            mb.showwarning("Warning", "No image opened")
            return

        if len(self.objects_manager.created_items) == 0:
            mb.showwarning("Warning", "Create markup first")
            return

        self.unbind_canvas()
        self.selection_canvas.tag_bind("draggable", "<ButtonPress-1>",
                                       self.remove_selection_button_press)

    def remove_selection_button_press(self, event):
        item = self.selection_canvas.find_withtag(CURRENT)
        item = item[0]
        for tag in self.selection_canvas.gettags(item):
            if tag.find("tag") == 0:
                item = tag
                break

        if item == self.drawing_tools.unit_line_tag:
            mb.showwarning("Warning",
                           "To create new unit line use \"Select unit line\" function")
            return

        self.objects_manager.created_items.pop(item)
        self.selection_canvas.delete(item)
        self.markup_canvas.delete(item)

    def remove_all_selection(self):
        if self.selection_canvas is None:
            mb.showwarning("Warning", "No image opened")
            return

        if len(self.objects_manager.created_items) == 0:
            mb.showwarning("Warning", "Create markup first")
            return

        self.unbind_canvas()
        if not mb.askyesno("Remove all selection", "Clear all markup?"):
            return

        for item in self.objects_manager.created_items.keys():
            self.selection_canvas.delete(item)
            self.markup_canvas.delete(item)
        self.objects_manager.created_items.clear()

        self.markup_is_generated = False
        self.selection_canvas.delete(self.drawing_tools.unit_line_tag)
        self.drawing_tools.unit_line_tag = None

    def generate_markup(self):
        if self.selection_canvas is None:
            mb.showwarning("Warning", "No image opened")
            return

        if (not mb.askyesno("Generate markup",
                            "Automatic markup generation works only " +
                            "with images of flat spherical structures. " +
                            "Structures in the shots should not have shadows.\n\n" +
                            "Do you want to continue?")):
            return

        if self.selection_canvas is None or self.markup_is_generated:
            return

        self.markup_is_generated = True
        self.unbind_canvas()

        im = cv2.imread(self.image_path)

        # im = cv2.GaussianBlur(im, (7, 7), 0)
        # im = cv2.medianBlur(im, 7)
        # im = cv2.blur(im, (3, 3))

        hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
        th, bw = cv2.threshold(hsv[:, :, 2], 0, 255,
                               cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        # laplacian_filtered = cv2.Laplacian(bw, cv2.CV_8UC1)
        # if (cv2.Laplacian(bw, cv2.CV_8UC1).var() - cv2.Laplacian(
        #         bw - laplacian_filtered, cv2.CV_8UC1).var() > 45):
        #     bw = bw - cv2.Laplacian(bw, cv2.CV_8UC1)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        morph = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel)
        dist = cv2.distanceTransform(morph, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
        borderSize = 30
        distborder = cv2.copyMakeBorder(dist, borderSize, borderSize,
                                        borderSize, borderSize,
                                        cv2.BORDER_CONSTANT | cv2.BORDER_ISOLATED,
                                        0)
        gap = 10
        kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (
            2 * (borderSize - gap) + 1, 2 * (borderSize - gap) + 1))
        kernel2 = cv2.copyMakeBorder(kernel2, gap, gap, gap, gap,
                                     cv2.BORDER_CONSTANT | cv2.BORDER_ISOLATED,
                                     0)
        distTempl = cv2.distanceTransform(kernel2, cv2.DIST_L2,
                                          cv2.DIST_MASK_PRECISE)
        nxcor = cv2.matchTemplate(distborder, distTempl, cv2.TM_CCOEFF_NORMED)
        mn, mx, _, _ = cv2.minMaxLoc(nxcor)
        th, peaks = cv2.threshold(nxcor, mx * 0.5, 255, cv2.THRESH_BINARY)
        peaks8u = cv2.convertScaleAbs(peaks)
        contours, hierarchy = cv2.findContours(peaks8u, cv2.RETR_CCOMP,
                                               cv2.CHAIN_APPROX_SIMPLE)
        peaks8u = cv2.convertScaleAbs(peaks)  # to use as mask
        for i in range(len(contours)):
            x, y, w, h = cv2.boundingRect(contours[i])
            _, mx, _, mxloc = cv2.minMaxLoc(dist[y:y + h, x:x + w],
                                            peaks8u[y:y + h, x:x + w])
            radius = int(mx)
            if (radius < 10):
                continue

            item = self.selection_canvas.create_oval(
                (int(mxloc[0] + x) + radius) * self.image_proportion,
                (int(mxloc[1] + y) + radius) * self.image_proportion,
                (int(mxloc[0] + x) - radius) * self.image_proportion,
                (int(mxloc[1] + y) - radius) * self.image_proportion,
                dash=(10, 10), fill='',
                tags="draggable",
                outline="red", width=2)

            # self.drawing_tools.selection_to_markup_id[
            #     item] = self.markup_canvas.create_oval(
            #     (int(mxloc[0] + x) + radius) * self.image_proportion,
            #     (int(mxloc[1] + y) + radius) * self.image_proportion,
            #     (int(mxloc[0] + x) - radius) * self.image_proportion,
            #     (int(mxloc[1] + y) - radius) * self.image_proportion,
            #     dash=(10, 10), fill='',
            #     tags="draggable",
            #     outline="red", width=2)
            #
            # self.drawing_tools.objects_sizes[item] = math.pi * (
            #         (radius * self.image_proportion) ** 2)

    def unbind_canvas(self):
        self.drawing_tools.unbind_canvas()
