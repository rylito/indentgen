import re
from dentmark.defs_manager import DefSet
from dentmark import TagDef, OptionalUnique

class TaxonomyDefSetContent(DefSet):
    #def __init__(self, tag_set_name, taxonomy_map):
        #super().__init__(tag_set_name)
        #self.taxonomy_map = taxonomy_map

    PATTERN = re.compile(r'^root\.meta\.taxonomy\.[^\.]+?(?P<parent>\.parent)?$')

    @classmethod
    def copy_from_def_set(cls, other_def_set):
        new_obj = cls(other_def_set.tag_set_name)

        new_obj.pre_tag_addresses = other_def_set.pre_tag_addresses
        new_obj.root_def = other_def_set.root_def
        new_obj.tag_dict = other_def_set.tag_dict
        new_obj._is_checked = other_def_set._is_checked
        new_obj.children_relation_dict = other_def_set.children_relation_dict

        return new_obj

    #def get_def(self, tag_address):
        #if tag_address.startswith('root.meta.taxonomy.'): #trailing '.' is significant, 'root.meta.taxonomy' needs to be looked up as usual
            #return TaxonomyItemTagDef
        #else:
            #return self.tag_dict.get(tag_address)

    def get_def(self, tag_address):
        m = self.PATTERN.match(tag_address)
        if m and not m.group('parent'):
            return TaxonomyItemTagDef
        else:
            return self.tag_dict.get(tag_address)


    def get_children_relations(self, tag_address):
        if tag_address == 'root.meta.taxonomy':
            #tag_name = tag_address.split('.')[-1]
            return TaxonomyChildrenRelations()
        else:
            return self.children_relation_dict.get(tag_address, {})


class TaxonomyDefSetTaxonomy(TaxonomyDefSetContent):

    def get_def(self, tag_address):
        m = self.PATTERN.match(tag_address)
        if m:
            if m.group('parent'):
                return TaxonomyItemParentTagDef
            else:
                return TaxonomyItemTagDef
        else:
            return self.tag_dict.get(tag_address)


    def get_children_relations(self, tag_address):
        if tag_address == 'root.meta.taxonomy':
            #tag_name = tag_address.split('.')[-1]
            return TaxonomyChildrenRelations()

        m = self.PATTERN.match(tag_address)
        if m and not m.group('parent'):
            #return TaxonomyChildrenParentRelation()
            return TaxonomyChildrenRelations()
        else:
            return self.children_relation_dict.get(tag_address, {})




class TaxonomyChildrenRelations:
    # A 'dummy' dictionary that always returns the same thing no matter what the key
    def __getitem__(self, item):
        return OptionalUnique(item) # arg doesn't really matter, just use item I guess in case I need to debug off it. Could be None or '' too

    def items(self):
        return [] # causes .items() to do nothing. None of the taxonomy names are required, so don't need to check for missing names


#class TaxonomyChildrenParentRelation
    #def __getitem__(self, item):
        #return OptionalUnique(item) # arg doesn't really matter, just use item I guess in case I need to debug off it. Could be None or '' too

    #def items(self):
        #return [] # causes .items() to do nothing. None of the taxonomy names are required, so don't need to check for missing names




class TaxonomyItemTagDef(TagDef):
    is_context = True
    #allow_children = []

    min_num_text_nodes = 0
    max_num_text_nodes = 1

    parents = [OptionalUnique('root.meta.taxonomy')]

    def __init__(self, tag_name, address, line_no, indent_level, parent, root, order, nth_of_type, trim_left, trim_right):
        self.tag_name = tag_name
        super().__init__(tag_name, address, line_no, indent_level, parent, root, order, nth_of_type, trim_left, trim_right)


    def process_data(self, data):
        order = None
        for child in self.children:
            if not child.is_element:
                order = int(child.text)
                if order < 1:
                    raise ValueError
        return (order, self.context.get('parent', False))


    def validate(self):
        try:
            self.get_data()
        except ValueError:
            return f"Tag '{self.tag_name}' expects a positive integer >= 1"


class TaxonomyItemParentTagDef(TagDef):
    tag_name = 'parent'
    is_context = True

    min_num_text_nodes = 0
    max_num_text_nodes = 1

    #parents = [OptionalUnique('root.meta')]

    def process_data(self, data):
        if data:
            return data[0].lower() == 'true'
        return True

    def validate(self):
        if self.children:
            if self.children[0].get_data().lower() not in ('true', 'false'):
                return f"'parent' tag value must be either 'true', 'false', or [empty]. Defaults to 'true' if [empty]"



#@taxonomy_tag_set.register()
#class TaxonomyParentContext(TagDef):
    #tag_name = 'parent'
    #is_context = True
    #allow_children = []

    #min_num_text_nodes = 1
    #max_num_text_nodes = 1

    #parents = [OptionalUnique('root.meta')]

