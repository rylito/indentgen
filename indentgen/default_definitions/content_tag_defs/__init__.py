from . root import *
from . paragraph import *
from . meta import *
from . image import *
from . anchor import *
from . pullquote import *
from . meta_reviews import *
from . lists import *
from . emphasis import *
from . conversation import *
from . message_archive import *
from . blockquote import *
from . aside import *

from . content_tag_set import content_tag_set
from indentgen.taxonomy_def_set import MetaTaxonomyContext

content_tag_set.register_tag(MetaTaxonomyContext)
