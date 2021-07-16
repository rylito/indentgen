from dentmark import TagDef, Optional
from . content_tag_set import content_tag_set

@content_tag_set.register()
class IndentgenContentAside(TagDef):
    tag_name = 'aside'

    parents = [Optional('root')]

    def render_main(self):
        return f'<div class="aside">{self.content}</div>'
