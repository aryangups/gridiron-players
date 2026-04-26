"""NCAA public stats adapter placeholder, disabled by default."""

from cfb_intel.sources.base import Source


class NcaaSource(Source):
    source_name = "NCAA"
    enabled = False
    kind = "stats"

    def fetch(self): return []
    def parse(self, raw): return raw
    def normalize(self, parsed): return {}

