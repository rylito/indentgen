from dentmark import Optional
from . content_tag_set import content_tag_set
from dentmark.default_definitions import Paragraph

@content_tag_set.register(replace = True)
class IndentgenContentParagraph(Paragraph):

    parents = [Optional('root'), Optional('root.sum'), Optional('root.meta.summary'), Optional('root.bq'), Optional('root.conv.msg'), Optional('root.p.a8n.fn.bq')]

    def render_main(self):
        classes = ''
        if self.classes:
            class_str = ' '.join(self.classes)
            classes = f' class="{class_str}"'

        dropcap = ''
        first_letter = self.context.get('use_dropcap')

        if first_letter:
            dropcap = f'<span class="dropcap">{first_letter}</span>'

        leadin = ''
        leadin_txt = self.context.get('use_leadin')

        if leadin_txt:
            commaspace = '' if self.content[0] == ',' else ' '
            leadin = f'<span class="leadin">{leadin_txt}</span>{commaspace}'

        return f'<p{classes}>{dropcap}{leadin}{self.content}</p>'


    def before_render(self):
        # This has to be done here prior to render, so it take effect

        text_nodes = self.strip_tags()

        if 'use_dropcap' in self.context:
            first_letter = None
            if text_nodes:
                first_letter = text_nodes[0].text[0] if text_nodes[0].text else None
                if first_letter:
                    text_nodes[0].text = text_nodes[0].text[1:] # strip first letter
                    self.context['use_dropcap'] = first_letter

        if 'use_leadin' in self.context:
            if text_nodes:
                first_part = text_nodes[0].text if text_nodes[0].text else None
                if first_part:
                    # only go up to comma if it is present
                    before_comma = first_part.split(',')[0]
                    words = before_comma.split(' ')[:5] # max number of words for lead-in
                    rejoin = ' '.join(words)
                    # trim the leadin text off the text node
                    text_nodes[0].text = first_part[len(rejoin):]
                    self.context['use_leadin'] = rejoin


