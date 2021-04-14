import datetime

from dentmark import defs_manager, TagDef, Optional, OptionalUnique, RequiredUnique

from dentmark.default_definitions.anchor import Anchor, URLContext, AnchorTitleContext
from dentmark.default_definitions.images import ImgAltContext, ImgTitleContext
from dentmark.default_definitions import Paragraph, Root, BlockQuote, Break
from dentmark.default_definitions.emphasis import Italic
from dentmark.default_definitions.annotation import Annotation, FootNote
from dentmark.default_definitions.lists import UnorderedList, ListItem
from indentgen.default_definitions.config_tag_defs import ConfigURLContext
from indentgen.taxonomy_def_set import MetaTaxonomyContext

CONTENT_TAG_SET = 'indentgen_content'

content_tag_set = defs_manager.copy_tag_set(CONTENT_TAG_SET) # copies from default Dentmark tags by default

content_tag_set.register_tag(MetaTaxonomyContext)


@content_tag_set.register(replace=True)
class IndentgenContentRoot(TagDef):
    tag_name = 'root'

    def before_render(self):
        inline_sum = self.collectors.get('sum')
        meta_summary = self.context['meta'].get('summary')
        pk = self.context['meta'].get('pk')

        taxonomy = self.context['meta'].get('taxonomy', {})

        if not pk and (inline_sum or meta_summary):
            return 'Content with no pk cannot have inline sum tags or meta summary'

        if (inline_sum and meta_summary):
            return 'Cannot declare meta.summary AND inline sum tags. Remove the meta.summary or the inline sum tags.'

        if pk and not (inline_sum or meta_summary):
            return 'Content with pk must declare an inline summary with sum tags OR a meta summary'


        # make sure bookmarks have bm tag
        if 'types/bookmarks' in taxonomy:
            if 'bm' not in self.context['meta']:
                return "Content belonging to taxonomy 'types/bookmarks' must define the 'bm' tag (root.meta.bm)"

            bm = self.context['meta']['bm']
            pub = bm['pub']
            author = bm['author']
            title = bm['title']

            # set the lead if it isn't declared
            if not self.context['meta'].get('lead'):
                self.context['meta']['lead'] = [f'By {author} / {pub}']
                self.context['meta']['lead_content'] = f'By {author} / {pub}'

            # set the description if it isn't declared
            if not self.context['meta'].get('description'):
                self.context['meta']['description'] = f'Thoughts on "{title}" from "{pub}"'

            # set the title if it isn't declared
            if not self.context['meta'].get('title'):
                self.context['meta']['title'] = title

            # TODO: maybe a big change/refactor in the future would be to add the ability to use entirely different TagSets
            # for different types (basically Hugo's notion of a archetype or whatever)

        # promote orphaned text nodes to 'p'
        for i,child in enumerate(self.children):
            if not child.is_element:
                promoted_elem = child.promote(Paragraph)
                self.children[i] = promoted_elem

        # decorate last 'p' with endmark
        # use gen_tags_by_name to find nested p tags (last p tag might be in summary for short posts)
        if self.context['meta'].get('pk') is not None: # Don't do this for info pages that don't have a pk
            p_tags = list(self.gen_tags_by_name('p'))
            if p_tags:
                last_child = self.children[-1]

                # this check ensures that the endmark isn't added if the last child is an img or some other content that
                # would cause the endmark to appear prior to it. Just omit the endmark for posts like this
                if last_child.is_element and (last_child.tag_name == 'p' or last_child.tag_name == 'sum'):
                    p_tags[-1].add_class('p__endmark')

        if 'types/articles' in taxonomy or 'types/thoughts' in taxonomy:
            # ensure thoughts and articles have title and description in meta
            # bookmarks are exempts since these are derived from root.meta.bm, but
            # override the derived versions if present

            if 'title' not in self.context['meta']:
                return "Content belonging to taxonomy 'articles' or 'thoughts' must define the 'title' tag (root.meta.title)"

            if 'description' not in self.context['meta']:
                return "Content belonging to taxonomy 'articles' or 'thoughts' must define the 'description' tag (root.meta.description)"


        if 'types/articles' in taxonomy:
            # use dropcap for first p of article and p following h2
            # use gen_tags_by_name to find nested p tags (first p tag might be in summary)

            # dropcap to first p in article, even if it is nested in a sum tag
            for child in self.gen_tags_by_name('p'):
                child.context['use_dropcap'] = ''
                break

            # add dropcaps to the first p following an h2
            for child in self.gen_tags_by_name('h2'):
                next_p = child.next_tag_of_type('p')
                if next_p:
                    next_p.context['use_dropcap'] = ''

            # add leadin styling to the first p following an h3
            for child in self.gen_tags_by_name('h3'):
                next_p = child.next_tag_of_type('p')
                if next_p:
                    next_p.context['use_leadin'] = ''

        # make sure only photos types have gallery tag
        if 'gallery' in self.context['meta']:
            # check against all the taxonomies since taxonomies specify gallery
            gallery_valid = False
            tax_defs = self.extra_context['indentgen'].taxonomy_map
            for tax_slug_path in taxonomy:
                if tax_defs[tax_slug_path]['gallery']:
                    gallery_valid = True
                    break
            if not gallery_valid:
                return "Only content with a taxonomy with 'gallery' set may define the 'gallery' tag (root.meta.gallery)"

            # do not specify meta.img since galleries draw from meta.gallery.img OR use the 1st image in the gallery
            # have to do it this way since the img tag won't populate until after render
            meta_def = self.get_child_by_name('meta')
            if meta_def.get_child_by_name('img'):
                return "meta.img prohibited for a gallery page. These draw the featured image from meta.gallery.img OR use the 1st image in the gallery"

            # check that multiple covers aren't specified
            if len(self.collectors.get('cover', [])) > 1:
                return "Only 1 cover tag can be specified for a root.meta.gallery.img tag. Multiple cover tags detected"


    def render_main(self):
        body = f'{self.content}'

        fns = self.collectors.get('fn', [])
        fns_rendered = ''.join(fns)

        taxonomy = self.context['meta'].get('taxonomy', {})

        if 'bm' in self.collectors:
            body = self.collectors['bm'][0] + body

        if 'articles' in taxonomy or self.context['meta']['slug'] == 'about':
            indentgen = self.extra_context['indentgen']

            if 'creative-writing' in taxonomy:
                url = '/who-is-nally-dupri/'
                sig_suffix = 'nd'
                alt = 'Nally Duprí'
            else:
                url = '/about/'
                sig_suffix = 'rd'
                alt = 'Ryli Dunlap'

            body += f'<p><a href="{url}"><img class="signature" src="/{indentgen.STATIC_URL}/img/signature_{sig_suffix}.png" alt="{alt}" /></a></p>'

        if fns_rendered:
            body += f'<section class="footnotes" role="doc-endnotes"><hr/><ol>{fns_rendered}</ol></section>'

        return body


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


