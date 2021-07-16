from dentmark import TagDef, OptionalUnique, RequiredUnique
from . content_tag_set import content_tag_set

# begin meta.bm

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

        return f'<p class="bookmark__link">The following is my review of <a href="{url}">this article</a> from <i>{pub}</i>{annotated_src}</p>'


@content_tag_set.register()
class IndentgenContentBookMarkURL(TagDef):
    tag_name = 'url'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [RequiredUnique('root.meta.bm'), RequiredUnique('root.meta.book')]


@content_tag_set.register()
class IndentgenContentBookMarkPublication(TagDef):
    tag_name = 'pub'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1


    parents = [RequiredUnique('root.meta.bm')]


@content_tag_set.register()
class IndentgenContentBookMarkAuthor(TagDef):
    tag_name = 'author'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [RequiredUnique('root.meta.bm'), RequiredUnique('root.meta.book')]


@content_tag_set.register()
class IndentgenContentBookMarkDiigo(TagDef):
    tag_name = 'diigo'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [OptionalUnique('root.meta.bm')]


# begin meta.book

@content_tag_set.register()
class IndentgenContentBook(IndentgenContentBookMark):
    tag_name = 'book'

    def render_secondary(self):
        url = self.context['url']
        author = self.context['author']
        title = self.context['title']

        return f'<p class="bookmark__link">The following is my review of <a href="{url}"><i>{title}</i></a> by {author}</p>'


