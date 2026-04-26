"""Sports Reference adapter placeholder, disabled by default."""

from cfb_intel.sources.base import Source


class SportsReferenceSource(Source):
    source_name = "Sports Reference"
    enabled = False
    kind = "stats"

    def fetch(self): return []
    def parse(self, raw): return raw
    def normalize(self, parsed): return {}

