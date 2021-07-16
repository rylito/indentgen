from dentmark import TagDef, BoolTagDef, Optional, OptionalUnique
from . content_tag_set import content_tag_set
from dentmark.default_definitions.images import Image, ImgAltContext, ImgTitleContext

# Patch Image tag
@content_tag_set.register(replace=True)
class IndentgenContentImage(Image):

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
class IndentgenContentImageLinkToOriginal(BoolTagDef):
    tag_name = 'link_to_original'

    parents = [OptionalUnique('root.img')]


@content_tag_set.register()
class IndentgenContentImageAttr(TagDef):
    tag_name = 'attr'
    is_context = True

    #TODO maybe these should be split up since it defines an img tag for meta too
    parents = [OptionalUnique('root.img'), OptionalUnique('root.meta.img'), OptionalUnique('root.meta.gallery.img')]

    def render_main(self):
        self.parent.context[f'{self.tag_name}_content'] = self.content
        return ''


@content_tag_set.register()
class IndentgenContentImageCaption(IndentgenContentImageAttr):
    tag_name = 'caption'

    def process_data(self, data):
        return [' '.join(x.text for x in self.strip_tags())]


@content_tag_set.register()
class IndentgenContentImageGalleryCover(BoolTagDef):
    tag_name = 'cover'
    add_to_collector = True

    parents = [OptionalUnique('root.meta.gallery.img')]


# patch these for img
@content_tag_set.register()
class IndentgenContentImageMetaAlt(ImgAltContext):
    parents = [Optional('root.meta.img')]


@content_tag_set.register()
class IndentgenContentImageMetaTitle(ImgTitleContext):
    parents = [Optional('root.meta.img')]

