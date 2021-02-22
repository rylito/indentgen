import math
from pathlib import Path

PAGE_URL = 'page' #TODO make this configurable in site settings?

class Endpoint:
    use_template = 'home.html'
    #has_content = False
    srp = None
    #is_static = False

    def __init__(self, url_components, page=None):
        self.url_components = url_components
        self.page = page

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
        url = '/'.join(self.url_components)
        if self.page is not None and self.page > 0:
            url += f'/{PAGE_URL}/{self.page + 1}'
        return f'/{url}/'

    @property
    def identifier(self):
        return self.srp if self.srp is not None else self.url

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



#class SrpEndpoint(Endpoint):
    #def __init__(self, url_components, srp):
        #super().__init(url_components)
        #self.srp = srp

    #def generate(self, template_mgr, context):
        #template = template_mgr.get_template(self.use_template)
        #return template.render(**context)


class ContentEndpoint(Endpoint):
    use_template = 'content.html'
    #has_content = True
    is_taxonomy = False

    def __init__(self, url_components, page, srp, taxonomies=[]):
        super().__init__(url_components, page)
        #self.url_components = url_components
        self.srp = srp
        self.taxonomies = taxonomies

    def render(self, indentgen_obj):
        rendered, root = indentgen_obj.wisdom.get_rendered(self.srp, self.is_taxonomy)

        context = {
            'static_url': indentgen_obj.static_url,
            'taxonomies': indentgen_obj.taxonomy_map,
            'content': rendered,
            'content_root': root,
            'site_config': indentgen_obj.config,
            'page': self
        }

        template = indentgen_obj.templates.get_template(self.use_template)
        return template.render(**context)

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
    use_template = 'taxonomy.html'
    is_taxonomy = True


    #def __init__(self, url_components, srp, page):
        #super().__init(url_components, srp)
        #self.page = page

    #def prev_page(self):
        #if self.page > 0:
            #return TaxonomyEndpoint(self.url_components, self.page - 1, self.srp, self.taxonomies)
        #return None

    def next_page(self):
        return TaxonomyEndpoint(self.url_components, self.page + 1, self.srp, self.taxonomies)


#class PaginatedEndpoint(ContentEndpoin):

class RedirectEndpoint(Endpoint):
    use_template = 'redirect.html'
    #has_content = False

    def __init__(self, from_url_components, to_endpoint):
        super().__init__(from_url_components, None)
        self.to_endpoint = to_endpoint

    @property
    def identifier(self):
        return self.to_endpoint.identifier


    def render(self, indentgen_obj):
        context = {
            #'static_url': indentgen_obj.static_url,
            #'taxonomies': indentgen_obj.taxonomy_map,
            #'content': rendered,
            #'content_root': rendered,
            'site_config': indentgen_obj.config,
            'page': self
        }

        template = indentgen_obj.templates.get_template(self.use_template)
        return template.render(**context)


class StaticServeEndpoint(Endpoint):
    use_template = None
    #is_static = True

    def __init__(self, url_components, actual_path):
        super().__init__(url_components, None)
        self.actual_path = actual_path

    def render(self, indentgen_obj):
        return None


class Paginator:

    class Page:
        def __init__(self, paginator, page_num_0, start_index, end_index, prev_endpoint, next_endpoint):
            self.paginator = paginator
            self.items = paginator.items[start_index:end_index]
            self.page_num_0 = page_num_0
            self.start_index = start_index
            self.end_index = end_index
            self.prev_endpoint = prev_endpoint
            self.next_endpoint = next_endpoint

            #self.page_total = (end_index_inclusive_0 - start_index_inclusive_0) + 1
            self.num_items_on_page = len(self.items)

    def __init__(self, child_items, per_page):
        self.items = child_items
        self.per_page = per_page
        self.total = len(child_items)
        self.num_of_pages = math.ceil(self.total / per_page)

    def attach_page(self, list_endpoint, prev_endpoint): # 0 based page index read off of list_endpoint_obj
        page_num = list_endpoint.page
        start_index = page_num * self.per_page
        end_index = start_index + self.per_page
        if end_index > self.total:
            end_index = self.total

        #prev_endpoint = list_endpoint.prev_page()
        next_endpoint = list_endpoint.next_page() if (page_num + 1) < self.num_of_pages else None

        #return Page(self, page_num, start_index, end_index, prev_endpoint, next_endpoint)
        list_endpoint.paginator_page = self.Page(self, page_num, start_index, end_index, prev_endpoint, next_endpoint)
        return list_endpoint

    def gen_all_pages(self, list_endpoint_0):
        prev_endpoint = None
        annotated_endpoint = self.attach_page(list_endpoint_0, prev_endpoint)
        yield annotated_endpoint

        while annotated_endpoint.paginator_page.next_endpoint is not None:
            prev_endpoint = annotated_endpoint
            next_endpoint = annotated_endpoint.paginator_page.next_endpoint
            annotated_endpoint = self.attach_page(next_endpoint, prev_endpoint)
            yield annotated_endpoint


'''
topic:
{'title': 'Topics', 'slug': 'topics', 'srp': PosixPath('taxonomy/tags/topics.dentmark'), 'url_components': ['topics'], 'children': ['politics', 'aviation']}

{'topics': {'title': 'Topics', 'slug': 'topics', 'srp': PosixPath('taxonomy/tags/topics.dentmark'), 'url_components': ['topics'], 'children': ['politics', 'aviation']}, 'politics': {'parent': 'topics', 'title': 'Politics', 'slug': 'politics', 'srp': PosixPath('taxonomy/tags/politics.dentmark'), 'url_components': ['topics', 'politics'], 'pages': ['first-thought']}, 'aviation': {'parent': 'topics', 'title': 'Aviation', 'slug': 'aviation', 'srp': PosixPath('taxonomy/tags/aviation.dentmark'), 'url_components': ['topics', 'aviation']}}

content:
{'pk': '4', 'title': 'First Thought', 'slug': 'first-thought', 'taxonomy': ['politics'], 'srp': PosixPath('content/thoughts/thought_1.dentmark')}

{'first-thought': {'pk': '4', 'title': 'First Thought', 'slug': 'first-thought', 'taxonomy': ['politics'], 'srp': PosixPath('content/thoughts/thought_1.dentmark')}, 'third-thought': {'pk': '6', 'title': 'Third Thought', 'slug': 'third-thought', 'srp': PosixPath('content/thoughts/thought_3.dentmark')}, 'second-thought': {'pk': '5', 'title': 'Second Thought', 'slug': 'second-thought', 'srp': PosixPath('content/thoughts/thought_2.dentmark')}, 'first-article': {'pk': '1', 'title': 'First Article', 'slug': 'first-article', 'srp': PosixPath('content/articles/article_1.dentmark')}, 'second-article': {'pk': '2', 'title': 'Second Article', 'slug': 'second-article', 'srp': PosixPath('content/articles/article_2.dentmark')}, 'third-article': {'pk': '3', 'title': 'Third Article', 'slug': 'third-article', 'srp': PosixPath('content/articles/article_3.dentmark')}}
'''
