import math


class ObjectsGroup:
    def __init__(self, id, main_size):
        self.id = id
        self.main_size = main_size
        self.main_col = list()
        self.left_col = list()
        self.right_col = list()

        self.main_id = 1
        self.left_id = 1
        self.right_id = 1

        self.total_size = 0

    def check_if_attachable(self, size):
        return 0.64 * self.main_size <= size <= 1.36 * self.main_size

    def add_line(self, elem, size, pixel_proportion):
        if 0.64 * self.main_size <= size < 0.88 * self.main_size:
            line = self.create_line_from_specs(elem, self.left_id,
                                               pixel_proportion)
            self.left_id += 1
            self.total_size += float(line[(-1)])
            self.left_col.append(line)
        elif 0.88 * self.main_size <= size <= 1.12 * self.main_size:
            line = self.create_line_from_specs(elem, self.main_id,
                                               pixel_proportion)
            self.main_id += 1
            self.total_size += float(line[(-1)])
            self.main_col.append(line)
        else:
            line = self.create_line_from_specs(elem, self.right_id,
                                               pixel_proportion)
            self.right_id += 1
            self.total_size += float(line[(-1)])
            self.right_col.append(line)

    def create_line_from_specs(self, specs, id, pixel_proportion):
        fig_type = specs[0]
        if fig_type == "circle":
            x, y, radius = specs[1], specs[2], specs[3]
            radius *= pixel_proportion
            return ('S' + str(id), fig_type, None, str(round(radius, 3)),
                    str(round(math.pi * radius ** 2, 3)))
        elif fig_type == "ellipse":
            radius_a, radius_b = specs[1], specs[2]
            radius_a *= pixel_proportion
            radius_b *= pixel_proportion
            return ('S' + str(id), fig_type, None,
                    str(round(radius_a, 3)) + '\t' + str(
                        round(radius_b, 3)),
                    str(round(math.pi * radius_a * radius_b, 3)))
        elif fig_type == "polyhedron":
            bound_fig_type = specs[1]
            if bound_fig_type == "circle":
                radius = specs[2]
                radius *= pixel_proportion
                return ('S' + str(id), fig_type, bound_fig_type,
                        str(round(radius, 3)),
                        str(round(math.pi * radius ** 2, 3)))
            elif bound_fig_type == "ellipse":
                radius_a, radius_b = specs[2], specs[3]
                radius_a *= pixel_proportion
                radius_b *= pixel_proportion
                return ('S' + str(id), fig_type, bound_fig_type,
                        str(round(radius_a, 3)) + '\t' + str(
                            round(radius_b, 3)),
                        str(round(math.pi * radius_a * radius_b, 3)))
        elif fig_type == "amorphous":
            bound_fig_type = specs[1]
            if bound_fig_type == "circle":
                radius = specs[2]
                radius *= pixel_proportion
                return ('S' + str(id), fig_type, bound_fig_type,
                        str(round(radius, 3)),
                        str(round(math.pi * radius ** 2, 3)))
            elif bound_fig_type == "ellipse":
                radius_a, radius_b = specs[2], specs[3]
                radius_a *= pixel_proportion
                radius_b *= pixel_proportion
                return ('S' + str(id), fig_type, bound_fig_type,
                        str(round(radius_a, 3)) + '\t' + str(
                            round(radius_b, 3)),
                        str(round(math.pi * radius_a * radius_b, 3)))
            else:
                area = specs[2] * pixel_proportion ** 2
                return 'S' + str(id), fig_type, None, None, str(round(area, 3))


class ObjectsManager():
    def __init__(self):
        self.created_items = {}
        self.groups = list()

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

    def group_objects(self, pixel_proportion):
        for elem in self.created_items.values():
            size = self.get_object_size(elem, pixel_proportion)
            for group in self.groups:
                if group.check_if_attachable(size):
                    group.add_line(elem, size, pixel_proportion)
                    break
            else:
                group = ObjectsGroup(len(self.groups) + 1, size)
                group.add_line(elem, size, pixel_proportion)
                self.groups.append(group)

    def get_object_size(self, specs, pixel_proportion):
        fig_type = specs[0]
        if fig_type == "circle":
            x, y, radius = specs[1], specs[2], specs[3]
            radius *= pixel_proportion
            return round(math.pi * radius ** 2, 3)
        elif fig_type == "ellipse":
            radius_a, radius_b = specs[1], specs[2]
            radius_a *= pixel_proportion
            radius_b *= pixel_proportion
            return round(math.pi * radius_a * radius_b, 3)
        elif fig_type == "polyhedron":
            bound_fig_type = specs[1]
            if bound_fig_type == "circle":
                radius = specs[2]
                radius *= pixel_proportion
                return round(math.pi * radius ** 2, 3)
            elif bound_fig_type == "ellipse":
                radius_a, radius_b = specs[2], specs[3]
                radius_a *= pixel_proportion
                radius_b *= pixel_proportion
                return round(math.pi * radius_a * radius_b, 3)
        elif fig_type == "amorphous":
            bound_fig_type = specs[1]
            if bound_fig_type == "circle":
                radius = specs[2]
                radius *= pixel_proportion
                return round(math.pi * radius ** 2, 3)
            elif bound_fig_type == "ellipse":
                radius_a, radius_b = specs[2], specs[3]
                radius_a *= pixel_proportion
                radius_b *= pixel_proportion
                return round(math.pi * radius_a * radius_b, 3)
            else:
                area = specs[2] * pixel_proportion ** 2
                return round(area, 3)
