"""ESPN adapter placeholder.

Disabled by default. Enable only after confirming the public endpoint or page
being used permits automated access under ESPN's current terms.
"""

from cfb_intel.sources.base import Source


class EspnSource(Source):
    source_name = "ESPN"
    enabled = False
    kind = "stats"

    def fetch(self): return []
    def parse(self, raw): return raw
    def normalize(self, parsed): return {}

