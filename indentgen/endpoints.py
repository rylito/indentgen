import math
from pathlib import Path

PAGE_URL = 'page' #TODO make this configurable in site settings?

class Endpoint:
    use_template = 'pages/home.html'
    #has_content = False
    srp = None
    #is_static = False
    #is_home = True
    is_taxonomy = False
    is_redirect = False
    #is_static = False

    def __init__(self, indentgen_obj, url_components, page=None):
        self.url_components = url_components
        self.page = page
        self.indentgen = indentgen_obj

    def get_output_path(self):
        #if not self.url_components:
            #return
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
        print('RENDERING', self.srp, self.url_components, self)
        #rendered, root = indentgen_obj.wisdom.get_rendered(self.srp, self.is_taxonomy)

        context = {
            #'static_url': indentgen_obj.static_url,
            #'taxonomies': indentgen_obj.taxonomy_map,
            #'content': rendered,
            #'content_root': root,
            #'site_config': indentgen_obj.config,
            #'page_store': indentgen_obj.page_store,
            #'url': self.url
            'page': self,
        }

        template = indentgen_obj.templates.get_template(self.use_template)
        return template.render(**context)

    #def generate(self, template_mgr, site_config, static_func, taxonomy, wisdom):
        #rendered, root = wisdom.get_rendered(self.srp, self.i_taxonomy)
        #template = template_mgr.get_template(self.use_template)
        #context = {
            #'site_config': site_config,
            #'static_url': static_func,
            #'taxonomy': taxonomy,
            #'body': rendered,
            #'root': root,
            #'meta': root.context['meta'], #TODO shortcut, is this necessary?
            #'page': page,
        #}
        #return template.render(**context)

    def next_page(self):
        return Endpoint(self.indentgen, self.url_components, self.page + 1)






#class SrpEndpoint(Endpoint):
    #def __init__(self, url_components, srp):
        #super().__init(url_components)
        #self.srp = srp

    #def generate(self, template_mgr, context):
        #template = template_mgr.get_template(self.use_template)
        #return template.render(**context)


class ContentEndpoint(Endpoint):
    use_template = 'pages/content.html'
    #has_content = True
    #is_home = False

    def __init__(self, indentgen_obj, url_components, page, srp):
        super().__init__(indentgen_obj, url_components, page)
        #self.url_components = url_components
        #self.indentgen = indentgen_obj
        self.srp = srp
        self.prev = None
        self.next = None
        #self.meta = meta
        #self.taxonomies = taxonomies

    #TODO perhaps optimize this so it doesn't read from cached wisdom .html files if only fetching root
    def get_rendered(self):
        # returns (rendered, root)
        return self.indentgen.wisdom.get_rendered(self.srp, self.is_taxonomy)

    @property
    def root(self):
        return self.get_rendered()[1]

    @property
    def content(self):
        return self.get_rendered()[0]

    #@property
    #def collectors(self):
        #return self.root.collectors

    @property
    def meta(self):
        return self.root.context['meta']

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
        return self.meta['title']

    @property
    def slug(self):
        return self.meta['slug']

    def get_taxonomy_group(self, top_level_taxonomy):
        #TODO maybe cache this in indentgen so we're not having to re-filter these over and over for every hit
        filter_page_taxonomies = [k for k,v in self.indentgen.taxonomy_map.items() if v['top_level'] == top_level_taxonomy]
        taxonomies_for_page =  set(filter_page_taxonomies).intersection(self.taxonomies)
        return [self.indentgen.taxonomy_map[slug]['endpoint'] for slug in taxonomies_for_page]

    def next_page(self):
        return None # this class does not have paginated pages, so this method should never be called



    #@property
    #def meta(self):
        #return indentgen_obj.wisdom.get_rendered(self.srp, self.is_taxonomy)[1]['meta']

    #def get_taxonomies_by_top_level(self, tax_slug):
        #for

    #def render(self):
        #rendered, root = self.get_rendered()

        #context = {
            #'static_url': indentgen_obj.static_url,
            #'taxonomies': indentgen_obj.taxonomy_map,
            #'content': rendered,
            #'content_root': root,
            #'site_config': indentgen_obj.config,
            #'page_store': indentgen_obj.page_store,
            #'page': self,
            #'url': self.url
        #}

        #template = indentgen_obj.templates.get_template(self.use_template)
        #return template.render(**context)

        #return wisdom.get_rendered(self.srp, self.is_taxonomy)

    #def generate(self, template_mgr, site_config, static_func, taxonomy, wisdom):
        #rendered, root = wisdom.get_rendered(self.srp, self.i_taxonomy)
        #template = template_mgr.get_template(self.use_template)
        #context = {
            #'site_config': site_config,
            #'static_url': static_func,
            #'taxonomy': taxonomy,
            #'body': rendered,
            #'root': root,
            #'meta': root.context['meta'], #TODO shortcut, is this necessary?
            #'page': page,
        #}
        #return template.render(**context)


