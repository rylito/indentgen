from dentmark import TagDef, Optional
from . content_tag_set import content_tag_set
from dentmark.default_definitions import Paragraph

@content_tag_set.register(replace=True)
class IndentgenContentRoot(TagDef):
    tag_name = 'root'

    def before_render(self):
        inline_sum = self.collectors.get('sum')
        meta_summary = self.context['meta'].get('summary')
        pk = self.context['meta'].get('pk')
        date = self.context['meta'].get('date')

        taxonomy = self.context['meta'].get('taxonomy', {})

        if not pk and (inline_sum or meta_summary):
            return 'Content with no pk cannot have inline sum tags or meta summary'

        if (inline_sum and meta_summary):
            return 'Cannot declare meta.summary AND inline sum tags. Remove the meta.summary or the inline sum tags.'

        if pk and not (inline_sum or meta_summary):
            return 'Content with pk must declare an inline summary with sum tags OR a meta summary'

        if pk and not date:
            return 'Content with pk must declare a date'

        is_gallery = False
        tax_defs = self.extra_context['indentgen'].taxonomy_map
        for tax_slug_path in taxonomy:
            try:
                is_gallery = tax_defs[tax_slug_path]['gallery']
            except KeyError:
                pass

            if is_gallery:
                break

        # make sure bookmarks have bm tag
        if 'types/reviews/articles' in taxonomy:
            if 'bm' not in self.context['meta']:
                return "Content belonging to taxonomy 'types/reviews/articles' must define the 'bm' tag (root.meta.bm)"

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

        # make sure book reviews have book tag
        if 'types/reviews/books' in taxonomy:
            if 'book' not in self.context['meta']:
                return "Content belonging to taxonomy 'types/reviews/books' must define the 'book' tag (root.meta.book)"

            book = self.context['meta']['book']
            author = book['author']
            title = book['title']

            # set the lead if it isn't declared
            if not self.context['meta'].get('lead'):
                self.context['meta']['lead'] = [f'By {author}']
                self.context['meta']['lead_content'] = f'By {author}'

            # set the description if it isn't declared
            if not self.context['meta'].get('description'):
                self.context['meta']['description'] = f'Thoughts on "{title}" by {author}'

            # set the title if it isn't declared
            if not self.context['meta'].get('title'):
                self.context['meta']['title'] = title

            # TODO: maybe a big change/refactor in the future would be to add the ability to use entirely different TagSets
            # for different types (basically Hugo's notion of a archetype or whatever)

        # TODO: check that meta does not have both bm and book. Check that tax does not include both reviews/articles and reviews/books

        # promote orphaned text nodes to 'p'
        for i,child in enumerate(self.children):
            if not child.is_element:
                promoted_elem = child.promote(Paragraph)
                self.children[i] = promoted_elem

        # decorate last 'p' with endmark
        # use gen_tags_by_name to find nested p tags (last p tag might be in summary for short posts)
        # don't do this for gallery pages
        if self.context['meta'].get('pk') is not None and not is_gallery: # Don't do this for info pages that don't have a pk
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
            if not is_gallery:
                return "Only content with a taxonomy with 'gallery' set may define the 'gallery' tag (root.meta.gallery)"

        # do not specify meta.img since galleries draw from meta.gallery.img OR use the 1st image in the gallery
        # have to do it this way since the img tag won't populate until after render
        if is_gallery:
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

        if 'book' in self.collectors:
            body = self.collectors['book'][0] + body

        if 'types/articles' in taxonomy or self.context['meta']['slug'] == 'about':
            indentgen = self.extra_context['indentgen']

            if 'categories/creative-writing' in taxonomy:
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


