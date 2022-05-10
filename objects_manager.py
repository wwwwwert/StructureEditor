import math


class ObjectsManager():
    def __init__(self):
        self.created_items = {}
        self.lines = list()

    def add_circle(self, specs):
        fig_type, id_tag, radius, x, y = specs
        self.created_items[id_tag] = (fig_type, x, y, radius)

    def add_ellipse(self, specs):
        fig_type, id_tag, radius_a, radius_b = specs
        self.created_items[id_tag] = (fig_type, radius_a, radius_b)

    def add_polyhedron(self, specs):
        if specs[2] == "circle":
            fig_type, id_tag, bound_fig_type, radius = specs
            self.created_items[id_tag] = (fig_type, bound_fig_type, radius)
        elif specs[2] == "ellipse":
            fig_type, id_tag, bound_fig_type, radius_a, radius_b = specs
            self.created_items[id_tag] = (
                fig_type, bound_fig_type, radius_a, radius_b)

    def add_amorphous(self, specs):
        if specs[2] == "circle":
            fig_type, id_tag, bound_fig_type, radius = specs
            self.created_items[id_tag] = (fig_type, bound_fig_type, radius)
        elif specs[2] == "ellipse":
            fig_type, id_tag, bound_fig_type, radius_a, radius_b = specs
            self.created_items[id_tag] = (
                fig_type, bound_fig_type, radius_a, radius_b)
        else:
            fig_type, id_tag, _, area = specs
            self.created_items[id_tag] = (fig_type, id_tag, area)

    def create_lines(self, pixel_proportion):
        self.lines.clear()
        for specs in self.created_items.values():
            self.lines.append(
                self.create_line_from_specs(specs, pixel_proportion))
        self.lines.sort(key=lambda x: x[-1])

    def create_line_from_specs(self, specs, pixel_proportion):
        fig_type = specs[0]
        if fig_type == "circle":
            x, y, radius = specs[1], specs[2], specs[3]
            radius *= pixel_proportion
            return (fig_type, None, str(round(radius, 3)),
                    round(math.pi * radius ** 2, 3))
        elif fig_type == "ellipse":
            radius_a, radius_b = specs[1], specs[2]
            radius_a *= pixel_proportion
            radius_b *= pixel_proportion
            return (fig_type, None,
                    str(round(radius_a, 3)) + '\t' + str(
                        round(radius_b, 3)),
                    round(math.pi * radius_a * radius_b, 3))
        elif fig_type == "polyhedron":
            bound_fig_type = specs[1]
            if bound_fig_type == "circle":
                radius = specs[2]
                radius *= pixel_proportion
                return (fig_type, bound_fig_type,
                        str(round(radius, 3)),
                        round(math.pi * radius ** 2, 3))
            elif bound_fig_type == "ellipse":
                radius_a, radius_b = specs[2], specs[3]
                radius_a *= pixel_proportion
                radius_b *= pixel_proportion
                return (fig_type, bound_fig_type,
                        str(round(radius_a, 3)) + '\t' + str(
                            round(radius_b, 3)),
                        round(math.pi * radius_a * radius_b, 3))
        elif fig_type == "amorphous":
            bound_fig_type = specs[1]
            if bound_fig_type == "circle":
                radius = specs[2]
                radius *= pixel_proportion
                return (fig_type, bound_fig_type,
                        str(round(radius, 3)),
                        round(math.pi * radius ** 2, 3))
            elif bound_fig_type == "ellipse":
                radius_a, radius_b = specs[2], specs[3]
                radius_a *= pixel_proportion
                radius_b *= pixel_proportion
                return (fig_type, bound_fig_type,
                        str(round(radius_a, 3)) + '\t' + str(
                            round(radius_b, 3)),
                        round(math.pi * radius_a * radius_b, 3))
            else:
                area = specs[2] * pixel_proportion ** 2
                return fig_type, None, None, round(area, 3)
