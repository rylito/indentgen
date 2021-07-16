from dentmark import TagDef, Optional, OptionalUnique
from . content_tag_set import content_tag_set
from dentmark.default_definitions import Paragraph, Break

@content_tag_set.register()
class IndentgenContentConversation(TagDef):
    tag_name = 'conv'

    parents = [Optional('root')]


@content_tag_set.register()
class IndentgenContentConversationDefault(TagDef):
    tag_name = 'default_from'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [OptionalUnique('root.conv')]


@content_tag_set.register()
class IndentgenContentMsg(TagDef):
    tag_name = 'msg'

    parents = [Optional('root.conv')]

    def before_render(self):
        # promote orphaned text nodes to 'p'
        for i,child in enumerate(self.children):
            if not child.is_element:
                promoted_elem = child.promote(Paragraph)
                self.children[i] = promoted_elem


    def render_main(self):
        msg_str = ''

        actor_id_map = self.parent.context.setdefault('msg_actors', {})

        prev_actor_id = self.parent.context.get('prev_actor_id')

        default_actor_name = self.parent.context.get('default_from') or 'Me' # default name for messages I sent (ones without a 'from' context)

        #for msg in msgs:
        frm = self.context.get('from')
        content = self.content

        side = 'left' if frm else 'right'
        cls_color = ''

        put_name = ''

        actor_id = -1 # denotes 'Me'

        if frm:
            actor_id = actor_id_map.setdefault(frm, len(actor_id_map))
            cls_color = f' msg__color__{actor_id}'

        if actor_id != prev_actor_id:
            use_name = frm or default_actor_name
            put_name = f'<span>{use_name}</span>'
            self.parent.context['prev_actor_id'] = actor_id

        return f'<div class="conversation__msg msg__{side}{cls_color}">{put_name}{content}</div>'


@content_tag_set.register()
class IndentgenContentMsgFrom(TagDef):
    tag_name = 'from'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [OptionalUnique('root.conv.msg')]


@content_tag_set.register()
class IndentgenContentBr(Break):
    parents = [Optional('root.conv.msg.p')]

