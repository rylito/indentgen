class PageStore:
    def __init__(self, init=None):
        self.pages = init if init else []


    def add(self, endpoint):
        self.pages.append(endpoint)


    def remove(self, endpoint):
        self.pages.remove(endpoint)


    def extend(self, endpoint_list_or_pagestore):
        self.pages.extend(endpoint_list_or_pagestore)


    def extendleft(self, endpoint_list_or_pagestore):
        # TODO probably a way more efficient way to do this using deque or something
        extended = []
        for endpoint in endpoint_list_or_pagestore:
            extended.append(endpoint)

        for endpoint in self.pages:
            extended.append(endpoint)

        self.pages = extended


    def order_by_date(self, descending=True): # sort from latest to earliest (descending) by default
        sort = sorted(self.pages, key=lambda x: x.meta['date'], reverse=descending)
        return PageStore(sort)


    def order_by_title(self, descending=False):
        sort = sorted(self.pages, key=lambda x: x.meta['title'], reverse=descending)
        return PageStore(sort)


    def recent(self):
        return self.order_by_date(descending=True)


    def only_taxonomies(self):
        return PageStore([endpoint for endpoint in self.pages if endpoint.is_taxonomy])


    def exclude_taxonomies(self):
        return PageStore([endpoint for endpoint in self.pages if not endpoint.is_taxonomy])


    def only_dated(self):
        return PageStore([endpoint for endpoint in self.pages if endpoint.meta.get('date')])


    def group_by_date(self):
        # (year, month (1 indexed)): PageStore
        by_months = {}

        for endpoint in self:
            date = endpoint.meta['date']
            by_months.setdefault((date.year, date.month), PageStore()).add(endpoint)

        return by_months


    def filter_by_topic(self, slug):
        filtered = []
        parts = {}
        for endpoint in self.pages:
            if slug in endpoint.taxonomies:
                part = endpoint.taxonomies[slug]
                if part is not None:
                    collision_part = parts.get(part)
                    if collision_part is not None:
                        raise Exception(f"Pages cannot have the same part '{part}' for taxonomy '{slug}': {endpoint.srp} and {collision_part.srp}")
                    parts[part] = endpoint
                filtered.append(endpoint)

        # sort by parts/orders
        filtered_and_sorted = sorted(filtered, key=lambda x: x.taxonomies[slug] if x.taxonomies[slug] is not None else len(filtered))

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


    def list_view_sort(self, slug):
        # sort precedence:
        # 1. taxonomy order
        # 2. taxonomies in alphabetical order
        # 3. pages in date descending
        # 4. pages with no date last (order doesn't matter)

        ordered = []
        taxonomies = []
        pages = []
        no_date = []

        for endpoint in self.pages:
            tax_order = endpoint.taxonomies.get(slug)
            if tax_order is not None:
                ordered.append(endpoint)
            elif endpoint.is_taxonomy:
                taxonomies.append(endpoint)
            elif endpoint.meta.get('date'):
                pages.append(endpoint)
            else:
                no_date.append(endpoint)

            ordered.sort(key=lambda x: x.taxonomies[slug])
            taxonomies.sort(key=lambda x: x.meta['title'])
            pages.sort(key=lambda x: x.meta['date'], reverse=True)

        return PageStore(ordered + taxonomies + pages + no_date)


    def annotate_nav(self, descending=False):
        recent = self.order_by_date(descending)
        prev = None
        for endpoint in recent:
            if prev:
                prev.next = endpoint
            endpoint.prev = prev
            prev = endpoint

        if recent:
            endpoint.next = None


    def __len__(self):
        return len(self.pages)


    def __getitem__(self, key):
        return self.pages[key]


    def __add__(self, other):
        return PageStore(self.pages + other.pages)
