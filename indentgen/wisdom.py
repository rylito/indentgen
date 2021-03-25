from uuid import uuid4
import pickle
#from dentmark import render

from indentgen.default_definitions import CONFIG_TAG_SET, SUBSITE_CONFIG_TAG_SET, TAXONOMY_TAG_SET, CONTENT_TAG_SET
import dentmark
from indentgen.img_resize_utils import resize


class PickleableTagDef:
    def __init__(self, context, collectors):
        self.context = context
        self.collectors = collectors


class Wisdom:
    WISDOM_DATA = 'wisdom_data.pickle'
    IMAGE_CACHE_DIR = 'image_cache'
    CACHED_IMAGE_TYPE = 'png'

    #def __init__(self, site_path, wisdom_path, content_path, taxonomy_path, static_path, img_url, img_output_path, config_file_path, static_url):
    def __init__(self, indentgen_inst):
        self.indentgen = indentgen_inst
        self.site_path = indentgen_inst.site_path
        self.wisdom_path = indentgen_inst.wisdom_path
        self.content_path = indentgen_inst.content_path
        self.taxonomy_path = indentgen_inst.taxonomy_path
        self.static_path = indentgen_inst.static_path
        self.img_url = indentgen_inst.IMAGE_URL # the URL prefix where resized images should be accessd from in the HTML
        self.img_output_path = indentgen_inst.img_output_path # directory where resized images should be published
        self.pickle_path = self.wisdom_path / self.WISDOM_DATA

        self.config_file_path = indentgen_inst.config_file_path
        #self.static_url = indentgen_inst.STATIC_URL



        #self.content_dentmark = Dentmark(defs_module.REGISTERED_TAGS)
        #self.taxonomy_dentmark = Dentmark(defs_module.TAXONOMY_TAGS)

        try:
            with open(self.pickle_path, 'rb') as f:
                self.data = pickle.load(f)
        except FileNotFoundError:
            self.data = {}

        print(self.data)


    def save(self):
        self.wisdom_path.mkdir(parents=True, exist_ok=True)
        with open(self.pickle_path, 'wb') as f:
            pickle.dump(self.data, f)


    def get_static_file_name(self, key_srp):
        abs_static_path = self.static_path / key_srp
        print(key_srp)
        print('WILL CHECK THIS FILE', abs_static_path)
        mts = abs_static_path.stat().st_mtime
        static_cache = self.data.get('static_cache')
        if static_cache:
            static_meta = static_cache.get(key_srp)
            if static_meta:
                if static_meta['mts'] == mts:
                    print('USING CACHED STATIC FILENAME')
                    return static_meta['srp']

        print('GENERATED NEW NAME')
        static_cache = self.data.setdefault('static_cache', {})
        renamed = f'{key_srp.stem}_{uuid4().hex}{key_srp.suffix}'
        new_srp = key_srp.with_name(renamed)
        static_cache[key_srp] = {'mts': mts, 'srp': new_srp}
        self.save()
        return new_srp


    def get_rendered(self, key_srp, is_taxonomy = False, meta_only=False):


        #abs_content_path = (self.taxonomy_path if is_taxonomy else self.content_path) / key_srp
        abs_content_path = self.site_path / key_srp
        abs_cached_path = (self.wisdom_path / key_srp).with_suffix('.html')

        print('getting timestamp for', abs_content_path)
        mts = abs_content_path.stat().st_mtime

        if not meta_only:
            render_cache = self.data.get('render_cache')
            if render_cache:
                render_meta = render_cache.get(key_srp)
                if render_meta:
                    if render_meta['mts'] == mts:
                        print('USING CACHED')
                        try:
                            with open(abs_cached_path, 'r') as f:
                                root = render_meta['root']
                                return f.read(), root
                        except FileNotFoundError:
                            print('CACHED render result doesnt exist - re-render')
                            pass

        print('RENDERING')

        #dentmark = self.taxonomy_dentmark if is_taxonomy else self.content_dentmark

        extra_context = {
            'srp': key_srp,
            'indentgen': self.indentgen
        } #TODO will we need to use this?

        with open(abs_content_path, 'r') as f:
            #rendered = self.dentmark.render(f)
            try:
                only_address = 'root.meta' if meta_only else None
                root = dentmark.parse(f, TAXONOMY_TAG_SET if is_taxonomy else CONTENT_TAG_SET, extra_context, only_address)
            except Exception as e:
                raise Exception(f'{abs_content_path}: {e}')

        root.pre_render()

        if meta_only:
            print('meta only root context', root.context)
            #input('hold pk check')
            return '', root

        try:
            rendered = root.render()
        except Exception as e:
            raise Exception(f'{abs_content_path}: {e}')

        #meta = root.context['meta']
        #return rendered

        print(root.context)
        print(root.collectors)
        #input('HOLD')

        print('SAVING')
        abs_cached_path.parent.mkdir(parents=True, exist_ok=True)
        with open(abs_cached_path, 'w') as f:
            f.write(rendered)

        render_cache = self.data.setdefault('render_cache', {})
        pickleable_root = PickleableTagDef(root.context, root.collectors)
        render_cache[key_srp] = {'mts': mts, 'root': pickleable_root}

        self.save()

        return rendered, root


    def get_config(self):
        print('getting timestamp for config', self.config_file_path)
        mts = self.config_file_path.stat().st_mtime

        config_cache = self.data.get('config_cache')
        if config_cache:
            config_mts = config_cache['mts']
            if config_mts == mts:
                return config_cache['data']

        with open(self.config_file_path, 'r') as f:
            try:
                config_data = dentmark.render(f, CONFIG_TAG_SET)


                #root = dentmark.parse(f, CONFIG_TAG_SET)
                #root.pre_render(root, {})
                #config_data = root.render()
                #print(root.context)
            except Exception as e:
                raise Exception(f'{self.config_file_path}: {e}')

        print('SAVING CONFIG IN WISDOM')
        #config_cache = self.data.setdefault('config_cache', {})
        self.data['config_cache'] = {'mts': mts, 'data': config_data}

        #print(config_data)
        #input('hold')

        self.save()

        return config_data

    def get_subsite_config(self, subsite_config_dir_srp):
        config_file_path = self.site_path / subsite_config_dir_srp / self.indentgen.CONFIG_FILE_NAME
        mts = config_file_path.stat().st_mtime

        subsite_cache = self.data.get('subsite_cache')
        if subsite_cache:
            subsite_data = subsite_cache.get(subsite_config_dir_srp)
            if subsite_data:
                config_mts = subsite_data['mts']
                if config_mts == mts:
                    return subsite_data['data']

        print('Subsite config doesnt exist in cache - PARSING')

        with open(config_file_path, 'r') as f:
            try:
                config_data = dentmark.render(f, SUBSITE_CONFIG_TAG_SET)
            except Exception as e:
                raise Exception(f'{config_file_path}: {e}')

        print('SAVING SUBSITE CONFIG IN WISDOM')
        self.data.setdefault('subsite_cache', {})[subsite_config_dir_srp] = {'mts': mts, 'data': config_data}
        self.save()
        return config_data


    def _get_or_create_image_version(self, relative_path, max_width, max_height, copy_original, dentmark_srp):

        cache_key = (relative_path, max_width, max_height)

        img_cache = self.data.get('img_cache')
        if img_cache:
            img_data = img_cache.get(cache_key)
            if img_data:
                #if img_data['mts'] == mts:
                print('USING CACHED IMAGE URL for key', cache_key)
                #input('HOLD')
                img_data['copy_original'] = copy_original
                return relative_path, img_data['serve_path'], img_data['original_serve_path']


        full_path = self.site_path / relative_path

        mts = full_path.stat().st_mtime
        #print('resolved:', resolved)
        #print('relative:', relative)


        print('full_path:', full_path)
        print('relative:', relative_path)

        parent = relative_path.parent

        print('???', self.wisdom_path, self.IMAGE_CACHE_DIR, parent)
        wisdom_save_dir = self.wisdom_path / self.IMAGE_CACHE_DIR / parent
        original_name_stem = full_path.stem

        print(wisdom_save_dir)
        #input('HOLD WTF')
        print(original_name_stem)

        new_filename = f'{original_name_stem}_{max_width}_{max_height}.{self.CACHED_IMAGE_TYPE}'

        cached_img_path = wisdom_save_dir / new_filename


        print('original_path', full_path)
        print('------>>>>>>cached_img_path', cached_img_path)
        print('self.wisdow_path', self.wisdom_path)
        print('wisdom_save_dir',wisdom_save_dir)

        publish_path = (self.img_output_path / relative_path).with_name(new_filename)
        print('publish_path', publish_path)

        serve_path = ('/' + self.img_url) / publish_path.relative_to(self.img_output_path)
        print('serve_path', serve_path)

        original_publish_path = (self.img_output_path / relative_path)
        print('original_publish_path', original_publish_path)


        original_serve_path = ('/' + self.img_url) / original_publish_path.relative_to(self.img_output_path)
        print('original_serve_path', original_serve_path)

        img_cache = self.data.setdefault('img_cache', {})
        img_cache[cache_key] = {'mts': mts, 'cached_path': cached_img_path, 'publish_path': publish_path, 'serve_path': serve_path, 'original_path': full_path, 'max_width': max_width, 'max_height': max_height, 'relative_path': relative_path, 'copy_original': copy_original, 'original_serve_path': original_serve_path, 'original_publish_path': original_publish_path}

        # This is only needed for generating helpful exception messages. If this is called via get_image_url_by_key, then it's being called by a template and will have already been checked so it's safe to leave this out in that case, since the template has no way of passing this value
        if dentmark_srp:
            img_cache[cache_key]['dentmark_srp'] = dentmark_srp

        self.save()

        return relative_path, serve_path, original_serve_path


    def get_image_url(self, dentmark_srp, image_relative_path, max_width, max_height, copy_original=False): # used by dentmark
        print(dentmark_srp, image_relative_path, max_width, max_height)
        print(self.site_path)
        parent = dentmark_srp.parent
        full_path = self.site_path / parent / image_relative_path
        print('full path', full_path)

        try:
            resolved = full_path.resolve(True) # make sure the image exists
            relative = resolved.relative_to(self.site_path) # make sure relative path doesn't ascend past the site_path
        except (ValueError, FileNotFoundError) as e:
            raise Exception(f"Invalid image url '{image_relative_path}'")

        print('resolved', resolved)
        print('relative', relative)

        return self._get_or_create_image_version(relative, max_width, max_height, copy_original, dentmark_srp)


    def get_image_url_by_key(self, srp_key, max_width, max_height): # used by templates
        return self._get_or_create_image_version(srp_key, max_width, max_height, False, None)


    def gen_cached_images(self, build=False):
        for img_data in self.data.get('img_cache', {}).values():
            if build:
                original_path = img_data['original_path']
                cached_path = img_data['cached_path']
                #mts = original_path.stat().st_mtime 
                print('original', original_path)
                print('cached', cached_path)
                print('cached_exists', cached_path.exists())
                #input('HOLD wisdom')

                #resized_exists = img_data['cached_path'].exists()

                # TODO will prob. error if original image no longer exists. Catch and handle better
                try:
                    mts = original_path.stat().st_mtime
                except FileNotFoundError as e:
                    raise Exception(f"Error in {img_data['dentmark_srp']}: Image file not found: {img_data['relative_path']}")

                if mts != img_data['mts'] or not cached_path.exists():
                    print('THE THUMB NEEDS TO BE MADE FOR', cached_path)
                    print(mts, img_data['mts'], cached_path.exists())
                    print('after:',img_data['mts'])
                    resize(original_path, cached_path, img_data['max_width'], img_data['max_height'])
                    img_data['mts'] = mts
                    self.save()
                else:
                    print('we golden')
                    #input('HOLD')

            yield img_data


    #def get_url_for_pk(self, pk): # used in TagDefs to dynamically resolve URLS to page urls
        #print('URL_FOR_PK_DICT', self.pk_lookup)
        #input('HOLD')
        #return self.pk_lookup[pk]
