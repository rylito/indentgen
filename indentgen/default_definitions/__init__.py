import re
from dentmark.default_definitions import *

# custom overrides
#from .anchor import Anchor, URLContext, IDContext

class MetaContext(TagDef):
    tag_name = 'meta'
    is_context = True
    allow_children = ['slug', 'title', 'pk', 'taxonomy']

    required_children = ['slug', 'title'] # TODO should aliases go here too? Keep it optional for now. Maybe taxonomy should be optional?
    unique_children = ['slug', 'title', 'pk', 'taxonomy']

    min_num_children = 0
    max_num_children = 0

    def process_data(self, data):
        return self.context


class ConfigURLContext(TagDef):
    is_context = True
    allow_children = []

    min_num_children = 1
    max_num_children = None

    #TODO don't allow slashes -> comp1/comp2
    url_pattern = re.compile(r'^/?(?P<url>.*?)/?$')

    def process_data(self, data):
        # url components should ignore leading/trailing '/'
        #return self.url_pattern.match(data[0]).group('url')
        no_slashes = [self.url_pattern.match(_).group('url') for _ in data]
        #return no_slashes[0] if len(no_slashes) == 1 else no_slashes
        return no_slashes


class SlugContext(ConfigURLContext):
    tag_name = 'slug'

    max_num_children = 1

    def process_data(self, data):
        return super().process_data(data)[0]


class PKContext(TagDef):
    tag_name = 'pk'
    is_context = True
    allow_children = []

    min_num_children = 1
    max_num_children = 1

    def validate(self):
        val = self.get_data()
        if not val.isdigit():
            return f"Tag '{self.tag_name}' expects a positive integer"


class MetaTaxonomyContext(TagDef):
    tag_name = 'taxonomy'
    is_context = True
    allow_children = []

    #TODO maybe default should be to make this optional?
    # For now, I'm always going to want at least one (type)
    min_num_children = 1

    def process_data(self, data):
        return data # TODO always return a list. Maybe this should be default in dentmark?


# patch default dentmark tags to include/exclude meta
class Root(Root):
    required_children = ['meta']
    unique_children = ['meta']

class Paragraph(Paragraph):
    exclude_children = ['p', 'li', 'bq', 'meta']

class ListItem(ListItem):
    exclude_children = ['meta']


REGISTERED_TAGS = (
    Root, MetaContext, SlugContext, PKContext, MetaTaxonomyContext,
    H1, H2, H3, H4, H5, H6,
    Anchor, URLContext, TitleContext,
    Pre,
    Paragraph,
    Annotation, FootNote,
    Italic, Bold, StrikeThrough,
    OrderedList, UnorderedList, ListItem,
    Table, TableRow, TableCell, ColspanContext, RowspanContext, AlignContext,
    BlockQuote,
    HorizontalRule,
    Break,
    Image, AltContext,
    YouTubeEmbed, WidthContext, HeightContext,
)


class TaxonomyParentContext(TagDef):
    tag_name = 'parent'
    is_context = True
    allow_children = []

    min_num_children = 1
    max_num_children = 1


class TaxonomyMetaContext(MetaContext):
    allow_children = ['slug', 'title', 'parent']

    required_children = ['slug', 'title']
    unique_children = ['slug', 'title', 'parent']



TAXONOMY_TAGS = (
    Root, TaxonomyMetaContext, SlugContext, TaxonomyParentContext,
    H1, H2, H3, H4, H5, H6,
    Anchor, URLContext, TitleContext,
    Pre,
    Paragraph,
    Annotation, FootNote,
    Italic, Bold, StrikeThrough,
    OrderedList, UnorderedList, ListItem,
    Table, TableRow, TableCell, ColspanContext, RowspanContext, AlignContext,
    BlockQuote,
    HorizontalRule,
    Break,
    Image, AltContext,
    YouTubeEmbed, WidthContext, HeightContext,

)



class ConfigRoot(TagDef):
    tag_name = 'root'
    is_root = True
    allow_children = ['date_archive_url', 'title', 'description', 'per_page']

    unique_children = ['date_archive_url', 'title', 'description', 'per_page']
    #required_children = []

    min_num_children = 0
    max_num_children = 0

    def render_main(self):
        return self.context # just return the context to get the config data


class ConfigDateArchiveURL(ConfigURLContext):
    tag_name = 'date_archive_url'

class ConfigDescription(TitleContext):
    tag_name = 'description'

class ConfigPerPage(TitleContext):
    tag_name = 'per_page'

    def process_data(self, data):
        try:
            per_page = int(data[0])
            if per_page < 0:
                raise ValueError
        except ValueError:
            raise Exception(f"Tag '{self.tag_name}' in config expects a positive integer: line {self.line_no}")
        return per_page


CONFIG_TAGS = (
    ConfigRoot,
    ConfigDateArchiveURL,
    TitleContext,
    ConfigDescription,
    ConfigPerPage,
)


print('default indentgen definitions loaded')
