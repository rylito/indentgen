import math

def gen_exp_range(slots, span, reverse=False):
    use_pow = math.log(span, slots)

    use_range = range(slots-1, -1, -1) if reverse else range(slots)

    for i, x in enumerate(use_range):
        yield i, math.floor(math.pow(x+1, use_pow))


def get_links(num_pages, on_page, slots): # on_page 1 indexed
    if num_pages <= slots:
        for x in range(num_pages):
            yield x + 1
        return

    num_pages_left = on_page - 1
    num_pages_right = num_pages - on_page

    available_slots = slots - 1 # the page you're on takes up one # 9
    pages_per_slot = (num_pages - 1) / available_slots # 11

    alloc_slots_left = int(num_pages_left // pages_per_slot) # 2.6 -> 2
    alloc_slots_right = int(num_pages_right // pages_per_slot) # 6.3 -> 6

    # make the allocations whole, favor giving whole one to 'smaller' side

    if alloc_slots_left + alloc_slots_right < available_slots:
        if on_page == 1:
            alloc_slots_right += 1
        elif on_page == num_pages:
            alloc_slots_left += 1
        elif alloc_slots_left < alloc_slots_right:
            alloc_slots_left += 1
        else:
            alloc_slots_right += 1


    if alloc_slots_left == 1:
        yield on_page - 1
    elif alloc_slots_left:
        for i,val in gen_exp_range(alloc_slots_left, num_pages_left, reverse=True):
            use_val = 1 if i == 0 else (on_page - val)
            yield use_val


    yield on_page


    if alloc_slots_right == 1:
        yield on_page + 1 #if on_page < num_pages else num_pages
    elif alloc_slots_right:
        for i,val in gen_exp_range(alloc_slots_right, num_pages_right):
            use_val = num_pages if i == alloc_slots_right - 1 else val + on_page
            yield use_val


class Paginator:

    class Page:
        def __init__(self, paginator, page_num_0, start_index, end_index, prev_endpoint, next_endpoint):
            self.paginator = paginator
            self.items = paginator.items[start_index:end_index]
            self.page_num = page_num_0 + 1 # 1 indexed
            self.start_index = start_index
            self.end_index = end_index
            self.prev_endpoint = prev_endpoint
            self.next_endpoint = next_endpoint

            self.num_items_on_page = len(self.items)

        @property
        def has_next(self):
            return self.next_endpoint is not None

        @property
        def has_prev(self):
            return self.prev_endpoint is not None


    def __init__(self, child_items, per_page):
        self.items = child_items
        self.per_page = per_page
        self.total = len(child_items)
        self.num_of_pages = math.ceil(self.total / per_page)
        self._endpoint_objs = []


    def _attach_page(self, list_endpoint, prev_endpoint): # 0 based page index read off of list_endpoint_obj
        page_num = list_endpoint.page
        start_index = page_num * self.per_page
        end_index = start_index + self.per_page
        if end_index > self.total:
            end_index = self.total

        #prev_endpoint = list_endpoint.prev_page()
        next_endpoint = list_endpoint.next_page() if (page_num + 1) < self.num_of_pages else None

        #return Page(self, page_num, start_index, end_index, prev_endpoint, next_endpoint)
        list_endpoint.paginator_page = self.Page(self, page_num, start_index, end_index, prev_endpoint, next_endpoint)
        self._endpoint_objs.append(list_endpoint)
        return list_endpoint


    def gen_all_pages(self, list_endpoint_0):
        prev_endpoint = None
        annotated_endpoint = self._attach_page(list_endpoint_0, prev_endpoint)
        yield annotated_endpoint

        while annotated_endpoint.paginator_page.next_endpoint is not None:
            prev_endpoint = annotated_endpoint
            next_endpoint = annotated_endpoint.paginator_page.next_endpoint
            annotated_endpoint = self._attach_page(next_endpoint, prev_endpoint)
            yield annotated_endpoint


    def get_page_endpoint(self, page_num): # 1-indexed
        return self._endpoint_objs[page_num - 1]


    def gen_all_page_endpoints(self, on_page, slots): # on_page 1-indexed
        page_num_gen = get_links(self.num_of_pages, on_page, slots) # on_page 1 indexed
        for page_num in page_num_gen:
            yield self.get_page_endpoint(page_num)
