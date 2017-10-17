from .dynamic_structure import StructureSelector
from .base_types import RAW

class Array(StructureSelector):

    def structure(self, length_path, data_type):
        length = self.get_variable(length_path)
        return data_type() * length

class DynamicRaw(StructureSelector):

    def structure(self, length_path):
        length = self.get_variable(length_path)
        return RAW(length=length)