from .dynamic_structure import StructureSelector
from .base_types import RAW

class Array(StructureSelector):

    def __init__(self, length_path, type):
        self.length_path = length_path
        self.type = type

    def structure(self):
        length = self.get_variable(self.length_path)
        return self.type() * length

class DynamicRaw(StructureSelector):

    def __init__(self, length_path):
        self.length_path = length_path

    def structure(self):
        length = self.get_variable(self.length_path)
        return RAW(length=length)