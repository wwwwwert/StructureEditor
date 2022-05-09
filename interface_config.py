import json
from math import sqrt

class InterfaceConfig:
    def __init__(self, dpi, width, height):
        print(dpi, width, height)
        self.proportion = sqrt((width * height) / (1280 * 800))

        with open('config.json', 'r') as f:
            self.config = json.load(f)

        sizes = self.config.pop("sizes")
        for spec in sizes.items():
            spec_name, spec_value = self.adjust_spec(spec)
            self.config[spec_name] = spec_value

    def adjust_spec(self, spec):
        # print(spec)
        spec_name, spec_value = spec
        if type(spec_value) == int or type(spec_value) == float:
            res_value = int(spec_value * self.proportion)
            if res_value == 0:
                res_value += 1
            return spec_name, res_value

        for new_spec_name, new_spec_value in spec_value.items():
            spec_value[new_spec_name] = \
                self.adjust_spec((new_spec_name, new_spec_value))[1]
        return spec_name, spec_value
