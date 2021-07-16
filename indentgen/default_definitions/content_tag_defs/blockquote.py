from . content_tag_set import content_tag_set
from dentmark.default_definitions import BlockQuote, Paragraph

@content_tag_set.register(replace=True)
class IndentgenContentBlockQuote(BlockQuote):

    def before_render(self):
        # promote orphaned text nodes to 'p'
        for i,child in enumerate(self.children):
            if not child.is_element:
                promoted_elem = child.promote(Paragraph)
                self.children[i] = promoted_elem

