class PageStore:
    pages = []


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
        return filtered


    #def count_by_topic(self, slug):
        #count = 0
        #for endpoint in self.gen_by_topic(slug):
            #count +=1
        #return count