@content_tag_set.register()
class MetaContext(TagDef):
    tag_name = 'meta'
    is_context = True

    min_num_text_nodes = 0
    max_num_text_nodes = 0

    parents = [RequiredUnique('root')]

    def process_data(self, data):
        return self.context


@content_tag_set.register()
class TitleMetaContext(TagDef):
    tag_name = 'title'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [OptionalUnique('root.meta')]


@content_tag_set.register()
class IndentgenContentMetaUseTemplate(TagDef):
    tag_name = 'use_template'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [OptionalUnique('root.meta')]

    def validate(self):
        path = self.get_data()
        indentgen = self.extra_context['indentgen']
        try:
            indentgen.templates.get_template(path)
        except Exception as e:
            return f'use_template: {e}'


# register this separately since TitleMetaContext is imported and used for
# Taxonomy config definitons too, which doesn't use root.meta.bm
@content_tag_set.register()
class TitleMetaBMContext(TitleMetaContext):
    parents = [RequiredUnique('root.meta.bm')]


@content_tag_set.register()
class SlugContext(ConfigURLContext):
    tag_name = 'slug'

    parents = [RequiredUnique('root.meta')]


@content_tag_set.register()
class PKContext(TagDef):
    tag_name = 'pk'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [OptionalUnique('root.meta')]

    def process_data(self, data):
        if not data:
            return None
        pk = int(data[0])
        if pk < 1:
            raise ValueError
        return pk


    def validate(self):
        try:
            self.get_data()
        except ValueError:
            return f"Tag '{self.tag_name}' expects a positive integer >= 1"


@content_tag_set.register()
class MetaDateContext(TagDef):
    tag_name = 'date'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [OptionalUnique('root.meta')]

    date_format = '%Y-%m-%d-%H%M'

    def process_data(self, data):
        time = data[0].strip()
        if len(time) == 10:
            # add default time
            time += '-0000'

        return datetime.datetime.strptime(time, self.date_format)

    def validate(self):
        try:
            # calls process_data() on first child text node
            self.get_data()
        except ValueError:
            return f"Invalid date value for Tag '{self.tag_name}' in meta"


