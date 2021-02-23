#TODO make sure urls don't clobber 'static' and other reserved URLS

import sys
import shutil
import importlib
#import pkgutil
#import pickle
#import math
from pathlib import Path
from indentgen.default_definitions import *
from indentgen.wisdom import Wisdom
from dentmark import Dentmark
from mako.template import Template
from mako.lookup import TemplateLookup
from indentgen.endpoints import PAGE_URL, Endpoint, ContentEndpoint, TaxonomyEndpoint, RedirectEndpoint, StaticServeEndpoint, Paginator
from indentgen.page_store import PageStore
#from development_server import DevelopmentServer
import indentgen.default_definitions


class Indentgen:
    WISDOM_DIR = '_wisdom'
    CONTENT_DIR = 'content'
    TAXONOMY_DIR = 'taxonomy'
    #DEFAULT_DEFS_MODULE_NAME = 'indentgen.default_definitions'
    CUSTOM_DEFS_MODULE_NAME = 'indentgen_defs'
    CONFIG_FILE_NAME = 'config.dentmark'
    THEME_DIR = 'theme'
    TEMPLATE_DIR = Path(THEME_DIR) / 'templates'
    TEMPLATE_CACHE_DIR = Path(WISDOM_DIR) / 'mako_modules'
    STATIC_DIR = Path(THEME_DIR) / 'static'

    #TODO puth these in config.dentmark instead?
    OUTPUT_DIR = 'publish'
    STATIC_URL = '_static'
    CACHE_BUST_STATIC_EXTENSIONS = ('.css', '.js') #TODO put this in config.dentmark instead?

    DEFAULT_PER_PAGE = 25

    def __init__(self, site_path):
        self.site_path = Path(site_path)
        print(self.site_path)

        sys.path.append(str(self.site_path))
        print(sys.path)

        #self.defs_module_name = defs_module_name
        #self.available_definitions = self._find_defs()
        #self.dentmark = Dentmark('dentmark_defs')

        #print(self.available_definitions)
        try:
            self.defs_module = importlib.import_module(self.CUSTOM_DEFS_MODULE_NAME)
        except ModuleNotFoundError:
            #self.defs_module = importlib.import_module(self.DEFAULT_DEFS_MODULE_NAME)
            self.defs_module = indentgen.default_definitions
        #print(defs_module.REGISTERED_TAGS)
        #self.dentmark = Dentmark(defs_module.REGISTERED_TAGS)

        self._load_config()

        self.content_path = self.site_path / self.CONTENT_DIR
        self.taxonomy_path = self.site_path / self.TAXONOMY_DIR
        self.wisdom_path = self.site_path / self.WISDOM_DIR

        self.static_path = self.site_path / self.STATIC_DIR
        self.output_path = self.site_path / self.OUTPUT_DIR
        self.static_output_path = self.output_path / self.STATIC_URL

        self.wisdom = Wisdom(self.site_path, self.wisdom_path, self.content_path, self.taxonomy_path, self.static_path, self.defs_module)

        #{('url_component', 'url_component', ...): Endpoint}
        self.routes = {}
        self._add_route(Endpoint([])) # add home page
        #print(self.routes)
        #print(Endpoint([]).get_output_path())
        #input('hold')

        self._build_taxonomy_map()
        self._build_page_store()
        #self._add_pages_to_taxonomy_map()
        self._generate_pagination_routes()

        self._build_static_file_remapping()

        template_dir = self.site_path / self.TEMPLATE_DIR
        template_cache_dir = self.site_path / self.TEMPLATE_CACHE_DIR
        self.templates = TemplateLookup(directories=[template_dir], module_directory=template_cache_dir)


    def _load_config(self):
        dentmark_instance = Dentmark(self.defs_module.CONFIG_TAGS)
        config_file_path = self.site_path / self.CONFIG_FILE_NAME

        with open(config_file_path, 'r') as f:
            self.config = dentmark_instance.render(f)
            print(self.config)

    #def get_site_relative_path(self, path):
        #return path.relative_to(self.site_path)

    #def get_rendered(self):
        #aoeu

    def _gen_walk_content(self, is_taxonomy=False):
        #content_path = self.site_path.joinpath(self.CONTENT_DIR)
        use_path = self.taxonomy_path if is_taxonomy else self.content_path
        print('Globbing:', use_path)
        for f in use_path.glob('**/*.dentmark'):
            print(f)
            srp = f.relative_to(self.site_path)
            print('srp:', srp)

            rendered, meta = self.wisdom.get_rendered(srp, is_taxonomy)
            yield srp, rendered, meta


    def _add_route(self, endpoint):
        collision_endpoint = self.routes.get(endpoint.url)
        if collision_endpoint is not None:
            #this_name = endpoint.url if not endpoint.has_content else endpoint.srp
            #other_name = collision_endpoint.url if not collision_endpoint.has_content else collision_endpoint.srp
            raise Exception(f"URL conflict for '{endpoint.url}': {endpoint.identifier} and {collision_endpoint.identifier}")
        self.routes[endpoint.url] = endpoint


    # {tax_slug: {}, tax_slug: {meta.., children: []}}
    def _build_taxonomy_map(self):
        #srp_map = {}
        tax_map = {}
        top_level_taxonomies = []
        #taxonomy_urls = {}

        for srp, rendered, root in self._gen_walk_content(is_taxonomy=True):
            meta = root.context['meta']
            slug = meta['slug']
            collision = tax_map.get(slug)
            if collision:
                raise Exception(f"Taxonomy slugs conflict: {srp} and {collision['srp']}")
            #meta_copy = meta.copy() # use a copy to not contaminate the _wisdom
            #meta_copy['srp'] = srp
            #meta = root.context['meta']
            #tax_map[meta['slug']] = meta_copy
            #srp_map[slug] = {'parent'}

            tax_map[slug] = {'slug': slug, 'srp': srp}

            if 'parent' not in meta:
                top_level_taxonomies.append(slug)
            else:
                tax_map[slug]['parent'] = meta['parent']

        for slug, info in tax_map.items():
            #meta = info['meta']
            #tax_map_dict = {'srp': info['srp'], 'slug': meta['slug']}
            parent_slug = info.get('parent')
            if parent_slug:
                #tax_map_dict['parent'] = parent_slug
                try:
                    #parent_tax = tax_map[parent_slug]
                    children = tax_map[parent_slug].setdefault('children', [])
                except KeyError:
                    raise Exception(f"{info['srp']}: meta parent value does not exist for '{parent_slug}'")
                #children = parent_meta.setdefault('children', [])
                children.append(slug)
                print(tax_map)
                #input('HOLD HERE')
            #tax_map[slug] = tax_map_dict

            #endpoint_obj = TaxonomyEndpoint(url_components)

            #def __init__(self, url_components, page, srp):

            #taxonomy_urls[tuple(url_components)] = meta['srp']
            #print(url_components)

            #meta['url_components'] = url_components

        print(tax_map)
        #input('HOLD tax map')
        print(top_level_taxonomies)
        #print(taxonomy_urls)

        self.taxonomy_map = tax_map
        self.top_level_taxonomies = top_level_taxonomies
        #self.taxonomy_urls = taxonomy_urls
        #input('HOLD')


    def _build_page_store(self):
        page_store = PageStore()
        #page_urls = {}
        for srp, rendered, root in self._gen_walk_content(is_taxonomy=False):
            meta = root.context['meta']

            # make sure taxonomies are valid
            taxonomy = meta.get('taxonomy', [])
            if taxonomy:
                for tax in taxonomy:
                    try:
                        tax_meta = self.taxonomy_map[tax]
                    except KeyError:
                        raise Exception(f"{srp} contains invalid taxonomy slug: {tax}")


            #TODO make this configurable in setting whether to use pk shortcuts or not
            pk = meta.get('pk')
            slug = meta['slug']

            url_components = (f'{pk}-{slug}',) if pk is not None else (slug,)

            #0 is for 0th page, these won't have mulitple pages
            endpoint = ContentEndpoint(url_components, None, srp, taxonomy)

            #page_list.append(endpoint)
            page_store.add(endpoint)

            self._add_route(endpoint)

            if pk is not None:
                redirect_endpoint = RedirectEndpoint((pk,), endpoint)
                self._add_route(redirect_endpoint)

        self.page_store = page_store

        print(self.page_store.pages)
        #input('HOLD')
        print(self.routes)
        #input('HOLD')


    def _generate_pagination_routes(self):
        per_page = self.config.get('per_page', self.DEFAULT_PER_PAGE)

        for slug, info in self.taxonomy_map.items():
            url_components = [info['slug']]
            focused = info
            while 'parent' in focused:
                focused = self.taxonomy_map[focused['parent']]
                url_components.append(focused['slug'])
            url_components.reverse()
            print(url_components)
            #input('HOLD URL COMP')


            child_pages = self.page_store.filter_by_topic(slug)
            pag = Paginator(child_pages, per_page)

            endpoint_0 = TaxonomyEndpoint(url_components, 0, info['srp']) # topic/, topic/page/2, topic/page/3 etc.

            # add this to taxonomy map
            info['endpoint'] = endpoint_0

            # clean this out of taxonomy map since it is stored on endpoint obj
            del info['srp']

            base_redirect = RedirectEndpoint(url_components + [PAGE_URL] + ['1'], endpoint_0) # topic/page/1 -> topic/
            self._add_route(base_redirect)

            page_redirect = RedirectEndpoint(url_components + [PAGE_URL], endpoint_0) # topic/page -> topic/page/1
            self._add_route(page_redirect)

            for endpoint in pag.gen_all_pages(endpoint_0):
                self._add_route(endpoint)

            print(self.routes)
            #input('HOLD pagination gen thing')

            #content_count = self.page_store.count_by_topic(slug)
            #print(slug, page_count)
            #input('HOLD PAGE COUNT')

            #num_pages = math.ceil(content_count / per_page)

            #for
        print(self.taxonomy_map)
        #input('HOLD')


    def _build_static_file_remapping(self):
        # {}
        static_file_mapping = {}

        for f in self.static_path.glob('**/*.*'):
            #print(f)

            srp = f.relative_to(self.static_path)

            if f.suffix in self.CACHE_BUST_STATIC_EXTENSIONS:
                print('srp:', srp)
                use_srp = self.wisdom.get_static_file_name(srp)
                print(use_srp)
            else:
                use_srp = srp

            move_to = self.static_output_path / use_srp
            print(move_to)
            static_file_mapping[srp] = {'from': f, 'to': move_to, 'srp': use_srp}

            components = [self.STATIC_URL] + list(use_srp.parts)
            endpoint = StaticServeEndpoint(components, f)
            self._add_route(endpoint)
            #print('srp:', srp)
            #print('moveto:', move_to)

            #rendered, meta = self.wisdom.get_rendered(srp, is_taxonomy)
            #yield srp, rendered, meta
        self.static_file_mapping = static_file_mapping
        print(static_file_mapping)
        #input('HOLD static file mapping')


    def static_url(self, srp):
        use_srp = self.static_file_mapping[Path(srp)]['srp']
        return f'/{self.STATIC_URL}/{use_srp}'


    def _copy_static(self):
        for meta in self.static_file_mapping.values():
            meta['to'].parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(meta['from'], meta['to'])

    #def _clear_output_dir(self):
        #shutil.rmtree(site.path / self.OUTPUT_DIR)

    def generate(self):
        # index.html
        #template = self.templates.get_template('base.html')
        #print(template.render(config=self.config, static_url=self.static_url))
        #self._copy_static()

        # remove old/stale published content
        shutil.rmtree(self.output_path, ignore_errors=True) # if dir doesn't exist, ignore error

        for endpoint in self.routes.values():
            #if endpoint.is_static:
                #continue

            #rendered = f'bogus_render for {endpoint.url}'

            rendered = endpoint.render(self)
            if rendered is None:
                continue

            output_path = self.output_path / endpoint.get_output_path()

            output_path.mkdir(parents=True, exist_ok=True)
            print(output_path)
            with open(output_path / 'index.html', 'w') as f:
                f.write(rendered)

        self._copy_static()


    #def get_server(self):
        #return DevelopmentServer(self.routes)
        #return DevelopmentServer
