from pathlib import Path

class PathDict:
    def __init__(self):
        self._ordered_path_keys = []
        self._data_dict = {}


    def add(self, path_or_f, data):
        key = Path(path_or_f)

        if key not in self._data_dict:
            # key does not exist. Add new key and order it
            self._ordered_path_keys.append(key)
            self._ordered_path_keys.sort(key=lambda x: len(x.parts), reverse=True)

        self._data_dict[key] = data


    def get(self, path_or_f):
        # fetches the key that matches the closest relative path
        key = Path(path_or_f)

        for path in self._ordered_path_keys:
            try:
                key.relative_to(path)
                return self._data_dict[path]
            except ValueError:
                pass
        return None


    def __iter__(self):
        # when iterating over these to validate, we should check the highest path first (i.e. path with least parts)
        # in case children subsites depend on a parent higher in the path tree. Since the keys are ordered from paths with the most
        # parts to paths with the least, iterate over this object in reverse key order.
        for key in reversed(self._ordered_path_keys):
            yield self._data_dict[key]
