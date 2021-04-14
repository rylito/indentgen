from uuid import uuid4
import pickle

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

        try:
            with open(self.pickle_path, 'rb') as f:
                self.data = pickle.load(f)
        except FileNotFoundError:
            self.data = {}


    def save(self):
        self.wisdom_path.mkdir(parents=True, exist_ok=True)
        with open(self.pickle_path, 'wb') as f:
            pickle.dump(self.data, f)


    def get_static_file_name(self, key_srp):
        abs_static_path = self.static_path / key_srp
        mts = abs_static_path.stat().st_mtime
        static_cache = self.data.get('static_cache')
        if static_cache:
            static_meta = static_cache.get(key_srp)
            if static_meta:
                if static_meta['mts'] == mts:
                    return static_meta['srp']

        static_cache = self.data.setdefault('static_cache', {})
        renamed = f'{key_srp.stem}_{uuid4().hex}{key_srp.suffix}'
        new_srp = key_srp.with_name(renamed)
        static_cache[key_srp] = {'mts': mts, 'srp': new_srp}
        self.save()
        return new_srp


    def get_rendered(self, key_srp, is_taxonomy = False, meta_only=False):
        abs_content_path = self.site_path / key_srp
        abs_cached_path = (self.wisdom_path / key_srp).with_suffix('.html')

        mts = abs_content_path.stat().st_mtime

        if not meta_only:
            render_cache = self.data.get('render_cache')
            if render_cache:
                render_meta = render_cache.get(key_srp)
                if render_meta:
                    if render_meta['mts'] == mts:
                        try:
                            with open(abs_cached_path, 'r') as f:
                                root = render_meta['root']
                                return f.read(), root
                        except FileNotFoundError:
                            # CACHED render result doesn't exist - re-render
                            pass

        extra_context = {
            'srp': key_srp,
            'indentgen': self.indentgen
        }

        with open(abs_content_path, 'r') as f:
            try:
                only_address = 'root.meta' if meta_only else None
                root = dentmark.parse(f, TAXONOMY_TAG_SET if is_taxonomy else CONTENT_TAG_SET, extra_context, only_address)
            except Exception as e:
                raise Exception(f'{abs_content_path}: {e}')

        root.pre_render()

        if meta_only:
            return '', root

        try:
            rendered = root.render()
        except Exception as e:
            raise Exception(f'{abs_content_path}: {e}')

        abs_cached_path.parent.mkdir(parents=True, exist_ok=True)
        with open(abs_cached_path, 'w') as f:
            f.write(rendered)

        render_cache = self.data.setdefault('render_cache', {})
        pickleable_root = PickleableTagDef(root.context, root.collectors)
        render_cache[key_srp] = {'mts': mts, 'root': pickleable_root}

        self.save()
        return rendered, root


    def get_config(self):
        mts = self.config_file_path.stat().st_mtime

        config_cache = self.data.get('config_cache')
        if config_cache:
            config_mts = config_cache['mts']
            if config_mts == mts:
                return config_cache['data']

        with open(self.config_file_path, 'r') as f:
            try:
                config_data = dentmark.render(f, CONFIG_TAG_SET)
            except Exception as e:
                raise Exception(f'{self.config_file_path}: {e}')

        self.data['config_cache'] = {'mts': mts, 'data': config_data}

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

        with open(config_file_path, 'r') as f:
            try:
                config_data = dentmark.render(f, SUBSITE_CONFIG_TAG_SET)
            except Exception as e:
                raise Exception(f'{config_file_path}: {e}')

        self.data.setdefault('subsite_cache', {})[subsite_config_dir_srp] = {'mts': mts, 'data': config_data}
        self.save()
        return config_data


    def _get_or_create_image_version(self, relative_path, max_width, max_height, copy_original, dentmark_srp):

        cache_key = (relative_path, max_width, max_height)

        img_cache = self.data.get('img_cache')
        if img_cache:
            img_data = img_cache.get(cache_key)
            if img_data:
                img_data['copy_original'] = copy_original
                return relative_path, img_data['serve_path'], img_data['original_serve_path']


        full_path = self.site_path / relative_path

        mts = full_path.stat().st_mtime

        parent = relative_path.parent

        wisdom_save_dir = self.wisdom_path / self.IMAGE_CACHE_DIR / parent
        original_name_stem = full_path.stem

        new_filename = f'{original_name_stem}_{max_width}_{max_height}.{self.CACHED_IMAGE_TYPE}'
        cached_img_path = wisdom_save_dir / new_filename
        publish_path = (self.img_output_path / relative_path).with_name(new_filename)
        serve_path = ('/' + self.img_url) / publish_path.relative_to(self.img_output_path)
        original_publish_path = (self.img_output_path / relative_path)
        original_serve_path = ('/' + self.img_url) / original_publish_path.relative_to(self.img_output_path)

        img_cache = self.data.setdefault('img_cache', {})

        img_cache[cache_key] = {
            'mts': mts,
            'cached_path': cached_img_path,
            'publish_path': publish_path,
            'serve_path': serve_path,
            'original_path': full_path,
            'max_width': max_width,
            'max_height': max_height,
            'relative_path': relative_path,
            'copy_original': copy_original,
            'original_serve_path': original_serve_path,
            'original_publish_path': original_publish_path
        }

        # This is only needed for generating helpful exception messages. If this is called via get_image_url_by_key,
        # then it's being called by a template and will have already been checked so it's safe to leave this out in that case,
        # since the template has no way of passing this value
        if dentmark_srp:
            img_cache[cache_key]['dentmark_srp'] = dentmark_srp

        self.save()

        return relative_path, serve_path, original_serve_path


    def get_image_url(self, dentmark_srp, image_relative_path, max_width, max_height, copy_original=False): # used by dentmark
        parent = dentmark_srp.parent
        full_path = self.site_path / parent / image_relative_path

        try:
            resolved = full_path.resolve(True) # make sure the image exists
            relative = resolved.relative_to(self.site_path) # make sure relative path doesn't ascend past the site_path
        except (ValueError, FileNotFoundError) as e:
            raise Exception(f"Invalid image url '{image_relative_path}'")

        return self._get_or_create_image_version(relative, max_width, max_height, copy_original, dentmark_srp)


    def get_image_url_by_key(self, srp_key, max_width, max_height): # used by templates
        return self._get_or_create_image_version(srp_key, max_width, max_height, False, None)


    def gen_cached_images(self, build=False):
        for img_data in self.data.get('img_cache', {}).values():
            if build:
                original_path = img_data['original_path']
                cached_path = img_data['cached_path']

                # TODO will prob. error if original image no longer exists. Catch and handle better
                try:
                    mts = original_path.stat().st_mtime
                except FileNotFoundError as e:
                    #raise Exception(f"Error in {img_data['dentmark_srp']}: Image file not found: {img_data['relative_path']}")
                    print(f"Stale Cached Image in Wisdom. No longer exists in content: {img_data['relative_path']}")
                    continue

                if mts != img_data['mts'] or not cached_path.exists():
                    print(f"Resizing image to {img_data['max_width']}x{img_data['max_height']}: {original_path}")
                    resize(original_path, cached_path, img_data['max_width'], img_data['max_height'])
                    img_data['mts'] = mts
                    self.save()

            yield img_data
