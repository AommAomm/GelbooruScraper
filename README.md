Required python to be installed.
syntex: <Required> (Optional) `python scraper.py <tags> (number of pages) (-nofuta) (-noai)`
use + to append multiple tags
example: `python scraper.py gawr_gura+cute 5 -nofuta -noai`
This example will download the first 5 pages of results that contain the tag Gawr Gura and cute, while excluding the tags that include funatari or AI generated images.

example: `python scraper.py hatsune_miku -nofuta`
This example will download *all* images that return when searching Hatsune Miku, to include images tagged as AI generated.
Its always recommended to use a page limit because there could be thousands of results.
