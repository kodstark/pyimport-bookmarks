## pyimport_bookmarks

Import Firefox bookmarks to Google / GMarks bookmarks.

Firefox has bookmarks in directories structure but Google and GMarks has bookmarks 
in flat structure but with possible tags.

This script is going through Firefox directories and add bookmarks to flat structure with creating tags 
basing on directories name. 

Look that Firefox allows you yo keep description with each bookmarks however GMarks and Google imports 
don't save description.

#### Usage

Default usage is:

```python import_bookmarks.py -b bookmarks.html -g google_bookmarks.html -m flat_bookmarks.html```

Type ```python import_bookmarks.py -h``` to see available options.

After generating google_bookmarks.html you can open it in browser and click "Start import" button.

After generating flat_bookmarks.html you can replace it with default Firefox bookmarks.html 
and start import in GMarks plugin.

#### License

Copyright (C) 2007 Kamil Demecki <kodstark@gmail.com>

Licensed under the terms of any of the following licenses at your choice:

- GNU Lesser General Public License Version 2.1 or later (the "LGPL")
  http://www.gnu.org/licenses/lgpl.html

- Mozilla Public License Version 1.1 or later (the "MPL")
  http://www.mozilla.org/MPL/MPL-1.1.html