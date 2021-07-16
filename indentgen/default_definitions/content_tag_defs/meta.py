import datetime
from dentmark import TagDef, BoolTagDef, PosIntTagDef, Optional, OptionalUnique, RequiredUnique
from . content_tag_set import content_tag_set
from indentgen.default_definitions.config_tag_defs import SlugTagDef

@content_tag_set.register()
class MetaContext(TagDef):
    tag_name = 'meta'
    is_context = True

    min_num_text_nodes = 0
    max_num_text_nodes = 0

    parents = [RequiredUnique('root')]

    def process_data(self, data):
        return self.context


@content_tag_set.register()
class TitleMetaContext(TagDef):
    tag_name = 'title'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [OptionalUnique('root.meta')]


@content_tag_set.register()
class IndentgenContentMetaUseTemplate(TagDef):
    tag_name = 'use_template'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [OptionalUnique('root.meta')]

    def validate(self):
        path = self.get_data()
        indentgen = self.extra_context['indentgen']
        try:
            indentgen.templates.get_template(path)
        except Exception as e:
            return f'use_template: {e}'


# register this separately since TitleMetaContext is imported and used for
# Taxonomy config definitons too, which doesn't use root.meta.bm
@content_tag_set.register()
class TitleMetaBMContext(TitleMetaContext):
    parents = [RequiredUnique('root.meta.bm'), RequiredUnique('root.meta.book')]


@content_tag_set.register()
class SlugContext(SlugTagDef):
    tag_name = 'slug'

    parents = [RequiredUnique('root.meta')]


@content_tag_set.register()
class PKContext(PosIntTagDef):
    tag_name = 'pk'

    parents = [OptionalUnique('root.meta')]


@content_tag_set.register()
class MetaDateContext(TagDef):
    tag_name = 'date'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [OptionalUnique('root.meta')]

    date_format = '%Y-%m-%d-%H%M'

    def process_data(self, data):
        time = data[0].strip()
        if len(time) == 10:
            # add default time
            time += '-0000'

        return datetime.datetime.strptime(time, self.date_format)

    def validate(self):
        try:
            # calls process_data() on first child text node
            self.get_data()
        except ValueError:
            return f"Invalid date value for Tag '{self.tag_name}' in meta"


@content_tag_set.register()
class MetaDisableCommentsContext(BoolTagDef):
    tag_name = 'disable_comments'

    parents = [OptionalUnique('root.meta')]


@content_tag_set.register()
class ContentLead(TagDef):
    tag_name = 'lead'
    is_context = True

    parents = [OptionalUnique('root.meta')]

    def render_main(self):
        self.parent.context[f'{self.tag_name}_content'] = self.content
        return ''


@content_tag_set.register()
class ContentMetaDescription(TagDef):
    tag_name = 'description'
    is_context = True

    min_num_text_nodes = 1
    max_num_text_nodes = 1

    parents = [OptionalUnique('root.meta')]


# not actually a child of meta, but place here since it has to do with meta.summary
@content_tag_set.register()
class IndentgenContentSummaryBody(TagDef):
    tag_name = 'sum'
    add_to_collector = True

    parents = [Optional('root'), Optional('root.p'), Optional('root.p.a8n')]


@content_tag_set.register()
class IndentgenContentSummaryMeta(TagDef):
    tag_name = 'summary'
    is_context = True

    min_num_text_nodes = 1

    parents = [OptionalUnique('root.meta')]

    def render_main(self):
        self.parent.context[f'{self.tag_name}_content'] = self.content
        return ''


@content_tag_set.register()
class IndentgenContentPhotoGallery(TagDef):
    tag_name = 'gallery'
    is_context = True

    min_num_text_nodes = 0
    max_num_text_nodes = 0

    parents = [OptionalUnique('root.meta')]

    def process_data(self, data):
        return self.context


@content_tag_set.register()
class IndentgenContentPhotoGalleryPerPage(PosIntTagDef):
    tag_name = 'per_page'

    parents = [OptionalUnique('root.meta.gallery')]


@content_tag_set.register()
class IdentgenContentMetaManifest(TagDef):
    tag_name = 'manifest'
    is_context = True

    min_num_text_nodes = 1

    parents = [OptionalUnique('root.meta')]

    def process_data(self, data):
        indentgen_obj = self.extra_context['indentgen']
        dentmark_srp = self.extra_context['srp']

        paths = []
        for filepath in data:
            full_path = indentgen_obj.site_path / dentmark_srp.parent / filepath

            try:
                resolved = full_path.resolve(True) # make sure the image exists
                relative = resolved.relative_to(indentgen_obj.site_path) # make sure relative path doesn't ascend past the site_path
            except (ValueError, FileNotFoundError) as e:
                raise Exception(f"Invalid url in manifest: {filepath}")

            paths.append(relative)
        return paths


    def validate(self):
        try:
            data = self.get_data()
        except Exception as e:
            return e

        name_set = set()

        for filepath in data:
            name = filepath.name
            if name in name_set:
                return f"Filename collision in manifest: {name}"
            name_set.add(name)

