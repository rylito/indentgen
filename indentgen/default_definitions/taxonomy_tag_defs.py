import re
from dentmark import defs_manager, TagDef, OptionalUnique, RequiredUnique
from dentmark.default_definitions import Root
from indentgen.default_definitions.content_tag_defs import MetaContext, TitleMetaContext
from indentgen.taxonomy_def_set import MetaTaxonomyContext

TAXONOMY_TAG_SET = 'indentgen_taxonomy'

taxonomy_tag_set = defs_manager.copy_tag_set(TAXONOMY_TAG_SET)


@taxonomy_tag_set.register(replace=True)
class IndentgenTaxonomyRoot(Root):

    def before_render(self):
        meta = self.context['meta']
        taxonomies = meta.get('taxonomy', {})
        slug_path = meta['slug_path']

        slug_path_components = slug_path.split('/')
        parent_slug_path = '/'.join(slug_path_components[:-1])

        if parent_slug_path and parent_slug_path not in taxonomies:
            taxonomies = meta.setdefault('taxonomy', {})
            taxonomies[parent_slug_path] = None

        if slug_path in taxonomies:
            return f"Cannot list self as a taxonomy: '{tax_slug_path}'"


@taxonomy_tag_set.register()
class TaxonomyPseudoContext(TagDef):
    tag_name = 'pseudo'
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
                return f"'pseudo' tags value must be either 'true', 'false', or [empty]. Defaults to 'true' if [empty]"


@taxonomy_tag_set.register()
class TaxonomyGalleryContext(TaxonomyPseudoContext):
    tag_name = 'gallery'

    def validate(self):
        if self.children:
            if self.children[0].get_data().lower() not in ('true', 'false'):
                return f"'gallery' tags value must be either 'true', 'false', or [empty]. Defaults to 'true' if [empty]"


@taxonomy_tag_set.register()
class ConfigSlugPathContext(TagDef):
    tag_name = 'slug_path'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [RequiredUnique('root.meta')]

    url_pattern = re.compile(r'^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:/[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*$')

    def validate(self):
        val = self.get_data()
        if not self.url_pattern.match(val):
            return f"Tag '{self.tag_name}' contains invalid format for a slug. Slug components can contain only [a-z0-9-] and cannot begin or end with '-' and must be separated by '/' with no leading and trailing '/'"


taxonomy_tag_set.register_tag(MetaContext)
taxonomy_tag_set.register_tag(MetaTaxonomyContext)
taxonomy_tag_set.register_tag(TitleMetaContext)
