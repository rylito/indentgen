class PageStore:
    def __init__(self, init=[]):
        self.pages = init


    def add(self, endpoint):
        self.pages.append(endpoint)


    def filter_pages(self):
        filtered = []
        for endpoint in self.pages:
            #if not endpoint.meta.get('date'):
                #print(endpoint.meta)
                #input('HOLD')
            if (not endpoint.is_taxonomy) and endpoint.meta.get('date'): # could just use date here since taxonomies don't have dates, but be explicit
                #print(endpoint.meta, 'ADDED', endpoint.meta.get('date'))
                filtered.append(endpoint)
        return PageStore(filtered)


    def order_by_date(self, descending=True): # sort from latest to earliest (descending) by default
        sort = sorted(self.pages, key=lambda x: x.meta['date'], reverse=descending)
        return PageStore(sort)


    def recent(self, descending=True):
        pages = self.filter_pages() # make sure we're only ordering pages, not taxonomies and unlisted pages which don't have dates
        return pages.order_by_date(descending)


    def filter_by_topic(self, slug):
        filtered = []
        parts = {}
        for endpoint in self.pages:
            #rendered, root = endpoint.get_rendered(wisdom)
            #meta = root.context['meta']
            if slug in endpoint.taxonomies:
                #yield endpoint
                part = endpoint.taxonomies[slug]
                if part is not None:
                    collision_part = parts.get(part)
                    if collision_part is not None:
                        raise Exception(f"Pages cannot have the same part '{part}' for taxonomy '{slug}': {endpoint.srp} and {collision_part.srp}")
                    parts[part] = endpoint
                filtered.append(endpoint)

        # sort by parts/orders
        #print(len(filtered))
        filtered_and_sorted = sorted(filtered, key=lambda x: x.taxonomies[slug] if x.taxonomies[slug] is not None else len(filtered))
        #print([x.taxonomies for x in filtered_and_sorted])

        #TODO could get rid of the parts = {} and just raise both errors below depending on if part == last_part

        # check to make sure no missing part numbers 1 - X
        last_part = 0
        for endpoint in filtered_and_sorted:
            part = endpoint.taxonomies[slug]
            if part is None:
                continue
            if part != last_part + 1:
                raise Exception(f"Page should be part '{last_part + 1}' for taxonomy '{slug}', not {part}: {endpoint.srp}")
            last_part = part

        return PageStore(filtered_and_sorted)

    def __len__(self):
        return len(self.pages)

    def __getitem__(self, key):
        return self.pages[key]
