from dentmark.defs_manager import DefSet
from dentmark import TagDef

class TaxonomyDefSet(DefSet):
    #def __init__(self, tag_set_name, taxonomy_map):
        #super().__init__(tag_set_name)
        #self.taxonomy_map = taxonomy_map

    @classmethod
    def copy_from_def_set(cls, other_def_set):
        new_obj = cls(other_def_set.tag_set_name)

        new_obj.pre_tag_names = other_def_set.pre_tag_names
        new_obj.root_def = other_def_set.root_def
        new_obj.tag_dict = other_def_set.tag_dict
        new_obj._is_checked = other_def_set._is_checked

        return new_obj

    def get_def(self, tag_name, parent_node):
        if parent_node.tag_name == 'taxonomy':
            return TaxonomyItemTagDef
        else:
            return self.tag_dict.get(tag_name)



class TaxonomyItemTagDef(TagDef):
    is_context = True
    allow_children = []

    min_num_children = 0 #TODO make this optional for the Part / order #
    max_num_children = 1

    def __init__(self, tag_name, line_no, indent_level, parent, order, nth_of_type, trim_left, trim_right):
        self.tag_name = tag_name
        super().__init__(tag_name, line_no, indent_level, parent, order, nth_of_type, trim_left, trim_right)

    def process_data(self, data):
        if not data:
            return None
        per_page = int(data[0])
        if per_page < 1:
            raise ValueError
        return per_page


    def validate(self):
        #val = self.get_data()
        #if not val.isdigit():
            #return f"Tag '{self.tag_name}' expects a positive integer"
        try:
            self.get_data()
        except ValueError:
            return f"Tag '{self.tag_name}' expects a positive integer >= 1"

