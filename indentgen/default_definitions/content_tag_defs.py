import datetime

from dentmark import defs_manager, TagDef

from dentmark.default_definitions import Root, Paragraph
from dentmark.default_definitions.lists import ListItem
from indentgen.default_definitions.config_tag_defs import ConfigURLContext
#from indentgen.default_definitions.taxonomy_tag_defs import TaxonomyMetaContext, TAXONOMY_TAG_SET

CONTENT_TAG_SET = 'indentgen_content'

content_tag_set = defs_manager.copy_tag_set(CONTENT_TAG_SET) # copies from default Dentmark tags by default


@content_tag_set.register()
class MetaContext(TagDef):
    tag_name = 'meta'
    is_context = True
    allow_children = ['slug', 'title', 'pk', 'taxonomy', 'date']

    required_children = ['slug', 'title', 'date'] # TODO should aliases go here too? Keep it optional for now. Maybe taxonomy should be optional?
    unique_children = ['slug', 'title', 'pk', 'taxonomy', 'date']

    min_num_children = 0
    max_num_children = 0

    def process_data(self, data):
        return self.context


@content_tag_set.register()
class SlugContext(ConfigURLContext):
    tag_name = 'slug'


@content_tag_set.register()
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


@content_tag_set.register()
class MetaTaxonomyContext(TagDef):
    tag_name = 'taxonomy'
    is_context = True
    allow_children = []

    #TODO maybe default should be to make this optional?
    # For now, I'm always going to want at least one (type)
    min_num_children = 1


@content_tag_set.register()
class MetaDateContext(TagDef):
    tag_name = 'date'
    is_context = True
    allow_children = []

    min_num_children = 1
    max_num_children = 1

    date_format = '%Y-%m-%d'

    def process_data(self, data):
        return datetime.datetime.strptime(data[0], self.date_format).date()

    def validate(self):
        try:
            # calls process_data() on first child text node
            self.get_data()
        except ValueError:
            return f"Invalid date value for Tag '{self.tag_name}' in meta"


# patch default dentmark tags to include/exclude meta
@content_tag_set.register(replace=True)
class Root(Root):
    exclude_children = ['date', 'pk', 'slug', 'taxonomy', 'title'] # TODO just for testing - delme and add correct children

    required_children = ['meta']
    unique_children = ['meta']

@content_tag_set.register(replace=True)
class Paragraph(Paragraph):
    exclude_children = ['p', 'li', 'bq', 'meta', 'pk', 'slug', 'taxonomy', 'title', 'date']

@content_tag_set.register(replace=True)
class ListItem(ListItem):
    exclude_children = ['meta', 'meta', 'pk', 'slug', 'taxonomy', 'title', 'date']

#for k,v in content_tag_set.tag_dict.items():
    #print(k)
#input('HOLD')
