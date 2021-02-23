class PageStore:
    def __init__(self, init=[]):
        self.pages = init


    def add(self, endpoint):
        self.pages.append(endpoint)


    def filter_by_topic(self, slug):
        filtered = []
        for endpoint in self.pages:
            #rendered, root = endpoint.get_rendered(wisdom)
            #meta = root.context['meta']
            if slug in endpoint.taxonomies:
                #yield endpoint
                filtered.append(endpoint)
        return PageStore(filtered)

    def __len__(self):
        return len(self.pages)

    def __getitem__(self, key):
        return self.pages[key]