@content_tag_set.register()
class MetaDisableCommentsContext(TagDef):
    tag_name = 'disable_comments'
    is_context = True

    min_num_text_nodes = 0
    max_num_text_nodes = 1

    parents = [OptionalUnique('root.meta')]

    def process_data(self, data):
        if data:
            return data[0].lower() == 'true'
        return True

    def validate(self):
        if self.children:
            if self.children[0].get_data().lower() not in ('true', 'false'):
                return f"'{self.tag_name}' tag value must be either 'true', 'false', or [empty]. Defaults to 'true' if [empty]"


@content_tag_set.register()
class ContentLead(TagDef):
    tag_name = 'lead'
    is_context = True

    parents = [OptionalUnique('root.meta')]

    def render_main(self):
        self.parent.context[f'{self.tag_name}_content'] = self.content
        return ''


@content_tag_set.register()
class ContentMetaDescription(TagDef):
    tag_name = 'description'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [OptionalUnique('root.meta')]


# Patch Image tag
@content_tag_set.register(replace=True)
class IndentgenContentImage(TagDef):
    tag_name = 'img'

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [Optional('root')]

    MAX_WIDTH = 800
    MAX_HEIGHT = 600

    def get_image_data(self):
        srp = self.extra_context['srp']
        wisdom = self.extra_context['indentgen'].wisdom
        lto = self.context.get('link_to_original', False)
        return wisdom.get_image_url(srp, self.content, self.MAX_WIDTH, self.MAX_HEIGHT, copy_original=lto)

    def render_main(self):
        key, resized_serve_path, original_serve_path = self.get_image_data()

        alt = self.context.get('alt', '')
        caption = self.context.get('caption', [])

        use_alt_text = alt or ' '.join(caption)
        use_alt = f' alt="{use_alt_text}"' if use_alt_text else ''

        img_src = f'<img src="{resized_serve_path}"{use_alt} />'

        lto = self.context.get('link_to_original', False)

        if lto:
            img_src = f'<a href="{original_serve_path}">{img_src}</a>'

        caption_content = self.context.get('caption_content', '')
        attr_content = self.context.get('attr_content', '')

        caption_attr_src = caption_content
        if caption_content and attr_content:
            caption_attr_src += ' / '
        caption_attr_src += attr_content

        if caption_attr_src:
            caption_attr_src = f'<figcaption><p class="figcaption__content">{caption_attr_src}</p></figcaption>'

        return f'<figure>{img_src}{caption_attr_src}</figure>'


@content_tag_set.register()
class IndentgenContentImageMeta(IndentgenContentImage):

    parents = [OptionalUnique('root.meta'), Optional('root.meta.gallery')]

    def render_main(self):
        img_ctx = self.parent.context.setdefault('img', [])
        self.context['key'] = self.get_image_data()[0]
        img_ctx.append(self.context)
        return ''


@content_tag_set.register()
class IndentgenContentImageLinkToOriginal(MetaDisableCommentsContext):
    tag_name = 'link_to_original'

    parents = [OptionalUnique('root.img')]


@content_tag_set.register()
class IndentgenContentImageAttr(TagDef):
    tag_name = 'attr'
    is_context = True

    parents = [OptionalUnique('root.img'), OptionalUnique('root.meta.img'), OptionalUnique('root.meta.gallery.img')]

    def render_main(self):
        self.parent.context[f'{self.tag_name}_content'] = self.content
        return ''


@content_tag_set.register()
class IndentgenContentImageCaption(IndentgenContentImageAttr):
    tag_name = 'caption'
    is_context = True

    def process_data(self, data):
        return [' '.join(x.text for x in self.strip_tags())]


@content_tag_set.register()
class IndentgenContentImageGalleryCover(MetaDisableCommentsContext):
    tag_name = 'cover'
    add_to_collector = True

    parents = [OptionalUnique('root.meta.gallery.img')]


@content_tag_set.register()
class IndentgenContentSummaryBody(TagDef):
    tag_name = 'sum'
    add_to_collector = True

    parents = [Optional('root'), Optional('root.p'), Optional('root.p.a8n')]


@content_tag_set.register()
class IndentgenContentSummaryMeta(TagDef):
    tag_name = 'summary'
    is_context = True

    parents = [OptionalUnique('root.meta')]

    def validate(self):
        if not self.children:
            return 'Meta summary cannot be blank/empty if present. Must have at least one child'

    def render_main(self):
        self.parent.context[f'{self.tag_name}_content'] = self.content
        return ''


# patch these for img
@content_tag_set.register()
class IndentgenContentImageMetaAlt(ImgAltContext):
    parents = [Optional('root.meta.img')]


@content_tag_set.register()
class IndentgenContentImageMetaTitle(ImgTitleContext):
    parents = [Optional('root.meta.img')]


