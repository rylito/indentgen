from dentmark import TagDef, Optional, RequiredUnique
from . content_tag_set import content_tag_set
from dentmark.default_definitions.anchor import URLContext

@content_tag_set.register()
class IndentgenContentMessageArchiveLink(TagDef):
    tag_name = 'ma'

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [Optional('root')]

    def render_main(self):
        url = self.context.get('url')

        if url:
            return f'<a href="{url}" class="message-archive-link">{self.content}</a>'

        return ''


@content_tag_set.register()
class IndentgenContentMessageExtract(TagDef):
    tag_name = 'extract'

    parents = [Optional('root')]

    def render_main(self):
        link = self.context.get('link')
        return f'<blockquote>{self.content}<sup><a href="{link}" class="extract-ref">↩︎</a></sup></blockquote>'


@content_tag_set.register()
class IndentgenContentMessageExtractLink(URLContext):
    tag_name = 'link'

    parents = [RequiredUnique('root.extract')]
