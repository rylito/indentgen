#TODO make sure urls don't clobber 'static' and other reserved URLS

import sys
import shutil
import importlib
#import pkgutil
#import pickle
from pathlib import Path
from default_definitions import *
from wisdom import Wisdom
from dentmark import Dentmark
from mako.template import Template
from mako.lookup import TemplateLookup



class Indentgen:
    WISDOM_DIR = '_wisdom'
    CONTENT_DIR = 'content'
    TAXONOMY_DIR = 'taxonomy'
    DEFS_MODULE_NAME = 'indentgen_defs'
    CONFIG_FILE_NAME = 'config.dentmark'
    THEME_DIR = 'theme'
    TEMPLATE_DIR = Path(THEME_DIR) / 'templates'
    TEMPLATE_CACHE_DIR = Path(WISDOM_DIR) / 'mako_modules'
    STATIC_DIR = Path(THEME_DIR) / 'static'

    #TODO puth these in config.dentmark instead?
    OUTPUT_DIR = 'publish'
    STATIC_URL = '_static'
    CACHE_BUST_STATIC_EXTENSIONS = ('.css', '.js') #TODO put this in config.dentmark instead?

    def __init__(self, site_path):
        self.site_path = Path(site_path)
        print(self.site_path)

        sys.path.append(str(self.site_path))
        print(sys.path)

        #self.defs_module_name = defs_module_name
        #self.available_definitions = self._find_defs()
        #self.dentmark = Dentmark('dentmark_defs')

        #print(self.available_definitions)
        self.defs_module = importlib.import_module(self.DEFS_MODULE_NAME)
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

        self._build_taxonomy_map()
        self._build_content_map()
        self._add_pages_to_taxonomy_mappings()

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

    # {tax_slug: {}, tax_slug: {meta.., children: []}}
    def _build_taxonomy_map(self):
        tax_map = {}
        top_level_taxonomies = []
        taxonomy_urls = {}

        for srp, rendered, meta in self._gen_walk_content(is_taxonomy=True):
            collision = tax_map.get(meta['slug'])
            if collision:
                raise Exception(f"Taxonomy slugs conflict: {srp} and {collision['srp']}")
            meta_copy = meta.copy() # use a copy to not contaminate the _wisdom
            meta_copy['srp'] = srp
            tax_map[meta_copy['slug']] = meta_copy
            if 'parent' not in meta_copy:
                top_level_taxonomies.append(meta_copy['slug'])

        for slug, meta in tax_map.items():
            parent_slug = meta.get('parent')
            if parent_slug:
                try:
                    parent_meta = tax_map[parent_slug]
                except KeyError:
                    raise Exception(f"{meta[srp]}: meta parent value does not exist for '{parent_slug}'")
                children = parent_meta.setdefault('children', [])
                children.append(slug)

            url_components = [slug]
            focused = meta
            while 'parent' in focused:
                focused = tax_map[focused['parent']]
                url_components.append(focused['slug'])
            url_components.reverse()
            taxonomy_urls[tuple(url_components)] = meta['srp']
            print(url_components)

            meta['url_components'] = url_components

        print(tax_map)
        print(top_level_taxonomies)
        print(taxonomy_urls)

        self.taxonomy_map = tax_map
        self.top_level_taxonomies = top_level_taxonomies
        self.taxonomy_urls = taxonomy_urls


    def _build_content_map(self):
        page_map = {}
        page_urls = {}
        for srp, rendered, meta in self._gen_walk_content(is_taxonomy=False):
            all_urls = set([(meta['slug'],)])
            aliases = meta.get('aliases')
            if aliases:
                all_urls.update([(_,) for _ in aliases])
            print('ALL aliases:', all_urls)

            for url_dict in (self.taxonomy_urls, page_urls):
                collision = set(url_dict).intersection(all_urls)
                if collision:
                    conflicting_slug = collision.pop()
                    collides_with = url_dict[conflicting_slug]
                    raise Exception(f"{srp} slug or aliases conflict with {collides_with}: {conflicting_slug}")

            for url in all_urls:
                page_urls[url] = srp

            meta_copy = meta.copy()
            meta_copy['srp'] = srp
            page_map[meta_copy['slug']] = meta_copy

        self.page_map = page_map
        self.page_urls = page_urls
        print(self.page_map)


    def _add_pages_to_taxonomy_mappings(self):
        taxonomy_to_content_map = {}
        for slug, meta in self.page_map.items():
            taxonomy = meta.get('taxonomy')
            if taxonomy:
                for tax in taxonomy:
                    try:
                        tax_meta = self.taxonomy_map[tax]
                    except KeyError:
                        raise Exception(f"{meta['srp']} contains invalid taxonomy slug: {tax}")
                    tax_meta.setdefault('pages', []).append(slug)
        print(self.taxonomy_map)


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
            #print('srp:', srp)
            #print('moveto:', move_to)

            #rendered, meta = self.wisdom.get_rendered(srp, is_taxonomy)
            #yield srp, rendered, meta
        self.static_file_mapping = static_file_mapping
        print(static_file_mapping)


    def static_url(self, srp):
        use_srp = self.static_file_mapping[Path(srp)]['srp']
        return f'/{self.STATIC_URL}/{use_srp}'


    def _copy_static(self):
        for meta in self.static_file_mapping.values():
            meta['to'].parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(meta['from'], meta['to'])

    def generate(self):
        # index.html
        template = self.templates.get_template('base.html')
        print(template.render(config=self.config, static_url=self.static_url))
        self._copy_static()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    #parser.add_argument("square", help="display a square of a given number")
    parser.add_argument("--source-dir", help="The directory of the site source files")
    args = parser.parse_args()
    print(args)

    if args.source_dir:
        source_dir = args.source_dir
    else:
        import os
        source_dir = os.getcwd()

    i = Indentgen(source_dir)
    i.generate()

    #print(args.square**2)


    #i = Indentgen('/home/ryli/src/personal/indentgen/sample_site')

    #i.wisdom.save()
    #i.wisdom.get_rendered('hello')
    #i.config

    #i.walk_content(True)

    #rendered, ctx = i.wisdom.get_rendered(i.content_path / 'articles' / 'article_1.dentmark')
    #print(rendered)
    #print(ctx)

    #i.build_taxonomy_map()
    #i._build_content_map()
