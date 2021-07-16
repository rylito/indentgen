from dentmark import Optional, OptionalUnique
from . content_tag_set import content_tag_set
from dentmark.default_definitions.anchor import Anchor, URLContext, AnchorTitleContext


@content_tag_set.register(replace=True)
class IndentgenContentImageAnchor(Anchor):
    parents = [
        Optional('root'),
        Optional('root.p'),
        Optional('root.p.a8n.fn'),
        Optional('root.bq.a8n.fn'),
        Optional('root.img.attr'),
        Optional('root.meta.img.attr'),
        Optional('root.meta.gallery.img.caption'),
        Optional('root.meta.gallery.img.attr'),
        Optional('root.p.sum'),
        Optional('root.p.sum.i'),
        Optional('root.sum.p'),
        Optional('root.ul.li'),
        Optional('root.p.a8n.fn.i'),
        Optional('root.p.i'),
        Optional('root.img.caption'),
        Optional('root.conv.msg.p'),
        Optional('root.bq.p.a8n.fn'),
        Optional('root.ul.li.a8n.fn.i'),
        Optional('root.aside'),
        Optional('root.extract'),
        Optional('root.p.hl')
    ]


    def render_main(self):
        url = self.context.get('url')
        if url is None:
            if self.content.startswith('http'):
                url = self.content
            else:
                content_split = self.content.split('@')
                if len(content_split) == 2 and '.' in content_split[1]:
                    url = f'mailto:{self.content}'
                else:
                    # don't add the tag. This supports the #TODO or 'deferred' links
                    return self.content

        href = f' href="{url}"' if url else ''

        title = self.context.get('title')
        title_str = f' title="{title}"' if title else ''

        return f'<a{href}{title_str}>{self.content}</a>'


@content_tag_set.register(replace=True)
class IndentgenContentImageAnchorURL(URLContext):
    parents = [
        OptionalUnique('root.a'),
        OptionalUnique('root.p.a'),
        OptionalUnique('root.p.a8n.fn.a'),
        OptionalUnique('root.bq.a8n.fn.a'),
        OptionalUnique('root.img.attr.a'),
        OptionalUnique('root.meta.img.attr.a'),
        OptionalUnique('root.meta.gallery.img.caption.a'),
        OptionalUnique('root.meta.gallery.img.attr.a'),
        OptionalUnique('root.p.sum.i.a'),
        OptionalUnique('root.p.a8n.fn.i.a'),
        OptionalUnique('root.p.i.a'),
        OptionalUnique('root.p.sum.a'),
        OptionalUnique('root.conv.msg.p.a'),
        OptionalUnique('root.bq.p.a8n.fn.a'),
        OptionalUnique('root.ul.li.a8n.fn.i.a'),
        OptionalUnique('root.aside.a'),
        OptionalUnique('root.ma'),
        OptionalUnique('root.extract.a'),
        OptionalUnique('root.p.hl.a'),
        OptionalUnique('root.sum.p.a'),
        OptionalUnique('root.ul.li.a')
    ]


    def process_data(self, data):
        if data[0].isdigit():
            indentgen = self.extra_context['indentgen']
            return indentgen.get_url_for_pk(data[0])
        return data[0]

    def validate(self):
        raw_val = self.children[0].text
        try:
            self.get_data()
        except KeyError as e:
            return f'Page with PK of {raw_val} does not exist'


@content_tag_set.register()
class IndentgenContentImageAnchorTitle(AnchorTitleContext):
    parents = [OptionalUnique('root.img.attr.a'), OptionalUnique('root.meta.img.attr.a')]