@content_tag_set.register(replace=True)
class IndentgenContentImageAnchor(Anchor):
    parents = [
        Optional('root'),
        Optional('root.p'),
        Optional('root.p.a8n.fn'),
        Optional('root.bq.a8n.fn'),
        Optional('root.img.attr'),
        Optional('root.meta.img.attr'),
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
        Optional('root.p.a8n.fn.a'),
        Optional('root.bq.a8n.fn.a'),
        OptionalUnique('root.img.attr.a'),
        OptionalUnique('root.meta.img.attr.a'),
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
        OptionalUnique('root.p.hl.a')
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
        Optional('root.ul.li.a8n.fn')
    ]


@content_tag_set.register()
class IndentgenContenBqA8n(Annotation):
    parents = [Optional('root.bq.p'), Optional('root.ul.li')]

@content_tag_set.register()
class IndentgenContenBqFootnote(FootNote):
    parents = [Optional('root.bq.p.a8n'), Optional('root.ul.li.a8n')]

@content_tag_set.register()
class IndentgenContentBr(Break):
    parents = [Optional('root.conv.msg.p')]


@content_tag_set.register(replace=True)
class IndentgenContentBlockQuote(BlockQuote):

    def before_render(self):
        # promote orphaned text nodes to 'p'
        for i,child in enumerate(self.children):
            if not child.is_element:
                promoted_elem = child.promote(Paragraph)
                self.children[i] = promoted_elem


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


@content_tag_set.register()
class IndentgenContentPutRef(TagDef):
    tag_name = 'putref'

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [Optional('root')]

    # Use get_data() here to get the value since self.content won't be available yet during the before_render check

    def render_main(self):
        id_split = self.get_data().split('-')
        index = int(id_split[-1]) - 1 # tag_value is 1-indexed
        if index < 0:
            raise ValueError
        tag_name_key = '-'.join(id_split[:-1])
        return self.root.collectors[tag_name_key][index]

    def before_render(self):
        try:
            self.render_main()
        except (ValueError, KeyError, IndexError) as e:
            return f'Invalid putref key: {self.get_data()}'


@content_tag_set.register()
class IndentgenContentBookMark(TagDef):
    tag_name = 'bm'
    is_context = True
    add_to_collector = True

    min_num_text_nodes = 0
    max_num_text_nodes = 0

    parents = [OptionalUnique('root.meta')]

    def process_data(self, data):
        return self.context

    def render_secondary(self):
        pub = self.context['pub']
        url = self.context['url']
        author = self.context['author']
        diigo = self.context.get('diigo')

        annotated_src = ''
        if diigo:
            annotated_src = f' <small>[ <a href="https://diigo.com/{diigo}">Annotated Version</a> ]</small>'

        return f'<p class="bookmark__link">Original Source: <a href="{url}"><i>{pub}</i></a>{annotated_src}</p>'


@content_tag_set.register()
class IndentgenContentBookMarkURL(TagDef):
    tag_name = 'url'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [RequiredUnique('root.meta.bm')]


@content_tag_set.register()
class IndentgenContentBookMarkPublication(IndentgenContentBookMarkURL):
    tag_name = 'pub'


@content_tag_set.register()
class IndentgenContentBookMarkAuthor(IndentgenContentBookMarkURL):
    tag_name = 'author'


@content_tag_set.register()
class IndentgenContentBookMarkDiigo(TagDef):
    tag_name = 'diigo'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [OptionalUnique('root.meta.bm')]


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
        # promote orphaned text nodes to 'li'
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
class IndentgenContentAside(TagDef):
    tag_name = 'aside'

    parents = [Optional('root')]

    def render_main(self):
        return f'<div class="aside">{self.content}</div>'


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
class IndentgenContentMessageExtractLink(IndentgenContentImageAnchorURL):
    tag_name = 'link'

    parents = [RequiredUnique('root.extract')]


@content_tag_set.register()
class IndentgenContentPhotoGallery(TagDef):
    tag_name = 'gallery'
    is_context = True

    min_num_text_nodes = 0
    max_num_text_nodes = 0

    parents = [OptionalUnique('root.meta')]

    def process_data(self, data):
        return self.context


@content_tag_set.register()
class IndentgenContentPhotoGalleryPerPage(TagDef):
    tag_name = 'per_page'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [OptionalUnique('root.meta.gallery')]

    def process_data(self, data):
        per_page = int(data[0])
        if per_page < 0:
            raise ValueError
        return per_page


    def validate(self):
        try:
            self.get_data()
        except ValueError:
            return f"Tag '{self.tag_name}' in meta.gallery expects a positive integer"

