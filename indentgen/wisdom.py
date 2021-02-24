from uuid import uuid4
import pickle
#from dentmark import render

from indentgen.default_definitions import CONFIG_TAG_SET, TAXONOMY_TAG_SET, CONTENT_TAG_SET
import dentmark


class Wisdom:
    WISDOM_DATA = 'wisdom_data.pickle'

    def __init__(self, site_path, wisdom_path, content_path, taxonomy_path, static_path, config_file_path):
        self.site_path = site_path
        self.wisdom_path = wisdom_path
        self.content_path = content_path
        self.taxonomy_path = taxonomy_path
        self.static_path = static_path
        self.pickle_path = self.wisdom_path / self.WISDOM_DATA

        self.config_file_path = config_file_path

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



    def get_rendered(self, key_srp, is_taxonomy = False):
        #abs_content_path = (self.taxonomy_path if is_taxonomy else self.content_path) / key_srp
        abs_content_path = self.site_path / key_srp
        abs_cached_path = (self.wisdom_path / key_srp).with_suffix('.html')

        print('getting timestamp for', abs_content_path)
        mts = abs_content_path.stat().st_mtime

        render_cache = self.data.get('render_cache')
        if render_cache:
            render_meta = render_cache.get(key_srp)
            if render_meta:
                if render_meta['mts'] == mts:
                    print('USING CACHED')
                    try:
                        with open(abs_cached_path, 'r') as f:
                            return f.read(), render_meta['root']
                    except FileNotFoundError:
                        print('CACHED render result doesnt exist - re-render')
                        pass

        print('RENDERING')

        #dentmark = self.taxonomy_dentmark if is_taxonomy else self.content_dentmark

        with open(abs_content_path, 'r') as f:
            #rendered = self.dentmark.render(f)
            try:
                root = dentmark.parse(f, TAXONOMY_TAG_SET if is_taxonomy else CONTENT_TAG_SET)
            except Exception as e:
                raise Exception(f'{abs_content_path}: {e}')

        extra_context = {} #TODO will we need to use this?
        root.pre_render(root, extra_context)
        rendered = root.render()
        #meta = root.context['meta']
        #return rendered

        print('SAVING')
        abs_cached_path.parent.mkdir(parents=True, exist_ok=True)
        with open(abs_cached_path, 'w') as f:
            f.write(rendered)

        render_cache = self.data.setdefault('render_cache', {})
        render_cache[key_srp] = {'mts': mts, 'root': root}

        self.save()

        return rendered, root


    def get_config(self):
        print('getting timestamp for config', self.config_file_path)
        mts = self.config_file_path.stat().st_mtime

        config_cache = self.data.get('config_cache')
        if config_cache:
            config_mts = config_cache['mts']
            if config_mts == mts:
            #if False: #TODO DELME
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
