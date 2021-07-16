import re
from dentmark import defs_manager, TagDef, PosIntTagDef, OptionalUnique, RequiredUnique

CONFIG_TAG_SET_NAME = 'indentgen_config'
SUBSITE_CONFIG_TAG_SET_NAME = 'indentgen_subsite_config'

config_tag_set = defs_manager.get_tag_set(CONFIG_TAG_SET_NAME)


class SlugTagDef(TagDef):
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    url_pattern = re.compile(r'^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$')

    def validate(self):
        val = self.get_data()
        if not self.url_pattern.match(val):
            return f"Tag '{self.tag_name}' contains invalid format for a slug. Can contain only [a-z0-9-] and cannot begin or end with '-'"



@config_tag_set.register()
class ConfigRoot(TagDef):
    tag_name = 'root'

    min_num_text_nodes = 0
    max_num_text_nodes = 0

    def render_main(self):
        return self.context # just return the context to get the config data so we can use render. Config file has no body content, all context


@config_tag_set.register()
class ConfigDateArchiveURL(SlugTagDef):
    tag_name = 'date_archive_url'

    parents = [OptionalUnique('root')]


@config_tag_set.register()
class ConfigTitle(TagDef):
    tag_name = 'title'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [OptionalUnique('root')]


@config_tag_set.register()
class ConfigDescription(TagDef):
    tag_name = 'description'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [OptionalUnique('root')]



@config_tag_set.register()
class ConfigPerPage(PosIntTagDef):
    tag_name = 'per_page'

    parents = [OptionalUnique('root')]


# copy from CONFIG_TAG_SET_NAME and add a few more required tags
subsite_config_tag_set = defs_manager.copy_tag_set(SUBSITE_CONFIG_TAG_SET_NAME, CONFIG_TAG_SET_NAME)

@subsite_config_tag_set.register()
class SubsiteConfigParentSlug(TagDef):
    tag_name = 'parent_slug'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [RequiredUnique('root')]


@subsite_config_tag_set.register()
class SubsiteConfigSubsiteSlug(TagDef):
    tag_name = 'subsite_slug'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [RequiredUnique('root')]

@subsite_config_tag_set.register()
class SubsiteConfigTemplatePathPrefix(TagDef):
    tag_name = 'template_path_prefix'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [OptionalUnique('root')]
