import math
import shapely.geometry
from dialogs import ask_bounding_figure


def outer_circle(coords, vertex_circles, radius):
    x, y = coords
    for circle in vertex_circles:
        x0, y0 = vertex_circles[circle]
        if (x - x0) ** 2 + (y - y0) ** 2 <= (2 * radius) ** 2:
            return circle
    return None


class DrawingTools:
    def __init__(self, selection_canvas, markup_canvas, interface_config):
        self.selection_canvas = selection_canvas
        self.markup_canvas = markup_canvas

        self.func_to_call = None
        self.finish_btn = None

        self.tag_num = 0
        self.created_object_specs = None
        self.unit_line_tag = None

        self.selection_top_x = 0
        self.selection_top_y = 0
        self.selection_bottom_x = 0
        self.selection_bottom_y = 0
        self.first_axle = (0, 0, 0, 0)
        self.first_axle_tag = None
        self.second_axle = (0, 0, 0, 0)
        self.second_axle_tag = None
        self.selection_fig_tag = None
        self.selection_fig_vertex_tag = None
        self.start_vertex = None
        self.custom_dots = []
        self.custom_lines_tags = []
        self.vertex_circles = {}
        self.edges_tag = None
        self.edges_tags = []
        self.bounding_status = False

        self.config = interface_config.config

    def draw_ellipse(self):
        self.unbind_canvas()
        self.selection_canvas.bind("<Button-1>",
                                   self.get_first_axle_start_pos)
        self.selection_canvas.bind("<ButtonRelease-1>",
                                   self.switch_to_second_axle)

    def switch_to_second_axle(self, event):
        self.first_axle = (self.selection_top_x, self.selection_top_y,
                           self.selection_bottom_x, self.selection_bottom_y)
        self.unbind_canvas(remove_axle=False)
        self.selection_canvas.bind("<Button-1>",
                                   self.get_second_axle_start_pos)
        self.selection_canvas.bind("<ButtonRelease-1>",
                                   self.create_ellipse)

    def get_first_axle_start_pos(self, event):
        fill = self.config["axle_color"]
        width = self.config["line_width"]
        self.selection_top_x, self.selection_top_y = event.x, event.y
        self.selection_fig_tag = self.get_id_tag()
        self.selection_canvas.create_line(
            self.selection_top_x,
            self.selection_top_y,
            self.selection_top_x,
            self.selection_top_y,
            tags=("draggable", self.selection_fig_tag),
            width=width, fill=fill, arrow="both")
        self.first_axle_tag = self.selection_fig_tag
        self.selection_canvas.bind("<B1-Motion>",
                                   self.update_first_axle_start_pos)

    def update_first_axle_start_pos(self, event):
        self.selection_bottom_x, self.selection_bottom_y = event.x, event.y
        self.selection_canvas.coords(self.selection_fig_tag,
                                     self.selection_top_x,
                                     self.selection_top_y,
                                     self.selection_bottom_x,
                                     self.selection_bottom_y)

    def get_second_axle_start_pos(self, event):
        dash = (self.config["dash"]["dash"], self.config["dash"]["space"])
        fill = self.config["axle_color"]
        width = self.config["line_width"]
        self.selection_top_x, self.selection_top_y = event.x, event.y
        self.selection_fig_tag = self.get_id_tag()
        self.selection_canvas.create_line(
            self.selection_top_x,
            self.selection_top_y,
            self.selection_top_x,
            self.selection_top_y,
            tags=("draggable", self.selection_fig_tag),
            width=width, fill=fill, arrow="both")
        self.second_axle_tag = self.selection_fig_tag
        self.selection_canvas.bind("<B1-Motion>",
                                   self.update_second_axle_start_pos)

    def update_second_axle_start_pos(self, event):
        self.selection_bottom_x, self.selection_bottom_y = event.x, event.y

        x1_1, y1_1, x1_2, y1_2 = self.first_axle
        v1 = (x1_2 - x1_1, y1_2 - y1_1)
        x_center = (x1_2 + x1_1) / 2
        y_center = (y1_2 + y1_1) / 2

        len = math.hypot(self.selection_top_x - self.selection_bottom_x,
                         self.selection_top_y - self.selection_bottom_y)
        koef = 1

        v2 = (0, len)
        if v1[0] == 0:
            v2 = (len, 0)
        if v1[1] == 0:
            v2 = (0, len)
        if v1[1] != 0 and v1[0] != 0:
            if -v1[0] / v1[1] != 0 and math.hypot(1, -v1[0] / v1[1]) != 0:
                koef = math.hypot(len) / math.hypot(1, -v1[0] / v1[1])
            v2 = (1 * koef, -v1[0] * koef / v1[1])

        self.selection_top_x = v2[0] / 2 + x_center
        self.selection_top_y = v2[1] / 2 + y_center
        self.selection_bottom_x = -v2[0] / 2 + x_center
        self.selection_bottom_y = -v2[1] / 2 + y_center

        self.selection_canvas.coords(self.selection_fig_tag,
                                     self.selection_top_x,
                                     self.selection_top_y,
                                     self.selection_bottom_x,
                                     self.selection_bottom_y)

    def create_ellipse(self, event):
        self.unbind_canvas()
        self.second_axle = (self.selection_top_x, self.selection_top_y,
                            self.selection_bottom_x, self.selection_bottom_y)

        x1_1, y1_1, x1_2, y1_2 = self.first_axle
        x2_1, y2_1, x2_2, y2_2 = self.second_axle

        if (x1_1, y1_1) > (x1_2, y1_2):
            x1_1, x1_2 = x1_2, x1_1
            y1_1, y1_2 = y1_2, y1_1

        v1 = (x1_2 - x1_1, y1_2 - y1_1)
        v2 = (x2_2 - x2_1, y2_2 - y2_1)

        x_center = (x1_2 + x1_1) / 2
        y_center = (y1_2 + y1_1) / 2
        v1_len = math.hypot(*v1)
        v2_len = math.hypot(*v2)

        angle_sin = v1[1] / v1_len
        angle_cos = v1[0] / v1_len

        a = v1_len / 2
        b = v2_len / 2

        points = [(x, math.sqrt(1 - x ** 2 / a ** 2) * b)
                  for x in range(-int(v1_len / 2), int(v1_len / 2), 5)]
        points += [(x, -math.sqrt(1 - x ** 2 / a ** 2) * b)
                   for x in range(int(v1_len / 2), -int(v1_len / 2), -5)]

        points = [(x * angle_cos - y * angle_sin + x_center,
                   x * angle_sin + y * angle_cos + y_center) for x, y in
                  points]

        dash = (self.config["dash"]["dash"], self.config["dash"]["space"])
        outline = self.config["oval_color"]
        width = self.config["line_width"]
        item = self.get_id_tag()
        self.selection_canvas.create_polygon(*points, dash=dash, width=width,
                                             fill='', tags=("draggable", item),
                                             outline=outline)
        self.markup_canvas.create_polygon(*points, dash=dash, width=width,
                                          fill='', tags=("draggable", item),
                                          outline=outline)

        x_a1, y_a1, x_a2, y_a2 = self.first_axle
        x_b1, y_b1, x_b2, y_b2 = self.second_axle
        self.created_object_specs = ("ellipse", item,
                                     math.hypot(x_a1 - x_a2, y_a1 - y_a2) / 2,
                                     math.hypot(x_b1 - x_b2, y_b1 - y_b2) / 2)

        self.selection_canvas.delete(self.first_axle_tag)
        self.selection_canvas.delete(self.second_axle_tag)
        self.first_axle_tag = None
        self.second_axle_tag = None

        self.func_to_call()

    def draw_circle(self):
        self.unbind_canvas()
        self.selection_canvas.bind("<Button-1>",
                                   self.get_circle_selection_start_pos)
        self.selection_canvas.bind("<ButtonRelease-1>",
                                   self.create_circle)

    def get_circle_selection_start_pos(self, event):
        self.selection_top_x, self.selection_top_y = event.x, event.y
        self.selection_bottom_x, self.selection_bottom_y = event.x, event.y
        dash = (self.config["dash"]["dash"], self.config["dash"]["space"])
        outline = self.config["circle_outline"]
        width = self.config["line_width"]

        self.selection_fig_tag = self.get_id_tag()
        self.selection_canvas.create_oval(
            self.selection_top_x,
            self.selection_top_y,
            self.selection_bottom_x,
            self.selection_bottom_y,
            dash=dash, fill='',
            tags=("draggable", self.selection_fig_tag),
            outline=outline, width=width)

        self.markup_canvas.create_oval(
            self.selection_top_x,
            self.selection_top_y,
            self.selection_bottom_x,
            self.selection_bottom_y,
            dash=dash, fill='',
            tags=("draggable", self.selection_fig_tag),
            outline=outline, width=width)
        self.selection_canvas.bind("<B1-Motion>",
                                   self.update_circle_selection_end_pos)

    def update_circle_selection_end_pos(self, event):
        self.selection_bottom_x, self.selection_bottom_y = event.x, event.y
        radius = math.hypot(self.selection_top_x - self.selection_bottom_x,
                            self.selection_top_y - self.selection_bottom_y)

        self.selection_canvas.coords(self.selection_fig_tag,
                                     self.selection_top_x + radius,
                                     self.selection_top_y + radius,
                                     self.selection_top_x - radius,
                                     self.selection_top_y - radius)
        self.markup_canvas.coords(
            self.selection_fig_tag,
            self.selection_top_x + radius,
            self.selection_top_y + radius,
            self.selection_top_x - radius,
            self.selection_top_y - radius)

    def create_circle(self, event):
        if (self.selection_top_x, self.selection_top_y) == (
                self.selection_bottom_x, self.selection_bottom_y):
            self.selection_top_x, self.selection_top_y = self.selection_bottom_x + 1, self.selection_bottom_y + 1

        radius = math.hypot(self.selection_top_x - self.selection_bottom_x,
                            self.selection_top_y - self.selection_bottom_y)
        self.created_object_specs = ("circle", self.selection_fig_tag, radius,
                                     self.selection_top_x,
                                     self.selection_top_y)
        self.func_to_call()

    def draw_polyhedron(self):
        self.unbind_canvas(False)
        self.custom_lines_tags.clear()
        self.selection_canvas.bind("<Button-1>",
                                   self.get_polyhedron_vertex)
        self.selection_canvas.bind("<B1-Motion>",
                                   self.draw_edge)
        self.selection_canvas.bind("<ButtonRelease-1>",
                                   self.add_edge)

    def get_polyhedron_vertex(self, event):
        x, y = event.x, event.y
        radius = self.config["vertex_circle_radius"]
        dash = (self.config["dash"]["dash"], self.config["dash"]["space"])
        width = self.config["line_width"]
        edge_fill = self.config["edge_color"]
        vertex_fill = self.config["vertex_fill"]
        item = outer_circle((x, y), self.vertex_circles, radius)
        if item is not None:
            x, y = self.vertex_circles[
                item]
        else:
            item = self.get_id_tag()
            self.selection_canvas.create_oval(
                x + radius,
                y + radius,
                x - radius,
                y - radius,
                outline=vertex_fill, tags=item,
                fill=vertex_fill, width=width)
            self.vertex_circles[item] = (x, y)

        self.selection_top_x, self.selection_top_y = x, y
        self.selection_bottom_x, self.selection_bottom_y = x, y

        self.selection_fig_vertex_tag = self.get_id_tag()
        self.selection_canvas.create_oval(
            x + radius, y + radius, x - radius, y - radius,
            outline=vertex_fill, fill=vertex_fill, width=width,
            tags=self.selection_fig_vertex_tag)
        self.start_vertex = item

        self.selection_fig_tag = self.get_id_tag()
        self.selection_canvas.create_line(
            x, y, x, y, dash=dash, width=width, fill=edge_fill,
            tags=("draggable", self.selection_fig_tag))
        self.markup_canvas.create_line(
            x, y, x, y, dash=dash, width=width, fill=edge_fill,
            tags=("draggable", self.selection_fig_tag))

    def draw_edge(self, event):
        x, y = event.x, event.y
        radius = self.config["vertex_circle_radius"]
        item = outer_circle((x, y), self.vertex_circles, radius)
        if item is not None:
            x, y = self.vertex_circles[item]

        self.selection_bottom_x, self.selection_bottom_y = x, y
        self.selection_canvas.coords(self.selection_fig_vertex_tag,
                                     x + radius,
                                     y + radius,
                                     x - radius,
                                     y - radius)
        self.selection_canvas.coords(self.selection_fig_tag,
                                     self.selection_top_x,
                                     self.selection_top_y, x, y)
        self.markup_canvas.coords(self.selection_fig_tag, self.selection_top_x,
                                  self.selection_top_y, x, y)

    def add_edge(self, event):
        x, y = self.selection_bottom_x, self.selection_bottom_y
        if (x, y) == self.vertex_circles[self.start_vertex]:
            self.selection_canvas.delete(self.selection_fig_tag)
            self.selection_canvas.delete(self.selection_fig_vertex_tag)
            self.start_vertex = None
            return

        if self.edges_tag is None:
            self.edges_tag = self.get_id_tag()
        item = self.selection_canvas.find_withtag(self.selection_fig_tag)[0]
        self.selection_canvas.itemconfig(item,
                                         tags=("draggable", self.edges_tag))
        item = self.markup_canvas.find_withtag(self.selection_fig_tag)[0]
        self.markup_canvas.itemconfig(item,
                                      tags=("draggable", self.edges_tag))

        self.vertex_circles[self.selection_fig_vertex_tag] = (x, y)

    def create_polyhedron(self):
        for circle in self.vertex_circles:
            self.selection_canvas.delete(circle)
        self.vertex_circles.clear()
        self.start_vertex = None
        self.selection_fig_vertex_tag = None

        if self.edges_tag is None:
            self.unbind_canvas()
            self.func_to_call()
            return

        options = ["Bound with circle", "Bound with ellipse"]
        bounding_figure = ask_bounding_figure(options).split(' ')[-1]
        if bounding_figure == "circle":
            self.bounding_status = True
            function = self.func_to_call

            def func():
                self.bound_with_circle(self.edges_tag, "polyhedron")
                self.edges_tag = None
                self.bounding_status = False
                function()
                return

            self.func_to_call = func
            self.draw_circle()
        elif bounding_figure == "ellipse":
            self.bounding_status = True
            function = self.func_to_call

            def func():
                self.bound_with_ellipse(self.edges_tag, "polyhedron")
                self.edges_tag = None
                self.bounding_status = False
                function()
                return

            self.func_to_call = func
            self.draw_ellipse()
        elif bounding_figure == "":
            self.selection_canvas.delete(self.edges_tag)
            self.markup_canvas.delete(self.edges_tag)
            self.edges_tag = None
            self.created_object_specs = None
            self.func_to_call()
            return

    def bound_with_circle(self, figure_tag, obj_type):
        self.bounding_status = False
        fig_type, circle_tag, radius, x, y = self.created_object_specs
        circle = self.selection_canvas.find_withtag(circle_tag)[0]
        self.selection_canvas.itemconfig(circle,
                                         tags=("draggable", figure_tag))
        circle = self.markup_canvas.find_withtag(circle_tag)[0]
        self.markup_canvas.itemconfig(circle,
                                      tags=("draggable", figure_tag))
        self.created_object_specs = (
            obj_type, figure_tag, fig_type, radius)

    def bound_with_ellipse(self, figure_tag, obj_type):
        self.bounding_status = False
        fig_type, ellipse_tag, radius_a, radius_b = self.created_object_specs
        ellipse = self.selection_canvas.find_withtag(ellipse_tag)[0]
        self.selection_canvas.itemconfig(ellipse,
                                         tags=("draggable", figure_tag))
        ellipse = self.markup_canvas.find_withtag(ellipse_tag)[0]
        self.markup_canvas.itemconfig(ellipse,
                                      tags=("draggable", self.edges_tag))
        self.created_object_specs = (
            obj_type, figure_tag, fig_type, radius_a, radius_b)

    def draw_custom_area(self):
        self.unbind_canvas()
        self.selection_canvas.bind("<Button-1>",
                                   self.get_custom_selection_start_pos)
        self.selection_canvas.bind("<ButtonRelease-1>",
                                   self.finish_custom_selection)

    def get_custom_selection_start_pos(self, event):
        self.selection_top_x, self.selection_top_y = event.x, event.y
        self.selection_canvas.bind("<B1-Motion>",
                                   self.update_custom_selection_end_pos)

    def update_custom_selection_end_pos(self, event):
        fill = self.config["custom_selection_outline"]
        width = self.config["line_width"]
        item = self.get_id_tag()
        self.selection_canvas.create_line(self.selection_top_x,
                                          self.selection_top_y,
                                          event.x, event.y,
                                          fill=fill,
                                          tags=("draggable", item),
                                          width=width)

        self.markup_canvas.create_line(
            self.selection_top_x,
            self.selection_top_y,
            event.x, event.y,
            fill=fill,
            tags=("draggable", item),
            width=width)

        self.custom_dots.append((self.selection_top_x, self.selection_top_y))
        self.custom_lines_tags.append(item)
        self.selection_top_x, self.selection_top_y = event.x, event.y

    def finish_custom_selection(self, event):
        self.unbind_canvas()
        for line in self.custom_lines_tags:
            self.selection_canvas.delete(line)
            self.markup_canvas.delete(line)

        coords = []

        for i in range(0, len(self.custom_dots), 5):
            coords.append(self.custom_dots[i])

        if len(coords) >= 3:
            dash = (self.config["dash"]["dash"], self.config["dash"]["space"])
            outline = self.config["custom_selection_outline"]
            width = self.config["line_width"]
            item = self.get_id_tag()
            self.selection_canvas.create_polygon(coords,
                                                 dash=dash, width=width,
                                                 fill='',
                                                 tags=("draggable", item),
                                                 outline=outline)
            self.markup_canvas.create_polygon(coords, dash=dash,
                                              width=width, fill='',
                                              tags=("draggable", item),
                                              outline=outline)

            options = ["Use area of hand-drawn figure", "Bound with circle",
                       "Bound with ellipse"]
            bounding_type = ask_bounding_figure(options)
            if bounding_type == "Use area of hand-drawn figure":
                area = shapely.geometry.Polygon(coords).area
                self.created_object_specs = ("amorphous", item, None, area)
                self.func_to_call()
            elif bounding_type == "Bound with circle":
                self.bounding_status = True
                function = self.func_to_call

                def func():
                    self.bound_with_circle(item, "amorphous")
                    self.edges_tag = None
                    self.bounding_status = False
                    function()
                    return

                self.func_to_call = func
                self.draw_circle()
                func()
            elif bounding_type == "Bound with ellipse":
                self.bounding_status = True
                function = self.func_to_call

                def func():
                    self.bound_with_ellipse(item, "amorphous")
                    self.bounding_status = False
                    function()
                    return

                self.func_to_call = func
                self.draw_ellipse()
        else:
            self.func_to_call()
        self.custom_dots.clear()
        self.custom_lines_tags.clear()

    def draw_unit_line(self):
        self.unbind_canvas()
        self.selection_canvas.bind("<Button-1>",
                                   self.get_unit_line_start_pos)

    def get_unit_line_start_pos(self, event):
        self.selection_top_x, self.selection_top_y = event.x, event.y
        self.selection_bottom_x, self.selection_bottom_y = event.x, event.y

        width = self.config["unit_line_width"]
        fill = self.config["unit_line_color"]

        self.selection_fig_tag = self.get_id_tag()
        self.selection_canvas.create_line(
            self.selection_top_x,
            self.selection_top_y,
            self.selection_bottom_x,
            self.selection_bottom_y,
            tags=("draggable", self.selection_fig_tag),
            width=width, fill=fill)

        self.markup_canvas.create_line(
            self.selection_top_x,
            self.selection_top_y,
            self.selection_bottom_x,
            self.selection_bottom_y,
            tags=("draggable", self.selection_fig_tag),
            width=width, fill=fill)

        self.unit_line_tag = self.selection_fig_tag

        self.selection_canvas.bind("<B1-Motion>",
                                   self.update_unit_line_end_pos)

        self.selection_canvas.bind("<B1-ButtonRelease>",
                                   lambda event: self.func_to_call(math.hypot(
                                       self.selection_top_x - self.selection_bottom_x,
                                       self.selection_top_y - self.selection_bottom_y)))

    def update_unit_line_end_pos(self, event):
        self.selection_bottom_x, self.selection_bottom_y = event.x, event.y

        self.selection_canvas.coords(self.selection_fig_tag,
                                     self.selection_top_x,
                                     self.selection_top_y,
                                     self.selection_bottom_x,
                                     self.selection_bottom_y)

        self.markup_canvas.coords(self.selection_fig_tag,
                                  self.selection_top_x,
                                  self.selection_top_y,
                                  self.selection_bottom_x,
                                  self.selection_bottom_y)

    def get_id_tag(self):
        res = "tag" + str(self.tag_num)
        self.tag_num += 1
        return res

    def unbind_canvas(self, remove_btn=True, remove_axle=True):
        if self.selection_canvas is None:
            return
        self.selection_canvas.unbind("<ButtonPress-1>")
        self.selection_canvas.tag_unbind("draggable", "<ButtonPress-1>")
        self.selection_canvas.tag_unbind("draggable", "<Button1-Motion>")
        self.selection_canvas.unbind("<Button-1>")
        self.selection_canvas.unbind("<B1-Motion>")
        self.selection_canvas.unbind("<Button1-Motion>")
        self.selection_canvas.unbind("<B1-ButtonRelease>")
        self.selection_canvas.unbind("<ButtonRelease-1>")

        if self.finish_btn is not None and remove_btn and not self.bounding_status:
            self.finish_btn.destroy()
            for circle in self.vertex_circles:
                self.selection_canvas.delete(circle)
            self.vertex_circles.clear()

            if self.edges_tag is not None:
                self.selection_canvas.delete(self.edges_tag)
                self.markup_canvas.delete(self.edges_tag)
                self.edges_tag = None

            if self.selection_fig_vertex_tag is not None:
                self.selection_canvas.delete(self.selection_fig_vertex_tag)
                self.selection_fig_vertex_tag = None

            if self.start_vertex is not None:
                self.selection_canvas.delete(self.start_vertex)
                self.start_vertex = None

        if not self.bounding_status:
            self.edges_tag = None

        if remove_axle and self.first_axle_tag is not None:
            self.selection_canvas.delete(self.first_axle_tag)
            self.first_axle_tag = None
