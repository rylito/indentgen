from dentmark import defs_manager, TagDef

from dentmark.default_definitions import Root, Paragraph
from dentmark.default_definitions.lists import ListItem
from indentgen.default_definitions.config_tag_defs import ConfigURLContext
from indentgen.default_definitions.content_tag_defs import MetaContext, SlugContext

TAXONOMY_TAG_SET = 'indentgen_taxonomy'

taxonomy_tag_set = defs_manager.copy_tag_set(TAXONOMY_TAG_SET)

#taxonomy_tag_set.remove_tag('date')

@taxonomy_tag_set.register()
class TaxonomyMetaContext(MetaContext):
    allow_children = ['slug', 'title', 'parent']

    required_children = ['slug', 'title']
    unique_children = ['slug', 'title', 'parent']


@taxonomy_tag_set.register()
class TaxonomyParentContext(TagDef):
    tag_name = 'parent'
    is_context = True
    allow_children = []

    min_num_children = 1
    max_num_children = 1


taxonomy_tag_set.register_tag(SlugContext)



# patch default dentmark tags to include/exclude meta
@taxonomy_tag_set.register(replace=True)
class Root(Root):
    exclude_children = ['slug', 'title', 'parent'] # TODO just for testing - delme and add correct children

    required_children = ['meta']
    unique_children = ['meta']

@taxonomy_tag_set.register(replace=True)
class Paragraph(Paragraph):
    exclude_children = ['p', 'li', 'bq', 'meta', 'slug', 'title', 'parent']

@taxonomy_tag_set.register(replace=True)
class ListItem(ListItem):
    exclude_children = ['meta', 'meta', 'slug', 'title', 'parent']

