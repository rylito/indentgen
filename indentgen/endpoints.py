import math
from indentgen.page_store import PageStore
from calendar import month_name
from pathlib import Path

PAGE_URL = 'page' #TODO make this configurable in site settings?

class Endpoint:
    use_template = 'pages/home.html'
    srp = None
    is_taxonomy = False
    is_redirect = False

    def __init__(self, indentgen_obj, url_components, page=None, subsite_config=None):
        self.url_components = url_components
        self.page = page
        self.indentgen = indentgen_obj
        self.subsite_config = subsite_config

    def get_output_path(self):
        if self.page is None or self.page == 0:
            return Path(*self.url_components)
        else:
            components = list(self.url_components) # components could be tuples
            components.append(PAGE_URL)
            components.append(str(self.page + 1))
            return Path(*components)

    @property
    def url(self):
        if not self.url_components and not self.page:
            return '/'
        url = '/'.join(self.url_components)
        if self.page is not None and self.page > 0:
            url += f'/{PAGE_URL}/{self.page + 1}'
        # all routes except home are xxx/xxx and need to
        # have the '/' added at he beginning and end.
        # Paginated homepage URLS are just /page/xx
        # and so will have //page/xx if this check is
        # not in place:
        append_slash = '/' if url[0] != '/' else ''
        return f"{append_slash}{url}/"

    @property
    def identifier(self):
        return self.srp if self.srp is not None else self.url

    @property
    def meta(self):
        return {} # for compatibility with templates rather that having to do hasattr checks


    def render(self, indentgen_obj):

        context = {
            'page': self,
            'config': self.subsite_config or self.indentgen.config
        }

        use_template = self.use_template
        if self.subsite_config:
            template_path_prefix = self.subsite_config.get('template_path_prefix', '').strip('/') # strip any leading or trailing '/'
            if template_path_prefix:
                use_template = f'{template_path_prefix}/{self.use_template}'

        template = indentgen_obj.templates.get_template(use_template)
        return template.render(**context)


    def next_page(self):
        return Endpoint(self.indentgen, self.url_components, self.page + 1)


class ContentEndpoint(Endpoint):
    use_template = 'pages/content.html'

    def __init__(self, indentgen_obj, url_components, page, srp, subsite_config=None):
        super().__init__(indentgen_obj, url_components, page, subsite_config)
        self.srp = srp
        self.prev = None
        self.next = None

    #TODO perhaps optimize this so it doesn't read from cached wisdom .html files if only fetching root
    def get_rendered(self):
        return self.indentgen.wisdom.get_rendered(self.srp, self.is_taxonomy)

    @property
    def root(self):
        return self.get_rendered()[1]

    @property
    def content(self):
        return self.get_rendered()[0]

    @property
    def context(self):
        return self.root.context

    @property
    def meta(self):
        return self.context['meta']

    @property
    def summary(self):
        meta_summary = self.root.context['meta'].get('summary_content', '')
        if meta_summary:
            return meta_summary
        else:
            inline_summary_list = self.root.collectors.get('sum', [])
            if inline_summary_list:
                return ''.join(inline_summary_list)
        return ''

    @property
    def taxonomies(self):
        return self.meta.get('taxonomy', {})

    @property
    def title(self):
        return self.meta.get('title', '')

    @property
    def description(self):
        return self.meta.get('description', '')

    @property
    def slug(self):
        return self.meta['slug']

    def get_taxonomy_group(self, top_level_taxonomy):
        #TODO maybe cache this in indentgen so we're not having to re-filter these over and over for every hit
        filter_page_taxonomies = [k for k,v in self.indentgen.taxonomy_map.items() if v['top_level'] == top_level_taxonomy]
        taxonomies_for_page =  set(filter_page_taxonomies).intersection(self.taxonomies)
        return PageStore([self.indentgen.taxonomy_map[slug]['endpoint'] for slug in taxonomies_for_page])

    def next_page(self):
        return None # this class does not have paginated pages, so this method should never be called


class TaxonomyEndpoint(ContentEndpoint):
    use_template = 'pages/taxonomy.html'
    is_taxonomy = True

    @property
    def breadcrumbs(self):
        path_titles = []
        focused = self.indentgen.taxonomy_map[self.slug]
        while 'parent' in focused:
            focused = self.indentgen.taxonomy_map[focused['parent']]
            path_titles.append({'title': focused['title'], 'url': focused['endpoint'].url})
        path_titles.reverse()
        return path_titles

    def next_page(self):
        return TaxonomyEndpoint(self.indentgen, self.url_components, self.page + 1, self.srp)


class RedirectEndpoint(Endpoint):
    use_template = 'pages/redirect.html'
    is_redirect = True

    def __init__(self, indentgen_obj, from_url_components, to_endpoint):
        super().__init__(indentgen_obj, from_url_components, None)
        self.to_endpoint = to_endpoint

    @property
    def identifier(self):
        return self.to_endpoint.identifier

    def next_page(self):
        return None # this class does not have paginated pages, so this method should never be called


class StaticServeEndpoint(Endpoint):
    use_template = None

    def __init__(self, indentgen_obj, url_components):
        super().__init__(indentgen_obj, url_components, None)

    def render(self, indentgen_obj):
        return None

    def next_page(self):
        return None # this class does not have paginated pages, so this method should never be called


class CachedImgEndpoint(StaticServeEndpoint):
    pass # use a different class in case we ever need to extend this differently


class DateArchiveEndpoint(Endpoint):
    use_template = 'pages/date_archive.html'

    @property
    def title(self):
        if len(self.url_components) == 1:
            return 'Date Archive'
        year = self.url_components[1]
        month = self.url_components[2] if len(self.url_components) == 3 else ''
        if month:
            month = month_name[int(month)]
        return f'{month} {year}'.strip()

    @property
    def meta(self):
        return {}

    @property
    def summary(self):
        return ''

    @property
    def breadcrumbs(self):
        if len(self.url_components) == 1:
            return []
        archive_url = f"/{self.indentgen.config['date_archive_url']}/"
        path_titles = [{'title': 'Date Archive', 'url': archive_url }]
        if len(self.url_components) == 3:
            path_titles.append({'title': self.url_components[1], 'url': f'{archive_url}{self.url_components[1]}/'})
        return path_titles
