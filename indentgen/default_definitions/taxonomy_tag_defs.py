from dentmark import defs_manager, TagDef, OptionalUnique, RequiredUnique

#from dentmark.default_definitions import Root, Paragraph
#from dentmark.default_definitions.lists import ListItem
#from indentgen.default_definitions.config_tag_defs import ConfigURLContext
from indentgen.default_definitions.content_tag_defs import MetaContext, SlugContext, MetaTaxonomyContext, TitleMetaContext

TAXONOMY_TAG_SET = 'indentgen_taxonomy'

taxonomy_tag_set = defs_manager.copy_tag_set(TAXONOMY_TAG_SET)

#taxonomy_tag_set.remove_tag('date')

#@taxonomy_tag_set.register()
#class TaxonomyMetaTaxonomyContext(MetaTaxonomyContext):
    # 
    #pass

#@taxonomy_tag_set.register()
#class TaxonomyMetaContext(MetaContext):
    #allow_children = ['slug', 'title', 'parent', 'pseudo', 'taxonomy']

    #required_children = ['slug', 'title']
    #unique_children = ['slug', 'title', 'parent', 'pseudo']


#@taxonomy_tag_set.register()
#class TaxonomyParentContext(TagDef):
    #tag_name = 'parent'
    #is_context = True
    #allow_children = []

    #min_num_text_nodes = 1
    #max_num_text_nodes = 1

    #parents = [OptionalUnique('root.meta')]


@taxonomy_tag_set.register()
class TaxonomyPseudoContext(TagDef):
    tag_name = 'pseudo'
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
                return f"'pseudo' tags value must be either 'true', 'false', or [empty]. Defaults to 'true' if [empty]"


taxonomy_tag_set.register_tag(MetaContext)
taxonomy_tag_set.register_tag(SlugContext)
taxonomy_tag_set.register_tag(MetaTaxonomyContext)
taxonomy_tag_set.register_tag(TitleMetaContext)



# patch default dentmark tags to include/exclude meta
#@taxonomy_tag_set.register(replace=True)
#class Root(Root):
    #exclude_children = ['slug', 'title', 'parent', 'pseudo', 'taxonomy']

    #required_children = ['meta']
    #unique_children = ['meta']

#@taxonomy_tag_set.register(replace=True)
#class Paragraph(Paragraph):
    #exclude_children = ['p', 'li', 'bq', 'meta', 'slug', 'title', 'parent', 'pseudo', 'taxonomy']

#@taxonomy_tag_set.register(replace=True)
#class ListItem(ListItem):
    #exclude_children = ['meta', 'meta', 'slug', 'title', 'parent', 'pseudo', 'taxonomy']

