import re
#import datetime

from dentmark import defs_manager, TagDef
#from dentmark.default_definitions.anchor import TitleContext
#from indentgen.default_definitions import ConfigURLContext

CONFIG_TAG_SET = 'indentgen_config'

config_tag_set = defs_manager.get_tag_set(CONFIG_TAG_SET)


class ConfigURLContext(TagDef):
    is_context = True
    allow_children = []

    min_num_children = 1
    max_num_children = 1

    url_pattern = re.compile(r'^(?P<url>[a-z0-9][a-z0-9-]*[a-z0-9])$')

    def validate(self):
        val = self.get_data()
        if not self.url_pattern.match(val):
            return f"Tag '{self.tag_name}' contains invalid format for a slug. Can contain only [a-z0-9-] and cannot begin or end with '-'"



@config_tag_set.register()
class ConfigRoot(TagDef):
    tag_name = 'root'
    is_root = True
    allow_children = ['date_archive_url', 'title', 'description', 'per_page']

    unique_children = ['date_archive_url', 'title', 'description', 'per_page']
    #required_children = []

    min_num_children = 0
    max_num_children = 0

    def render_main(self):
        return self.context # just return the context to get the config data so we can use render. Config file has no body content, all context

@config_tag_set.register()
class ConfigDateArchiveURL(ConfigURLContext):
    tag_name = 'date_archive_url'


@config_tag_set.register()
class ConfigTitle(TagDef):
    tag_name = 'title'
    is_context = True
    allow_children = []

    min_num_children = 1
    max_num_children = 1


@config_tag_set.register()
class ConfigDescription(ConfigTitle):
    tag_name = 'description'
    #is_context = True
    #allow_children = []

    #min_num_children = 1
    #max_num_children = 1

@config_tag_set.register()
class ConfigPerPage(ConfigTitle):
    tag_name = 'per_page'
    #is_context = True
    #allow_children = []

    #min_num_children = 1
    #max_num_children = 1


    def process_data(self, data):
        per_page = int(data[0])
        if per_page < 0:
            raise ValueError
        return per_page


    def validate(self):
        try:
            self.get_data()
        except ValueError:
            return f"Tag '{self.tag_name}' in config expects a positive integer"



print('default indentgen config definitions loaded')
