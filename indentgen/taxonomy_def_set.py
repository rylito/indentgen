import re
from dentmark.defs_manager import DefSet
from dentmark import TagDef, OptionalUnique

class TaxonomyDefSet(DefSet):

    PATTERN = re.compile(r'^root\.meta\.taxonomy\..*[^\.]+$')

    @classmethod
    def copy_from_def_set(cls, other_def_set):
        new_obj = cls(other_def_set.tag_set_name)

        new_obj.pre_tag_addresses = other_def_set.pre_tag_addresses
        new_obj.root_def = other_def_set.root_def
        new_obj.tag_dict = other_def_set.tag_dict
        new_obj._is_checked = other_def_set._is_checked
        new_obj.children_relation_dict = other_def_set.children_relation_dict

        return new_obj


    def get_def(self, tag_address):
        m = self.PATTERN.match(tag_address)
        if m:
            return TaxonomyItemTagDef
        else:
            return self.tag_dict.get(tag_address)


    def get_children_relations(self, tag_address):
        if tag_address.startswith('root.meta.taxonomy'):
            return TaxonomyChildrenRelations()
        else:
            return self.children_relation_dict.get(tag_address, {})


class TaxonomyChildrenRelations:
    # A 'dummy' dictionary that always returns the same thing no matter what the key
    def __getitem__(self, item):
        return OptionalUnique(item) # arg doesn't really matter, just use item I guess in case I need to debug off it. Could be None or '' too

    def items(self):
        return [] # causes .items() to do nothing. None of the taxonomy names are required, so don't need to check for missing names


class TaxonomyItemTagDef(TagDef):
    is_context = True

    min_num_text_nodes = 0
    max_num_text_nodes = 1

    parents = [OptionalUnique('root.meta.taxonomy')]

    def __init__(self, tag_name, address, line_no, indent_level, parent, root, order, nth_of_type, trim_left, trim_right, extra_context):
        self.tag_name = tag_name
        super().__init__(tag_name, address, line_no, indent_level, parent, root, order, nth_of_type, trim_left, trim_right, extra_context)


    def process_data(self, data):
        order = None

        has_order_element = False
        has_child_elements = False

        for child in self.children:
            if not child.is_element:
                has_order_element = True
                order = int(child.text)
                if order < 1:
                    raise ValueError
            else:
                has_child_elements = True

        if has_order_element and has_child_elements:
            raise Exception("Cannot have both an order number set AND child taxonomies listed")

        if has_child_elements:
            return self.context
        else:
            return order


    def validate(self):
        try:
            self.get_data()
        except ValueError:
            return f"Tag '{self.tag_name}' expects a positive integer >= 1"
        except Exception as e:
            return f"Tag '{self.tag_name}' {e}"


class MetaTaxonomyContext(TagDef):
    tag_name = 'taxonomy'
    is_context = True

    parents = [OptionalUnique('root.meta')]

    min_num_text_nodes = 0 # don't allow text nodes
    max_num_text_nodes = 0

    def process_data(self, data):

        taxonomies_dict = {}

        def walk_dict(d, slug_path = ''):
            for k,v in d.items():
                new_slug_path = slug_path
                if new_slug_path:
                    new_slug_path += '/'
                new_slug_path += k

                if type(v) is dict:
                    walk_dict(v, new_slug_path)
                else:
                    taxonomies_dict[new_slug_path] = v

        walk_dict(self.context)

        return taxonomies_dict

