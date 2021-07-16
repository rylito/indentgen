from dentmark import Optional
from . content_tag_set import content_tag_set
from dentmark.default_definitions.emphasis import Italic

@content_tag_set.register()
class IndentgenContentSumItalic(Italic):
    parents = [
        Optional('root.p.sum'),
        Optional('root.bq.p'),
        Optional('root.p.a8n.fn'),
        Optional('root.p.a'),
        Optional('root.p.a8n.fn.a'),
        Optional('root.bq.p.a8n.fn'),
        Optional('root.p.pq'),
        Optional('root.p.a8n'),
        Optional('root.img.caption'),
        Optional('root.meta.img.caption'),
        Optional('root.ul.li.a8n.fn')
    ]


