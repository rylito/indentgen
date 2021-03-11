#TODO make sure urls don't clobber 'static' and other reserved URLS
#TODO enforce that series must have part #s

import sys
import shutil
import importlib
#import pkgutil
#import pickle
#import math
from pathlib import Path

#from indentgen.default_definitions import *

from indentgen.wisdom import Wisdom

#from dentmark import render

import dentmark
#from indentgen.default_definitions import CONTENT_TAG_SET
from indentgen.default_definitions.content_tag_defs import CONTENT_TAG_SET #, TaxonomyItemTagDef
from indentgen.default_definitions.taxonomy_tag_defs import TAXONOMY_TAG_SET
from indentgen.taxonomy_def_set import TaxonomyDefSetContent, TaxonomyDefSetTaxonomy
#from indentgen.taxonomy_tag_def import TaxonomyTagDef, TaxonomyItemTagDef

from mako.template import Template
from mako.lookup import TemplateLookup
from indentgen.endpoints import PAGE_URL, Endpoint, ContentEndpoint, TaxonomyEndpoint, RedirectEndpoint, StaticServeEndpoint, CachedImgEndpoint
from indentgen.paginator import Paginator
from indentgen.page_store import PageStore
#from development_server import DevelopmentServer
#import indentgen.default_definitions



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

    IMAGE_URL = '_img'

    DEFAULT_PER_PAGE = 25

    def __init__(self, site_path):
        self.site_path = Path(site_path)
        print(self.site_path)

        sys.path.append(str(self.site_path))
        print(sys.path)

        #self.


        #self.defs_module_name = defs_module_name
        #self.available_definitions = self._find_defs()
        #self.dentmark = Dentmark('dentmark_defs')

        #print(self.available_definitions)
        try:
            self.defs_module = importlib.import_module(self.CUSTOM_DEFS_MODULE_NAME)
        except ModuleNotFoundError:
            print('No custom definitions found') #TODO better error or warning here?
            ##self.defs_module = importlib.import_module(self.DEFAULT_DEFS_MODULE_NAME)
            #self.defs_module = indentgen.default_definitions
        #print(defs_module.REGISTERED_TAGS)
        #self.dentmark = Dentmark(defs_module.REGISTERED_TAGS)

        #self._load_config()


        self.content_path = self.site_path / self.CONTENT_DIR
        self.taxonomy_path = self.site_path / self.TAXONOMY_DIR
        self.wisdom_path = self.site_path / self.WISDOM_DIR

        self.static_path = self.site_path / self.STATIC_DIR
        self.output_path = self.site_path / self.OUTPUT_DIR
        self.static_output_path = self.output_path / self.STATIC_URL

        self.img_output_path = self.output_path / self.IMAGE_URL

        self.config_file_path = self.site_path / self.CONFIG_FILE_NAME

        self.wisdom = Wisdom(self.site_path, self.wisdom_path, self.content_path, self.taxonomy_path, self.static_path, self.IMAGE_URL, self.img_output_path, self.config_file_path)
        self.config = self.wisdom.get_config()

        #{('url_component', 'url_component', ...): Endpoint}
        self.routes = {}
        #self._add_route(Endpoint(self, [])) # add home page
        #print(self.routes)
        #print(Endpoint([]).get_output_path())
        #input('hold')

        self._patch_def_sets()

        self._build_taxonomy_map()
        self._check_taxonomy_tags_meta(is_taxonomy=True)

        #self._build_taxonomy_tags()
        self._build_page_store()
        self._check_taxonomy_tags_meta(is_taxonomy=False)

        #self._build_taxonomy_page_store()
        #self._add_taxonomy_to_page_store()

        #self._add_pages_to_taxonomy_map()
        self._generate_taxonomy_pagination_routes()
        self._generate_home_pagination_routes()

        self._build_static_file_remapping()
        self._build_resized_img_endpoints()

        template_dir = self.site_path / self.TEMPLATE_DIR
        template_cache_dir = self.site_path / self.TEMPLATE_CACHE_DIR
        self.templates = TemplateLookup(directories=[template_dir], module_directory=template_cache_dir)


    #def _load_config(self):
        #dentmark_instance = Dentmark(self.defs_module.CONFIG_TAGS)
        #config_file_path = self.site_path / self.CONFIG_FILE_NAME

        #with open(config_file_path, 'r') as f:
            #self.config = dentmark_instance.render(f)
            #print(self.config)

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


    def _patch_def_sets(self):
        content_tag_set = dentmark.defs_manager.get_tag_set(CONTENT_TAG_SET)
        taxonomy_tag_set = dentmark.defs_manager.get_tag_set(TAXONOMY_TAG_SET)

        # Monkey patch this to use the extended class to defer resolving tag names
        # Kinda hacky, but it works

        for tag_set, patch_def_set  in ((content_tag_set, TaxonomyDefSetContent), (taxonomy_tag_set, TaxonomyDefSetTaxonomy)):
            new_def_set = patch_def_set.copy_from_def_set(tag_set)
            dentmark.defs_manager.def_sets[tag_set.tag_set_name] = new_def_set



    # {tax_slug: {}, tax_slug: {meta.., children: []}}
    def _build_taxonomy_map(self):
        #srp_map = {}
        tax_map = {}
        top_level_taxonomies = []
        #taxonomy_urls = {}

        for srp, rendered, root in self._gen_walk_content(is_taxonomy=True):
            meta = root.context['meta']

            #print(meta)
            #input('HOLD')

            slug = meta['slug']
            collision = tax_map.get(slug)
            if collision:
                raise Exception(f"Taxonomy slugs conflict: {srp} and {collision['srp']}")
            #meta_copy = meta.copy() # use a copy to not contaminate the _wisdom
            #meta_copy['srp'] = srp
            #meta = root.context['meta']
            #tax_map[meta['slug']] = meta_copy
            #srp_map[slug] = {'parent'}

            tax_map[slug] = {'slug': slug, 'srp': srp, 'title': meta['title']}
            tax_map[slug]['pseudo'] = meta['pseudo'] if 'pseudo' in meta else False

            if 'taxonomy' in meta:
                tax_map[slug]['taxonomy'] = meta['taxonomy']

                parent = None

                for tax_slug, (order, is_parent) in meta['taxonomy'].items():
                    if tax_slug == slug:
                        raise Exception(f"{srp}: Cannot list self as a taxonomy: '{tax_slug}'")

                    if is_parent:
                        if parent:
                            raise Exception(f"{srp}: Cannot have more than 1 taxonomy marked as parent")
                        parent = tax_slug

                if len(meta['taxonomy']) > 1 and not parent:
                    raise Exception(f"{srp}: A taxonomy must be marked as the parent since there is more than one listed")
                elif len(meta['taxonomy']) == 1:
                    parent = tax_slug

                if parent:
                    tax_map[slug]['parent'] = parent

            #print(tax_map)
            #input('TAX MAP HOLD')

            #TODO enforce that pseudo taxonomies cannot have children?

            if 'parent' not in tax_map[slug]:
                top_level_taxonomies.append(slug)

            #else:
                #tax_map[slug]['parent'] = meta['parent']


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
                    raise Exception(f"{info['srp']}: invalid parent taxonomy: '{parent_slug}'")
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


            url_components = [info['slug']]
            focused = info
            while 'parent' in focused:
                focused = tax_map[focused['parent']]
                url_components.append(focused['slug'])
            url_components.reverse()
            print(url_components)

            info['top_level'] = url_components[0]

            taxonomies = info.get('taxonomy', [])
            srp = info['srp']
            del info['srp']

            endpoint_0 = TaxonomyEndpoint(self, url_components, 0, srp)

            # add this to taxonomy map
            info['endpoint'] = endpoint_0




        print(tax_map)
        #input('HOLD tax map')
        print(top_level_taxonomies)
        #print(taxonomy_urls)
        #input('HOLD')

        self.taxonomy_map = tax_map
        self.top_level_taxonomies = top_level_taxonomies
        #self.taxonomy_urls = taxonomy_urls
        #input('HOLD')


    def _check_taxonomy_tags_meta(self, is_taxonomy):
        for srp, rendered, root in self._gen_walk_content(is_taxonomy):
            meta = root.context['meta']
            taxonomy = meta.get('taxonomy')
            if taxonomy is not None:
                invalid = set(taxonomy).difference(self.taxonomy_map)
                if invalid:
                    raise Exception(f"Invalid taxonomy tag(s) {invalid} in meta: {srp}")
                print(invalid)
                #input('HOLD')





    def _build_page_store(self):
        page_store = PageStore()
        non_pk_page_store = PageStore()
        #page_urls = {}
        for srp, rendered, root in self._gen_walk_content(is_taxonomy=False):
            meta = root.context['meta']

            # make sure taxonomies are valid
            #taxonomy = meta.get('taxonomy', [])
            print('meta', meta)
            #input('HOLD')
            #if taxonomy:
                #for tax in taxonomy:
                    #try:
                        #tax_meta = self.taxonomy_map[tax]
                    #except KeyError:
                        #raise Exception(f"{srp} contains invalid taxonomy slug: {tax}")


            #TODO make this configurable in setting whether to use pk shortcuts or not
            pk = meta.get('pk')
            slug = meta['slug']

            url_components = (f'{pk}-{slug}',) if pk is not None else (slug,)

            #None is for 0th page, these won't have multiple pages
            endpoint = ContentEndpoint(self, url_components, None, srp)

            #page_list.append(endpoint)
            #page_store.add(endpoint)

            self._add_route(endpoint)

            if pk is not None:
                redirect_endpoint = RedirectEndpoint(self, (str(pk),), endpoint)
                self._add_route(redirect_endpoint)
                page_store.add(endpoint)
            else:
                print(endpoint.url)
                #input('HOLD')
                non_pk_page_store.add(endpoint)
                #input('PAST IT')

        page_store.annotate_nav() # adds prev, next attrs to Endpoint objs for page nav

        self.page_store = page_store
        self.non_pk_page_store = non_pk_page_store

        print(self.page_store.pages)
        #input('HOLD')
        print(self.routes)
        #input('HOLD')


    def _has_deep_children(self, tax_slug):
        children_stack = [tax_slug]
        while children_stack:
            focused = self.taxonomy_map[children_stack.pop()]
            has_children = len(focused['endpoint'].child_pages.exclude_taxonomies()) > 0
            if has_children:
                return True
            #for child_tax_slug in focused.get('children', []):
            children_stack.extend(focused.get('children', []))
        return False


    def _generate_taxonomy_pagination_routes(self):
        per_page = self.config.get('per_page', self.DEFAULT_PER_PAGE)

        all_taxonomy_endpoints = PageStore([info['endpoint'] for info in self.taxonomy_map.values()])
        all_endpoints = self.page_store + self.non_pk_page_store + all_taxonomy_endpoints
        print([x.url for x in all_endpoints])
        #input('HOLD')

        # first pass to gather all of the child pages for each taxonomy
        for slug, info in self.taxonomy_map.items():
            # check integrity of taxonomy order
            #all_endpoints.filter_by_topic(slug)

            #all_pages = self.page_store + self.non_pk_page_store + PageStore([inf])

            #child_pages_for_topic = self.page_store.filter_by_topic(slug)
            #non_pk_pages_for_topic = self.non_pk_page_store.filter_by_topic(slug)

            #info['endpoint'].child_pages = self.page_store.filter_by_topic(slug)


            #info['endpoint'].child_pages = child_pages

            info['endpoint'].child_pages = all_endpoints.filter_by_topic(slug)

        for slug, info in self.taxonomy_map.items():

            endpoint_0 = info['endpoint']

            # remove the taxonomy children that do not have at least 1 page in their children chain
            #eligible_child_tax_endpoints = []
            for child_slug in info.get('children', []):
                if not self._has_deep_children(child_slug):
                    print('remove me', child_slug)
                    #input('HOLD')
                    child_endpoint = self.taxonomy_map[child_slug]['endpoint']
                    endpoint_0.child_pages.remove(child_endpoint)
                    #eligible_child_tax_endpoints.append(self.taxonomy_map[child_slug]['endpoint'])

            child_pages = endpoint_0.child_pages.list_view_sort(slug)

            print(endpoint_0.url, endpoint_0.child_pages.pages)
            #input('HOLD')

            #child_taxonomies = PageStore(eligible_child_tax_endpoints).order_by_title()
            #child_pages.extendleft(child_taxonomies)
            #child_taxonomies.extend(child_pages)
            #endpoint_0.child_pages = child_taxonomies

            #child_pages.prepend(eligible_child_tax_endpoints)

            # skip if the child_pages store is still empty after all that (i.e. no pages, and no eligible child taxonomies with a page in their children)
            # also skip if pseuod
            if info['pseudo'] or not child_pages:
                continue

            #child_pages = self.page_store.filter_by_topic(slug)

            #endpoint_0 = info['endpoint']
            #endpoint_0.child_pages = child_pages # attach this in addition to paginator, pseudo taxon only have this

            #if not child_pages:
                #print(child_pages.pages)
                #input('HOLD')
                #continue


            #endpoint_0 = TaxonomyEndpoint(url_components, 0, info['srp']) # topic/, topic/page/2, topic/page/3 etc.

            # add this to taxonomy map
            #info['endpoint'] = endpoint_0

            # clean this out of taxonomy map since it is stored on endpoint obj
            #del info['srp']


            url_components = endpoint_0.url_components


            #if not info['pseudo']:
            base_redirect = RedirectEndpoint(self, url_components + [PAGE_URL] + ['1'], endpoint_0) # topic/page/1 -> topic/
            self._add_route(base_redirect)

            page_redirect = RedirectEndpoint(self, url_components + [PAGE_URL], endpoint_0) # topic/page -> topic/
            self._add_route(page_redirect)

            pag = Paginator(child_pages, per_page)

            for endpoint in pag.gen_all_pages(endpoint_0):
                self._add_route(endpoint)



            #else:
                #endpoint_0.child_pages = child_pages # attach this rather than paginator for pseudo taxonomies

            #print('-->', url_components)

            #try:
                #print([x.taxonomies for x in endpoint_0.paginator_page.items])
            #except AttributeError:
                #print([x.taxonomies for x in endpoint_0.child_pages])

            #input('HOLD')

            #print(self.routes)
            #input('HOLD pagination gen thing')

            #content_count = self.page_store.count_by_topic(slug)
            #print(slug, page_count)
            #input('HOLD PAGE COUNT')

            #num_pages = math.ceil(content_count / per_page)

            #for

        #print(self.taxonomy_map)
        #input('HOLD')


    def _generate_home_pagination_routes(self):
        #self._add_route(Endpoint(self, [])) # add home page
        per_page = self.config.get('per_page', self.DEFAULT_PER_PAGE)

        endpoint_home_0 = Endpoint(self, [], 0)
        print(endpoint_home_0.url)
        #input('HOLD')

        child_pages = self.page_store.recent()
        pag = Paginator(child_pages, per_page)

        endpoint_home_0.child_pages = child_pages # attach this in addition to paginator, for completeness although home probably won't need it

        base_redirect = RedirectEndpoint(self, [] + [PAGE_URL] + ['1'], endpoint_home_0) # /page/1 -> /
        self._add_route(base_redirect)

        print(base_redirect.url)
        #input('HOLD')


        page_redirect = RedirectEndpoint(self, [] + [PAGE_URL], endpoint_home_0) # /page -> /
        self._add_route(page_redirect)

        print(page_redirect.url)
        #input('HOLD')


        for endpoint in pag.gen_all_pages(endpoint_home_0):
            self._add_route(endpoint)





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
            #endpoint = StaticServeEndpoint(self, components, f)
            endpoint = StaticServeEndpoint(self, components)
            self._add_route(endpoint)
            #print('srp:', srp)
            #print('moveto:', move_to)

            #rendered, meta = self.wisdom.get_rendered(srp, is_taxonomy)
            #yield srp, rendered, meta
        self.static_file_mapping = static_file_mapping
        print(static_file_mapping)
        #input('HOLD static file mapping')


    def static_url(self, srp): # used by templates
        use_srp = self.static_file_mapping[Path(srp)]['srp']
        return f'/{self.STATIC_URL}/{use_srp}'


    def _copy_static(self):
        for meta in self.static_file_mapping.values():
            meta['to'].parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(meta['from'], meta['to'])

    #def _clear_output_dir(self):
        #shutil.rmtree(site.path / self.OUTPUT_DIR)

    def _build_resized_img_endpoints(self):
        for img_data in self.wisdom.gen_cached_images():
            components = img_data['serve_path'].parts[1:] # drop leading '/'
            print('img_components', components)
            #input('HOLD')
            endpoint = CachedImgEndpoint(self, components)
            self._add_route(endpoint)

            if img_data['copy_original']:
                components = img_data['original_serve_path'].parts[1:] # drop leading '/'
                endpoint = CachedImgEndpoint(self, components)
                self._add_route(endpoint)

        print(self.routes)
        #input('HOLD')

    def _copy_cached_imgs(self):
        for img_data in self.wisdom.gen_cached_images(build=True):
            publish_path = img_data['publish_path']
            publish_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(img_data['cached_path'], publish_path)

            if img_data['copy_original']:
                publish_path = img_data['original_publish_path']
                publish_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(img_data['original_path'], publish_path)


    def get_image_url(self, srp_key, max_width, max_height): # helper/convienence relay method
        return self.wisdom.get_image_url_by_key(srp_key, max_width, max_height)[1] # just return serve path


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
        self._copy_cached_imgs()


    #def get_server(self):
        #return DevelopmentServer(self.routes)
        #return DevelopmentServer
