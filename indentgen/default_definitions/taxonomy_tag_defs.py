from dentmark import defs_manager, TagDef, OptionalUnique, RequiredUnique
from dentmark.default_definitions import Root
from indentgen.default_definitions.content_tag_defs import MetaContext, SlugContext, MetaTaxonomyContext, TitleMetaContext

TAXONOMY_TAG_SET = 'indentgen_taxonomy'

taxonomy_tag_set = defs_manager.copy_tag_set(TAXONOMY_TAG_SET)


@taxonomy_tag_set.register(replace=True)
class IndentgenTaxonomyRoot(Root):

    def before_render(self):
        meta = self.context['meta']
        taxonomies = meta.get('taxonomy', {})
        slug = meta['slug']

        parent = None

        for tax_slug, (order, is_parent) in taxonomies.items():
            if tax_slug == slug:
                return f"Cannot list self as a taxonomy: '{tax_slug}'"

            if is_parent:
                if parent:
                    return 'Cannot have more than 1 taxonomy marked as parent'
                parent = tax_slug

        if taxonomies and not parent:
            return "A taxonomy must be set as the parent using the 'parent' tag and cannot be false"


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


taxonomy_tag_set.register_tag(MetaContext)
taxonomy_tag_set.register_tag(SlugContext)
taxonomy_tag_set.register_tag(MetaTaxonomyContext)
taxonomy_tag_set.register_tag(TitleMetaContext)
