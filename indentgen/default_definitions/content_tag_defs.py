import datetime

from dentmark import defs_manager, TagDef

from dentmark.default_definitions import Root, Paragraph
from dentmark.default_definitions.lists import ListItem
from indentgen.default_definitions.config_tag_defs import ConfigURLContext
#from indentgen.default_definitions.taxonomy_tag_defs import TaxonomyMetaContext, TAXONOMY_TAG_SET

CONTENT_TAG_SET = 'indentgen_content'

content_tag_set = defs_manager.copy_tag_set(CONTENT_TAG_SET) # copies from default Dentmark tags by default

@content_tag_set.register()
class MetaTaxonomyContext(TagDef):
    tag_name = 'taxonomy'
    is_context = True

    exclude_children = [] # just allow everything... will check them later with a custom tag set class

    #TODO maybe default should be to make this optional?
    # For now, I'm always going to want at least one (type)
    min_num_children = 0 # don't allow non-context children
    max_num_children = 0

    def process_data(self, data):
        return self.context





@content_tag_set.register()
class MetaContext(TagDef):
    tag_name = 'meta'
    is_context = True
    allow_children = ['slug', 'title', 'pk', 'taxonomy', 'date', 'disable_comments']

    required_children = ['slug', 'title'] # TODO should aliases go here too? Keep it optional for now. Maybe taxonomy should be optional?
    unique_children = ['slug', 'title', 'pk', 'taxonomy', 'date', 'disable_comments']

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


@content_tag_set.register()
class MetaDisableCommentsContext(TagDef):
    tag_name = 'disable_comments'
    is_context = True
    allow_children = []

    min_num_children = 0
    max_num_children = 1

    def process_data(self, data):
        if data:
            return data[0].lower() == 'true'
        return True

    def validate(self):
        if self.children:
            if self.children[0].get_data().lower() not in ('true', 'false'):
                return f"'disable_comments' tag's value must be either 'true', 'false', or [empty]. Defaults to 'true' if [empty]"


@content_tag_set.register()
class ContentLead(TagDef):
    tag_name = 'lead'
    is_context = False
    allow_children = []

    add_to_collector = True

    def render_main(self):
        return ''

    def render_secondary(self):
        return self.content




# patch default dentmark tags to include/exclude meta
@content_tag_set.register(replace=True)
class Root(Root):
    #TODO figure out a better way to patch these with all the excludes, and taxonomy
    exclude_children = ['date', 'pk', 'slug', 'title', 'taxonomy', 'disable_comments']

    required_children = ['meta']
    unique_children = ['meta', 'lead']

@content_tag_set.register(replace=True)
class Paragraph(Paragraph):
    exclude_children = ['p', 'li', 'bq', 'meta', 'pk', 'slug', 'title', 'date', 'taxonomy', 'disable_comments', 'lead']

@content_tag_set.register(replace=True)
class ListItem(ListItem):
    exclude_children = ['meta', 'meta', 'pk', 'slug', 'title', 'date', 'taxonomy', 'disable_comments', 'lead']

#for k,v in content_tag_set.tag_dict.items():
    #print(k)
#input('HOLD')





