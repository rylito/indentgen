#TODO enforce that series must have part #s

import sys
import shutil
import importlib
from pathlib import Path

import dentmark

from mako.template import Template
from mako.lookup import TemplateLookup

from indentgen.wisdom import Wisdom
from indentgen.path_dict import PathDict
from indentgen.default_definitions.content_tag_defs import CONTENT_TAG_SET
from indentgen.default_definitions.taxonomy_tag_defs import TAXONOMY_TAG_SET
from indentgen.taxonomy_def_set import TaxonomyDefSet
from indentgen.endpoints import PAGE_URL, Endpoint, ContentEndpoint, ContentGalleryEndpoint, TaxonomyEndpoint, RedirectEndpoint, StaticServeEndpoint, CachedImgEndpoint, DateArchiveEndpoint, Http404Endpoint, RssEndpoint, SiteMapEndpoint
from indentgen.paginator import Paginator
from indentgen.page_store import PageStore


class Indentgen:
    WISDOM_DIR = '_wisdom'
    CONTENT_DIR = 'content'
    TAXONOMY_DIR = 'taxonomy'
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
    GALLERY_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png')

    IMAGE_URL = '_img'

    DEFAULT_PER_PAGE = 25
    DEFAULT_PER_PAGE_GALLERY = 50

    def __init__(self, site_path):
        self.site_path = Path(site_path)

        sys.path.append(str(self.site_path))

        try:
            self.defs_module = importlib.import_module(self.CUSTOM_DEFS_MODULE_NAME)
        except ModuleNotFoundError:
            print('No custom definitions found') #TODO better error or warning here?

        self.content_path = self.site_path / self.CONTENT_DIR
        self.taxonomy_path = self.site_path / self.TAXONOMY_DIR
        self.wisdom_path = self.site_path / self.WISDOM_DIR

        self.static_path = self.site_path / self.STATIC_DIR
        self.output_path = self.site_path / self.OUTPUT_DIR
        self.static_output_path = self.output_path / self.STATIC_URL

        self.img_output_path = self.output_path / self.IMAGE_URL

        self.config_file_path = self.site_path / self.CONFIG_FILE_NAME

        template_dir = self.site_path / self.TEMPLATE_DIR
        template_cache_dir = self.site_path / self.TEMPLATE_CACHE_DIR
        self.templates = TemplateLookup(directories=[template_dir], module_directory=template_cache_dir)

        self.wisdom = Wisdom(self)
        self.config = self.wisdom.get_config()

        self.routes = {}

        self.pk_link_map = {}
        self.slug_map = {}
        self.subsite_data = PathDict()

        self._patch_def_sets()

        self._build_taxonomy_map()
        self._check_taxonomy_tags_meta(is_taxonomy=True)

        self._find_subsite_srps()

        # do a pass of the content parsing only the meta to build the PK map so that
        # all pks are known prior to rendering the full page content
        self._pre_populate_meta_pk()

        self._validate_subsite_slugs()

        self._build_page_store()

        self._check_taxonomy_tags_meta(is_taxonomy=False)

        self._generate_taxonomy_pagination_routes()
        self._generate_date_archive_routes()
        self._generate_home_pagination_routes()

        self._generate_404_route()
        self._generate_rss_route()
        self._generate_sitemap_route()

        self._build_static_file_remapping()
        self._build_resized_img_endpoints()


    def _gen_walk_content(self, is_taxonomy=False, meta_only=False):
        use_path = self.taxonomy_path if is_taxonomy else self.content_path
        for f in use_path.glob('**/*.dentmark'):
            srp = f.relative_to(self.site_path)

            # skip over subsite config
            if srp.name == self.CONFIG_FILE_NAME:
                continue

            rendered, root = self.wisdom.get_rendered(srp, is_taxonomy, meta_only)
            yield srp, rendered, root


    def _add_route(self, endpoint):
        collision_endpoint = self.routes.get(endpoint.url)
        if collision_endpoint is not None:
            raise Exception(f"URL conflict for '{endpoint.url}': {endpoint.identifier} and {collision_endpoint.identifier}")
        self.routes[endpoint.url] = endpoint


    def _patch_def_sets(self):
        content_tag_set = dentmark.defs_manager.get_tag_set(CONTENT_TAG_SET)
        taxonomy_tag_set = dentmark.defs_manager.get_tag_set(TAXONOMY_TAG_SET)

        # Monkey patch this to use the extended class to defer resolving tag names
        # Kinda hacky, but it works

        for tag_set in (content_tag_set, taxonomy_tag_set):
            new_def_set = TaxonomyDefSet.copy_from_def_set(tag_set)
            dentmark.defs_manager.def_sets[tag_set.tag_set_name] = new_def_set


    # {tax_slug: {}, tax_slug: {meta.., children: []}}
    def _build_taxonomy_map(self):
        tax_map = {}
        top_level_taxonomies = []

        for srp, rendered, root in self._gen_walk_content(is_taxonomy=True):
            meta = root.context['meta']

            slug_path = meta['slug_path']
            collision = tax_map.get(slug_path)
            if collision:
                raise Exception(f"Taxonomy slugs conflict: {srp} and {collision['srp']}")

            tax_map[slug_path] = {'slug_path': slug_path, 'srp': srp, 'title': meta['title']}
            tax_map[slug_path]['pseudo'] = meta['pseudo'] if 'pseudo' in meta else False
            tax_map[slug_path]['gallery'] = meta['gallery'] if 'gallery' in meta else False

            slug_path_components = slug_path.split('/')

            parent = '/'.join(slug_path_components[:-1])

            #TODO enforce that pseudo taxonomies cannot have children?

            if parent:
                tax_map[slug_path]['parent'] = parent
            else:
                top_level_taxonomies.append(slug_path)


        for slug_path, info in tax_map.items():
            parent_slug_path = info.get('parent')
            if parent_slug_path:
                try:
                    children = tax_map[parent_slug_path].setdefault('children', [])
                except KeyError:
                    raise Exception(f"{info['srp']}: invalid parent taxonomy: '{parent_slug_path}'")
                children.append(slug_path)

            url_components = info['slug_path'].split('/')

            info['top_level'] = url_components[0]

            taxonomies = info.get('taxonomy', [])
            srp = info['srp']
            del info['srp']

            endpoint_0 = TaxonomyEndpoint(self, url_components, 0, srp)

            # add this to taxonomy map
            info['endpoint'] = endpoint_0


        self.taxonomy_map = tax_map
        self.top_level_taxonomies = top_level_taxonomies


    def _check_taxonomy_tags_meta(self, is_taxonomy):
        for srp, rendered, root in self._gen_walk_content(is_taxonomy):
            meta = root.context['meta']
            taxonomy = meta.get('taxonomy')
            if taxonomy is not None:
                invalid = set(taxonomy).difference(self.taxonomy_map)
                if invalid:
                    raise Exception(f"Invalid taxonomy tag(s) {invalid} in meta: {srp}")


    # locate other config files in content dir so that we can handle subsites correctly
    def _find_subsite_srps(self):
        use_path = self.content_path
        for f in use_path.glob(f'**/{self.CONFIG_FILE_NAME}'):
            srp = f.relative_to(self.site_path)
            subsite_dir = srp.parent

            subsite_config = self.wisdom.get_subsite_config(subsite_dir)

            self.subsite_data.add(subsite_dir, {'config': subsite_config, 'config_srp': srp})


    # first pass is to resolve all of the pks in the meta, so that they are available
    # when rendering the full body. This is needed to reslove link url's that are PKs in the dentmark
    def _pre_populate_meta_pk(self):
        for srp, rendered, root in self._gen_walk_content(is_taxonomy=False, meta_only=True):

            slug = root.context['meta']['slug']

            conflicting_slug_srp = None

            # verify that slug does not conflict with a taxonomy slug
            if slug in self.taxonomy_map:
                conflicting_slug_srp = self.taxonomy_map[slug]['endpoint'].srp

            # verify that slug does not conflict with another page or subsite slug
            elif slug in self.slug_map:
                conflicting_slug_srp = self.slug_map[slug]['srp']

            if conflicting_slug_srp:
                raise Exception(f"Slugs conflict. Both are '{slug}'. Must be unique: {srp} and {conflicting_slug_srp}")

            pk = root.context['meta'].get('pk')

            #TODO make this configurable in setting whether to use pk shortcuts or not
            url = f'{pk}-{slug}' if pk is not None else slug

            self.slug_map[slug] = {'slug': slug, 'srp': srp, 'last_url_part': url, 'subsite_data': self.subsite_data.get(srp)}

            if pk:
                self.pk_link_map[pk] = slug


    def _validate_subsite_slugs(self):
        # now that we have ALL page slugs stored in self.slug_map, validate that the subsite slugs and parents make sense
        for subsite_data in self.subsite_data:
            config = subsite_data['config']
            config_srp = subsite_data['config_srp']
            slug = config['subsite_slug']
            parent_slug = config['parent_slug']

            if parent_slug not in self.slug_map:
                raise Exception(f"parent_slug '{parent_slug}' invalid in subsite config: {config_srp}")

            if slug in self.slug_map:
                conflicting_srp = self.slug_map[slug]['srp']
                raise Exception(f"subsite_slug '{slug}' conflicts with existing slug: {config_srp} and {conflicting_srp}")

            self.slug_map[slug] = {'slug': slug, 'srp': config_srp, 'last_url_part': slug, 'subsite_data': subsite_data}


    def _resolve_url_components(self, slug):
        slug_data = self.slug_map[slug]
        components = [slug_data['last_url_part']]

        seek = False
        while slug_data.get('subsite_data'):
            subsite_data = slug_data.get('subsite_data')
            config = subsite_data['config']
            subsite_slug = config['subsite_slug']
            if subsite_slug != slug:
                components.append(subsite_slug)
            seek = True
            slug_data = self.slug_map[config['parent_slug']]

        if seek:
            components.append(slug_data['last_url_part'])

        components.reverse()

        return components


    def _get_content_gallery_endpoint(self, gallery_ctx, url_components, srp, subsite_config):
        endpoint_0 = ContentEndpoint(self, url_components, 0, srp, subsite_config)

        # TODO gather photos. For now, just assume all photos live in same directory (alongside)
        # dentmark file. Maybe later, we can make this search location customizable with a context
        # tag or something.

        child_pages = PageStore()
        image_srps = []
        search_dir = srp.parent
        for f in search_dir.glob(f'**/*.*'):
            for ext in self.GALLERY_IMAGE_EXTENSIONS:
                if ext.lower() == f.suffix.lower():
                    image_srps.append(f)
                    break
        image_srps.sort()

        per_page_gallery = gallery_ctx.get('per_page', self.DEFAULT_PER_PAGE_GALLERY)

        prev = None
        for i,image_srp in enumerate(image_srps):
            # gallery url should be /XX-entry-slug/[image_1_indexed]
            gal_url_components = url_components + [str(i+1)]

            photo_data = {}
            #TODO iterating over this every time isn't efficient. Use sorted dict or something?
            for img_data in gallery_ctx.get('img', []):
                if img_data['key'] == image_srp:
                    photo_data = img_data
                    break

            gal_endpoint = ContentGalleryEndpoint(self, gal_url_components, image_srp, photo_data, endpoint_0) #TODO add attrs later
            if prev is not None:
                prev.next = gal_endpoint
                gal_endpoint.prev = prev
            child_pages.add(gal_endpoint)
            self._add_route(gal_endpoint)
            prev = gal_endpoint

        endpoint_0.child_pages = child_pages
        self._make_paginated_routes(endpoint_0, per_page_gallery)
        return endpoint_0


    def _build_page_store(self):
        page_store = PageStore()
        non_pk_page_store = PageStore()
        for srp, rendered, root in self._gen_walk_content(is_taxonomy=False):
            meta = root.context['meta']

            slug = meta['slug']
            url_components = self._resolve_url_components(slug)

            subsite_config = None
            subsite_data = self.subsite_data.get(srp)
            if subsite_data:
                subsite_config = subsite_data['config']

            has_gallery = False
            for tax_slug_path in meta.get('taxonomy', {}):
                if self.taxonomy_map[tax_slug_path]['gallery']:
                    has_gallery = True
                    break

            if has_gallery:
                gallery_ctx = meta.get('gallery', {})

                endpoint = self._get_content_gallery_endpoint(gallery_ctx, url_components, srp, subsite_config)
            else:
                #None is for 0th page, these won't have multiple pages
                endpoint = ContentEndpoint(self, url_components, None, srp, subsite_config)
                self._add_route(endpoint)

            pk = meta.get('pk')

            use_page_store = page_store
            use_non_pk_page_store = non_pk_page_store

            if subsite_data:
                use_page_store = subsite_data.setdefault('page_store', PageStore())
                use_non_pk_page_store = subsite_data.setdefault('non_pk_page_store', PageStore())

            if pk is not None:
                redirect_endpoint = RedirectEndpoint(self, (str(pk),), endpoint)
                self._add_route(redirect_endpoint)
                use_page_store.add(endpoint)
            else:
                use_non_pk_page_store.add(endpoint)

        page_store.annotate_nav() # adds prev, next attrs to Endpoint objs for page nav

        # do the same for all subsite page stores
        for subsite_data in self.subsite_data:

            # TODO is this a good way to handle this? Should I always combine these for both base site and subsites,
            # and maybe just exclude pages from home listing explicitly by using a pseudo taxonomy or something rather
            # relying on presence/absence of PK?
            subsite_page_store = subsite_data.get('page_store', PageStore())

            # message archive doesn't have any PK pages, so just combine these for now. Not sure if this is good default behavior for every subsite though
            subsite_page_store += subsite_data.get('non_pk_page_store', PageStore())

            subsite_page_store.annotate_nav()

        self.page_store = page_store
        self.non_pk_page_store = non_pk_page_store


    def _make_paginated_routes(self, base_endpoint, per_page=None):
        url_components = base_endpoint.url_components

        base_redirect = RedirectEndpoint(self, url_components + [PAGE_URL] + ['1'], base_endpoint) # 2021/3/page/1 -> 2021/3/
        self._add_route(base_redirect)

        page_redirect = RedirectEndpoint(self, url_components + [PAGE_URL], base_endpoint) # 2021/3/page -> 2021/3/
        self._add_route(page_redirect)

        #TODO this paginator stuff is a mess. clean it up. The PageStore should probably generate the paginator,
        # not all of this attaching the paginator to the endpoint crap. Plus violating DRY doing this in about 3 places

        if per_page is None:
            per_page = self.config.get('per_page', self.DEFAULT_PER_PAGE)

        pag = Paginator(base_endpoint.child_pages, per_page)

        for endpoint in pag.gen_all_pages(base_endpoint):
            self._add_route(endpoint)


    def _has_deep_children(self, tax_slug):
        children_stack = [tax_slug]
        while children_stack:
            focused = self.taxonomy_map[children_stack.pop()]
            has_children = len(focused['endpoint'].child_pages.exclude_taxonomies()) > 0
            if has_children:
                return True

            children_stack.extend(focused.get('children', []))
        return False


    def _generate_taxonomy_pagination_routes(self):
        per_page = self.config.get('per_page', self.DEFAULT_PER_PAGE)

        all_taxonomy_endpoints = PageStore([info['endpoint'] for info in self.taxonomy_map.values()])
        all_endpoints = self.page_store + self.non_pk_page_store + all_taxonomy_endpoints

        # add the subsite pages to all_endpoints
        for subsite_data in self.subsite_data:
            subsite_page_store = subsite_data.get('page_store')
            if subsite_page_store:
                all_endpoints += subsite_page_store

            non_pk_page_store = subsite_data.get('non_pk_page_store')
            if non_pk_page_store:
                all_endpoints += non_pk_page_store

        # first pass to gather all of the child pages for each taxonomy
        for slug, info in self.taxonomy_map.items():
            info['endpoint'].child_pages = all_endpoints.filter_by_topic(slug)

        for slug, info in self.taxonomy_map.items():
            endpoint_0 = info['endpoint']

            # remove the taxonomy children that do not have at least 1 page in their children chain
            #eligible_child_tax_endpoints = []
            for child_slug in info.get('children', []):
                if not self._has_deep_children(child_slug):
                    child_endpoint = self.taxonomy_map[child_slug]['endpoint']
                    endpoint_0.child_pages.remove(child_endpoint)

            child_pages = endpoint_0.child_pages.list_view_sort(slug)
            endpoint_0.child_pages = child_pages

            # skip if the child_pages store is still empty after all that (i.e. no pages, and no eligible child taxonomies with a page in their children)
            # also skip if pseuod
            if info['pseudo'] or not child_pages:
                continue

            self._make_paginated_routes(endpoint_0)


    def _generate_date_archive_routes(self):
        date_archive_url = self.config.get('date_archive_url')
        if not date_archive_url:
            # don't make date archives
            return

        dated_endpoints = self.page_store.only_dated() + self.non_pk_page_store.only_dated()
        by_months = dated_endpoints.group_by_date()

        year_list_endpoint = DateArchiveEndpoint(self, [date_archive_url], 0)
        year_list_endpoint.child_pages = PageStore()

        last_year = None

        for (year, month), page_store in sorted(by_months.items()): # this will iterate through the months in ascending order
            url_components = [date_archive_url, str(year), str(month)]

            month_0 = DateArchiveEndpoint(self, url_components, 0)

            # archive pages should be in ascending order
            month_0.child_pages = page_store.order_by_date(descending=False)

            self._make_paginated_routes(month_0)

            if last_year != year or not last_year:
                year_archive_endpoint = DateArchiveEndpoint(self, [date_archive_url, str(year)], 0)
                year_archive_endpoint.child_pages = PageStore()
                year_list_endpoint.child_pages.add(year_archive_endpoint)

            year_list_endpoint.child_pages[-1].child_pages.add(month_0)

            last_year = year

        # make year pages
        for year_endpoint in year_list_endpoint.child_pages:
            self._make_paginated_routes(year_endpoint)

        # make date archive root
        self._make_paginated_routes(year_list_endpoint)


    def _generate_home_pagination_routes_helper(self, per_page, page_store, prefix_components, subsite_config=None):
        endpoint_home_0 = Endpoint(self, prefix_components, 0, subsite_config)

        child_pages = page_store.recent()
        pag = Paginator(child_pages, per_page)

        endpoint_home_0.child_pages = child_pages # attach this in addition to paginator, for completeness although home probably won't need it

        base_redirect = RedirectEndpoint(self, prefix_components + [PAGE_URL] + ['1'], endpoint_home_0) # /page/1 -> /
        self._add_route(base_redirect)

        page_redirect = RedirectEndpoint(self, prefix_components + [PAGE_URL], endpoint_home_0) # /page -> /
        self._add_route(page_redirect)

        for endpoint in pag.gen_all_pages(endpoint_home_0):
            self._add_route(endpoint)


    def _generate_home_pagination_routes(self):
        # base site
        per_page = self.config.get('per_page', self.DEFAULT_PER_PAGE)
        self._generate_home_pagination_routes_helper(per_page, self.page_store, [])

        # subsites
        for subsite_data in self.subsite_data:
            config = subsite_data['config']
            per_page = config.get('per_page', self.DEFAULT_PER_PAGE)

            # TODO is this a good way to handle this? Should I always combine these for both base site and subsites,
            # and maybe just exclude pages from home listing explicitly by using a pseudo taxonomy or something rather
            # relying on presence/absence of PK?
            page_store = subsite_data.get('page_store', PageStore())

            # message archive doesn't have any PK pages, so just combine these for now. Not sure if this is good default behavior for every subsite though
            page_store += subsite_data.get('non_pk_page_store', PageStore())

            prefix_components = self._resolve_url_components(config['subsite_slug'])

            self._generate_home_pagination_routes_helper(per_page, page_store, prefix_components, config)


    def _generate_404_route(self):
        endpoint = Http404Endpoint(self)
        self._add_route(endpoint)


    def _generate_rss_route(self):
        endpoint = RssEndpoint(self)
        self._add_route(endpoint)


    def _generate_sitemap_route(self):
        endpoint = SiteMapEndpoint(self)
        self._add_route(endpoint)


    def _build_static_file_remapping(self):
        static_file_mapping = {}

        for f in self.static_path.glob('**/*.*'):
            srp = f.relative_to(self.static_path)

            if f.suffix in self.CACHE_BUST_STATIC_EXTENSIONS:
                use_srp = self.wisdom.get_static_file_name(srp)
            else:
                use_srp = srp

            move_to = self.static_output_path / use_srp
            static_file_mapping[srp] = {'from': f, 'to': move_to, 'srp': use_srp}

            components = [self.STATIC_URL] + list(use_srp.parts)
            endpoint = StaticServeEndpoint(self, components)
            self._add_route(endpoint)

        self.static_file_mapping = static_file_mapping


    def static_url(self, srp): # used by templates
        use_srp = self.static_file_mapping[Path(srp)]['srp']
        return f'/{self.STATIC_URL}/{use_srp}'


    def _copy_static(self):
        for meta in self.static_file_mapping.values():
            meta['to'].parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(meta['from'], meta['to'])


    def _build_resized_img_endpoints(self):
        for img_data in self.wisdom.gen_cached_images():
            components = img_data['serve_path'].parts[1:] # drop leading '/'
            endpoint = CachedImgEndpoint(self, components)
            self._add_route(endpoint)

            if img_data['copy_original']:
                components = img_data['original_serve_path'].parts[1:] # drop leading '/'
                endpoint = CachedImgEndpoint(self, components)
                self._add_route(endpoint)


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


    def get_url_for_pk(self, pk): # used in TagDefs to dynimacially resolve URLS to pages
        slug = self.pk_link_map[int(pk)]
        url_components = self._resolve_url_components(slug)
        url = '/'.join(url_components)
        return f'/{url}/' # add leading/trailing slashes to make it an absolute link


    def generate(self):
        # remove old/stale published content
        shutil.rmtree(self.output_path, ignore_errors=True) # if dir doesn't exist, ignore error

        for endpoint in self.routes.values():
            #print('rendering', endpoint.url_components, endpoint.url, endpoint.identifier, endpoint.get_output_path())
            rendered = endpoint.render()
            if rendered is None:
                continue

            output_path = self.output_path
            endpoint_output_path = endpoint.get_output_path()

            suffix = endpoint_output_path.suffix
            if suffix:
                fname = endpoint_output_path.name
                if suffix == '.xml':
                    rendered = rendered.lstrip() # strip leading whitespace from xml files to avoid XML parsing error
            else:
                output_path = output_path / endpoint_output_path
                fname = 'index.html'

            output_path.mkdir(parents=True, exist_ok=True)

            with open(output_path / fname, 'w') as f:
                f.write(rendered)

        self._copy_static()
        self._copy_cached_imgs()
