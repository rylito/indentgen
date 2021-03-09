import datetime

from dentmark import defs_manager, TagDef, Optional, OptionalUnique, RequiredUnique

from dentmark.default_definitions.anchor import Anchor, URLContext, AnchorTitleContext
from dentmark.default_definitions.images import ImgAltContext, ImgTitleContext
#from dentmark.default_definitions import Root, Paragraph
#from dentmark.default_definitions.lists import ListItem
from indentgen.default_definitions.config_tag_defs import ConfigURLContext
#from indentgen.default_definitions.taxonomy_tag_defs import TaxonomyMetaContext, TAXONOMY_TAG_SET

CONTENT_TAG_SET = 'indentgen_content'

content_tag_set = defs_manager.copy_tag_set(CONTENT_TAG_SET) # copies from default Dentmark tags by default

@content_tag_set.register()
class MetaTaxonomyContext(TagDef):
    tag_name = 'taxonomy'
    is_context = True

    #exclude_children = [] # just allow everything... will check them later with a custom tag set class
    parents = [OptionalUnique('root.meta')]

    min_num_text_nodes = 0 # don't allow text nodes
    max_num_text_nodes = 0

    def process_data(self, data):
        return self.context

    #def check_children(self, child_relations):
        #pass


@content_tag_set.register()
class MetaContext(TagDef):
    tag_name = 'meta'
    is_context = True
    #allow_children = ['slug', 'title', 'pk', 'taxonomy', 'date', 'disable_comments']

    #required_children = ['slug', 'title'] # TODO should aliases go here too? Keep it optional for now. Maybe taxonomy should be optional?
    #unique_children = ['slug', 'title', 'pk', 'taxonomy', 'date', 'disable_comments']

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

    parents = [RequiredUnique('root.meta')]


@content_tag_set.register()
class SlugContext(ConfigURLContext):
    tag_name = 'slug'

    parents = [RequiredUnique('root.meta')]


@content_tag_set.register()
class PKContext(TagDef):
    tag_name = 'pk'
    is_context = True
    #allow_children = []

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [OptionalUnique('root.meta')]

    def validate(self):
        val = self.get_data()
        if not val.isdigit():
            return f"Tag '{self.tag_name}' expects a positive integer"


@content_tag_set.register()
class MetaDateContext(TagDef):
    tag_name = 'date'
    is_context = True
    #allow_children = []

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [OptionalUnique('root.meta')]

    date_format = '%Y-%m-%d'

    def process_data(self, data):
        return datetime.datetime.strptime(data[0], self.date_format).date()

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
    #allow_children = []

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
    #allow_children = []

    #add_to_collector = True

    parents = [OptionalUnique('root.meta')]

    def render_main(self):
        self.parent.context[f'{self.tag_name}_content'] = self.content
        return ''





# patch default dentmark tags to include/exclude meta
#@content_tag_set.register(replace=True)
#class Root(Root):
    #exclude_children = ['date', 'pk', 'slug', 'title', 'taxonomy', 'disable_comments']

    #required_children = ['meta']
    #unique_children = ['meta', 'lead']

#@content_tag_set.register(replace=True)
#class Paragraph(Paragraph):
    #exclude_children = ['p', 'li', 'bq', 'meta', 'pk', 'slug', 'title', 'date', 'taxonomy', 'disable_comments', 'lead']

#@content_tag_set.register(replace=True)
#class ListItem(ListItem):
    #exclude_children = ['meta', 'meta', 'pk', 'slug', 'title', 'date', 'taxonomy', 'disable_comments', 'lead']

#for k,v in content_tag_set.tag_dict.items():
    #print(k)
#input('HOLD')


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
        wisdom = self.extra_context['wisdom']
        lto = self.context.get('link_to_original', False)
        return wisdom.get_image_url(srp, self.content, self.MAX_WIDTH, self.MAX_HEIGHT, copy_original=lto)

    def render_main(self):
        #srp = self.extra_context['srp']
        #wisdom = self.extra_context['wisdom']


        #key, resized_serve_path, original_serve_path = wisdom.get_image_url(srp, self.content, 800, 600, copy_original=lto)
        key, resized_serve_path, original_serve_path = self.get_image_data()

        #print(self.context)
        #input('HOLD')

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
            caption_attr_src = f'<p class="figcaption__content">{caption_attr_src}</p>'

        return f'<figure>{img_src}{caption_attr_src}</figure>'

    #def validate

@content_tag_set.register()
class IndentgenContentImageMeta(IndentgenContentImage):
    tag_name = 'img'
    is_context = True

    parents = [Optional('root.meta')]

    def render_main(self):
        #self.context['img_key'] = self.get_image_data()[0]
        print(self.parent.context)
        #input('Hold it here 33')
        self.parent.context['img']['key'] = self.get_image_data()[0]
        return ''

    def process_data(self, data):
        return self.context

    #def process_data(self, data):
        #print('data', data)
        #print(self.content)
        #input('HOLD')

        #self.context['img_key'] = self.get_image_data()[0]


        #meta_ctx = {}

        #for attr in ('attr_content', 'caption_content', 'caption', 'alt'):


        #meta_ctx = {
            #'attr_content': self.context.get('attr_content', ''),
            #'caption_content': self.context.get('caption_content', ''),
            #'caption': self.context.get('caption', []),
            #'alt': self.context.get('alt', ''),
        #}
        #return self.context



@content_tag_set.register()
class IndentgenContentImageLinkToOriginal(MetaDisableCommentsContext):
    tag_name = 'link_to_original'

    parents = [OptionalUnique('root.img')]


@content_tag_set.register()
class IndentgenContentImageAttr(TagDef):
    tag_name = 'attr'
    is_context = True

    parents = [OptionalUnique('root.img'), OptionalUnique('root.meta.img')]

    def render_main(self):
        self.parent.context[f'{self.tag_name}_content'] = self.content
        return ''


@content_tag_set.register()
class IndentgenContentImageCaption(IndentgenContentImageAttr):
    tag_name = 'caption'
    is_context = True

    #parents = [OptionalUnique('root.img')]



# patch these
@content_tag_set.register()
class IndentgenContentImageMetaAlt(ImgAltContext):
    parents = [Optional('root.meta.img')]

@content_tag_set.register()
class IndentgenContentImageMetaTitle(ImgTitleContext):
    parents = [Optional('root.meta.img')]



@content_tag_set.register()
class IndentgenContentImageAnchor(Anchor):
    parents = [Optional('root.img.attr'), Optional('root.meta.img.attr')]

@content_tag_set.register()
class IndentgenContentImageAnchorURL(URLContext):
    parents = [OptionalUnique('root.img.attr.a'), OptionalUnique('root.meta.img.attr.a')]

@content_tag_set.register()
class IndentgenContentImageAnchorTitle(AnchorTitleContext):
    parents = [OptionalUnique('root.img.attr.a'), OptionalUnique('root.meta.img.attr.a')]



