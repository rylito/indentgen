from . content_tag_set import content_tag_set
from dentmark.default_definitions.lists import UnorderedList, ListItem


@content_tag_set.register(replace=True)
class IndentgenContentUnorderedList(UnorderedList):

    # the default dentmark definitions don't allow text-only nodes,
    # but since we're promoting them in indentgen, re-set these
    # defaults.
    min_num_text_nodes = 0
    max_num_text_nodes = None

    def before_render(self):
        # promote orphaned text nodes to 'li'
        for i,child in enumerate(self.children):
            if not child.is_element:
                promoted_elem = child.promote(ListItem)
                self.children[i] = promoted_elem