class TaxonomyEndpoint(ContentEndpoint):
    use_template = 'pages/taxonomy.html'
    is_taxonomy = True


    #def __init__(self, url_components, srp, page):
        #super().__init(url_components, srp)
        #self.page = page

    #def prev_page(self):
        #if self.page > 0:
            #return TaxonomyEndpoint(self.url_components, self.page - 1, self.srp, self.taxonomies)
        #return None

    #def top_level(self):
        #return 

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



#class PaginatedEndpoint(ContentEndpoin):

class RedirectEndpoint(Endpoint):
    use_template = 'pages/redirect.html'
    #has_content = False
    #is_home = False
    is_redirect = True

    def __init__(self, indentgen_obj, from_url_components, to_endpoint):
        super().__init__(indentgen_obj, from_url_components, None)
        self.to_endpoint = to_endpoint

    @property
    def identifier(self):
        return self.to_endpoint.identifier

    def next_page(self):
        return None # this class does not have paginated pages, so this method should never be called




    #def render(self, indentgen_obj):
        #context = {
            #'static_url': indentgen_obj.static_url,
            #'taxonomies': indentgen_obj.taxonomy_map,
            #'content': rendered,
            #'content_root': rendered,
            #'site_config': indentgen_obj.config,
            #'page': self
        #}

        #template = indentgen_obj.templates.get_template(self.use_template)
        #return template.render(**context)


class StaticServeEndpoint(Endpoint):
    use_template = None
    #is_static = True
    #is_home = False

    def __init__(self, indentgen_obj, url_components):
        super().__init__(indentgen_obj, url_components, None)
        #self.actual_path = actual_path

    def render(self, indentgen_obj):
        return None

    def next_page(self):
        return None # this class does not have paginated pages, so this method should never be called


class CachedImgEndpoint(StaticServeEndpoint):
    pass # use a different class in case we ever need to extend this differently

    #use_template = None
    #is_static = True
    #is_home = False

    #def __init__(self, indentgen_obj, url_components, actual_path):
        #super().__init__(indentgen_obj, url_components, None)
        #self.actual_path = actual_path

    #def render(self, indentgen_obj):
        #return None

    #def next_page(self):
        #return None # this class does not have paginated pages, so this method should never be called






'''
topic:
{'title': 'Topics', 'slug': 'topics', 'srp': PosixPath('taxonomy/tags/topics.dentmark'), 'url_components': ['topics'], 'children': ['politics', 'aviation']}

{'topics': {'title': 'Topics', 'slug': 'topics', 'srp': PosixPath('taxonomy/tags/topics.dentmark'), 'url_components': ['topics'], 'children': ['politics', 'aviation']}, 'politics': {'parent': 'topics', 'title': 'Politics', 'slug': 'politics', 'srp': PosixPath('taxonomy/tags/politics.dentmark'), 'url_components': ['topics', 'politics'], 'pages': ['first-thought']}, 'aviation': {'parent': 'topics', 'title': 'Aviation', 'slug': 'aviation', 'srp': PosixPath('taxonomy/tags/aviation.dentmark'), 'url_components': ['topics', 'aviation']}}

content:
{'pk': '4', 'title': 'First Thought', 'slug': 'first-thought', 'taxonomy': ['politics'], 'srp': PosixPath('content/thoughts/thought_1.dentmark')}

{'first-thought': {'pk': '4', 'title': 'First Thought', 'slug': 'first-thought', 'taxonomy': ['politics'], 'srp': PosixPath('content/thoughts/thought_1.dentmark')}, 'third-thought': {'pk': '6', 'title': 'Third Thought', 'slug': 'third-thought', 'srp': PosixPath('content/thoughts/thought_3.dentmark')}, 'second-thought': {'pk': '5', 'title': 'Second Thought', 'slug': 'second-thought', 'srp': PosixPath('content/thoughts/thought_2.dentmark')}, 'first-article': {'pk': '1', 'title': 'First Article', 'slug': 'first-article', 'srp': PosixPath('content/articles/article_1.dentmark')}, 'second-article': {'pk': '2', 'title': 'Second Article', 'slug': 'second-article', 'srp': PosixPath('content/articles/article_2.dentmark')}, 'third-article': {'pk': '3', 'title': 'Third Article', 'slug': 'third-article', 'srp': PosixPath('content/articles/article_3.dentmark')}}
'''
