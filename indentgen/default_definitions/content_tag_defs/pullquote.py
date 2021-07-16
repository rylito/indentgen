from dentmark import TagDef, Optional
from . content_tag_set import content_tag_set

@content_tag_set.register()
class IndentgenContentPullQuote(TagDef):
    tag_name = 'pq'
    add_to_collector = True

    min_num_text_nodes = 1
    max_num_text_nodes = None

    parents = [Optional('root.p')]

    def render_secondary(self):
        pass

    def render_secondary(self):
        content = self.content

        if content:
            # make sure first letter is capitalized, so that we can pull fragments of sentences as pullquotes
            content = content[0].upper() + content[1:]

        return f'<div class="pullquote"><span class="openquote"></span><span class="quotecontent">{content}</span></div>'


