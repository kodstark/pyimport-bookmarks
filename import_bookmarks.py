# -*-coding: utf8 -*-
"""Import Firefox bookmarks to Google / GMarks bookmarks.

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
"""
import codecs
import HTMLParser
import sys
from optparse import OptionParser

def js_escape(text, charset=None):
    if type(text) == type(u""):
        text = text.encode([charset, 'utf-8'][charset == None])
    text = text.replace("\r", "\\r").replace("\n", "\\n")
    text = text.replace('"', '\\"').replace("'", "\\'")
    return "'" + text + "'"

def encode_utf8(text, charset=None):
    if type(text) == type(u""):
        text = text.encode([charset, 'utf-8'][charset == None])
    return text

class BookmarksHtmlParser(HTMLParser.HTMLParser):
    def __init__(self, *process_bookmarks_actions):
        HTMLParser.HTMLParser.__init__(self)
        self.folder_list = []
        self.is_folder_name = False
        self.address = None
        self.title = []
        self.desc = []
        self.start_a = False
        self.start_dd = False
        self.process_bookmarks_actions = process_bookmarks_actions

    def handle_starttag(self, tag, attrs):
        if tag == 'dt' and self.address:
            self.process_bookmark()

        if tag == 'h3':
            self.is_folder_name = True

        if tag == 'a':
            self.process_a_start(attrs)

        if tag == 'dd':
            self.start_dd = True
            
    def handle_endtag(self, tag):
        if tag == 'dl':
            if self.address:
                self.process_bookmark()
            self.folder_list.pop()

        if tag == 'h3':
            self.is_folder_name = False

        if tag == 'a':
            self.start_a = False

    def handle_data(self, dane):
        if self.is_folder_name:
            self.folder_list.append(dane)

        if self.start_a:
            self.title.append(dane)

        if self.start_dd:
            self.desc.append(dane)
            
    def process_a_start(self, attrs):
        self.start_a = True
        self.address = [v for k, v in attrs if k == 'href']
        if self.address:
            self.address = self.address[0]
        else:
            raise Exception("Missing href attribute in line (%s, %s)" % self.getpos())            

    def process_bookmark(self):
        """Get data from last accessed bookmark"""
        for action in self.process_bookmarks_actions:
            is_stop_action = action.process_bookmark(self)
            if is_stop_action: break
        self.reset_process_bookmark()

    def reset_process_bookmark(self):
        self.address = None
        self.title = []
        self.desc = []
        self.start_dd = False

class BookmarksBuffer:
    def __init__(self):
        self.counter_processed = 0
        self.address_set = set()
        self.doubled_addresses = set()
        self.address_map = {}

    def count_processed_bookmark(self):
        self.counter_processed = self.counter_processed + 1

class ProcessBookmarkAction:
    def process_bookmark(self, parser_zakladek):
        """Return true if skip next actions"""

class ReportBookmarkAction(ProcessBookmarkAction):
    def __init__(self, bufor_zakladek):
        self.bookmarks_bufer = bufor_zakladek
        
    def process_bookmark(self, bookmark_parser):
        self.bookmarks_bufer.count_processed_bookmark()
        if bookmark_parser.address in self.bookmarks_bufer.address_set:
            self.bookmarks_bufer.doubled_addresses.add(bookmark_parser.address)
        self.bookmarks_bufer.address_set.add(bookmark_parser.address)
        if not bookmark_parser.address in self.bookmarks_bufer.address_map:
            self.first_update_map(bookmark_parser)
        else:
            self.update_map_with_doubled(bookmark_parser)        

    def first_update_map(self, bookmark_parser):
        self.bookmarks_bufer.address_map[bookmark_parser.address] = {'title':bookmark_parser.title, 
            'desc':bookmark_parser.desc, 
            'folder_set':set(bookmark_parser.folder_list)}

    def update_map_with_doubled(self, bookmark_parser):
        address = lambda:self.bookmarks_bufer.address_map[bookmark_parser.address]
        address()['title'].append("--Doubled--")
        address()['title'].extend(bookmark_parser.title)
        address()['desc'].extend(bookmark_parser.desc)
        address()['folder_set'].update(set(bookmark_parser.folder_list))
        
    def finish(self):
        self.printReport(sys.stdout)

    def printReport(self, output_stream):
        output_stream.write("Processed %s bookmarks\n" % self.bookmarks_bufer.counter_processed)
        output_stream.write("Doubled URLs in %s bookmarks" % len(self.bookmarks_bufer.doubled_addresses))

class ImportGoogleAction(ProcessBookmarkAction):    
    def __init__(self, bookmarks_buffer, **kargs):
        self.bookmarks_bufer = bookmarks_buffer
        self.create_output_stream(kargs)
        self.is_first_link = True
        self.output_stream.write(self.get_page_beginning())
        
    def create_output_stream(self, kargs):
        if 'fileName' in kargs:
            self.output_stream = open(kargs['fileName'], 'w')
        elif 'output_stream' in kargs:
            self.output_stream = kargs['output_stream']
        else:
            raise Exception("Missing one of argument 'fileName' or 'output_stream'")        

    def process_bookmark(self, parser_zakladek):
        pass
    
    def finish(self):
        self.close_stream();

    def close_stream(self):
        for address, data in self.bookmarks_bufer.address_map.iteritems():
            if self.is_first_link:
                self.is_first_link = False
            else:
                self.output_stream.write(',')
            self.output_stream.write(' {"a": %s' % js_escape(address))
            self.output_stream.write(', "t": %s' % js_escape(" ".join(data['title']).title()))
            self.output_stream.write(', "o": %s' % js_escape(" ".join(data['desc'])))
            if data['folder_set']:
                labels = ", ".join([js_escape(f.title()) for f in data['folder_set']])
                self.output_stream.write(', "e":[%s]' % labels)
            self.output_stream.write('}\n')

        self.output_stream.write(self.get_page_end())
        self.output_stream.close()
        
    def get_page_beginning(self):
        return '''<html>
<head>
    <!-- File generated by import_bookmarks.py -->
    <meta http-equiv="content-type" content="text/html; charset=utf-8">
    <script type="text/javascript">
    function xmlEscape(str) {
      return str.replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    }
    
    function jsonCallback(bookmarks) {
      var dataNode = document.getElementById("data");
    
      var bookmarksXml = [];
    
      for (var i = 0, bookmark; bookmark = bookmarks[i]; i++) {
        bookmarksXml.push(
          "<bookmark>",
    "<url>", xmlEscape(bookmark.a), "</url>",
    "<title>", xmlEscape(bookmark.t), "</title>",
    "<annotation>", xmlEscape(bookmark.o), "</annotation>");
        if (bookmark.e) {
          bookmarksXml.push("<labels><label>",
                    bookmark.e.join(","),
                    "</label></labels>");
        }
        bookmarksXml.push(
          "</bookmark>");
      }
    
      // Split xml processing instruction across name and value in an ugly
      // hack to do something with the equals sign
      dataNode.name = "<?xml version";
      dataNode.value = [
        "\\"1.0\\" encoding=\\"utf-8\\"?>",
        "<bookmarks>",
          bookmarksXml.join(""),
        "</bookmarks>"].join("");
    
      var formNode = document.getElementById("upload-form");
      formNode.action += "&zx=" + Math.round(65535 * Math.random());
    }
    </script>
</head>
<body>
    <h1>Import bookmarks to Google</h1>
    <p>This page was generated and contains JavaScript function with all bookmarks ready to send 
    to Google service http://www.google.com/bookmarks/mark?op=upload. Click button to start import.</p> 
    <form id="upload-form" action="http://www.google.com/bookmarks/mark?op=upload" method="POST">
      <input type="hidden" name="" id="data">
      <p><input type="submit" name="import" value="Start import" /></p>  
    </form>
    <script type="text/javascript">
    jsonCallback(['''   
        
    def get_page_end(self):
        return """])</script>
</body>
</html>"""             

class BookmarksFlattenAction(ProcessBookmarkAction):
    def __init__(self, bufor_zakladek, **kargs):
        self.bookmarks_bufer = bufor_zakladek
        self.create_output_stream(kargs)
        self.output_stream.write(self.get_page_beginning())
        
    def create_output_stream(self, kargs):
        if 'fileName' in kargs:
            self.output_stream = open(kargs['fileName'], 'w')
        elif 'output_stream' in kargs:
            self.output_stream = kargs['output_stream']
        else:
            raise Exception("Missing one of argument 'fileName' or 'output_stream'") 
        
    def get_page_beginning(self):
        return '''<!DOCTYPE NETSCAPE-Bookmark-file-1>
<meta http-equiv="content-type" content="text/html; charset=utf-8">
<title>Bookmarks</title>
<h1>Bookmarks</h1>
<dl><p>
'''               

    def process_bookmark(self, bookmark_parser):
        pass

    def finish(self):
        self.close_stream();    

    def close_stream(self):
        labels_map = self.create_labels_map()
        for label, bookmarks_list in labels_map.iteritems():
            self.save_bookmarks_for_label(label, bookmarks_list)

        self.output_stream.write("</dl><p>")
        self.output_stream.close()
        
    def create_labels_map(self):
        labels_map = {}
        for address, data in self.bookmarks_bufer.address_map.iteritems():
            for label in data['folder_set']:
                if label not in labels_map:
                    labels_map[label] = []
                labels_map[label].append((address, data))        
        return labels_map        
        
    def create_desc(self, desc, title):
        result = " ".join(desc).strip()
        if len(title) > 50:
            desc_temp = [title]
            if result:
                desc_temp.append(' -- ')
                desc_temp.append(result)
            result = "".join(desc_temp)
        return result        
        
    def save_bookmarks_for_label(self, label, bookmarks_list):
        self.output_stream.write("<dt><h3>%s</h3></dt>\n" % encode_utf8(label.title()))
        self.output_stream.write("<dl><p>\n")
        for address, data in bookmarks_list:
            title = " ".join(data['title']).strip().title()
            desc = self.create_desc(data['desc'], title)
            self.output_stream.write('<dt><a href="%s">%s</a>\n' % (encode_utf8(address), encode_utf8(title)))
            if desc.strip():
                self.output_stream.write('<dd>%s\n' % encode_utf8(desc))        
        self.output_stream.write("</dl><p>\n")            


def parse_args():
    usage = "Usage: %prog [options]\nType %prog -h to see available options"
    parser = OptionParser(usage=usage)
    parser.add_option("-b", "--bookmarks", dest="bookmarks", help="read Firefox bookmarks from file", metavar="FILE")
    parser.add_option("-g", "--google", dest="google", help="save Google import HTML to file", metavar="FILE")
    parser.add_option("-m", "--gmarks", dest="gmarks", help="save GMarks HTML to file", metavar="FILE")
    options = parser.parse_args()[0]
    if not options.bookmarks:
        parser.error("bookmarks file is required")
    if not (options.google or options.gmarks):
        parser.error("at least one option -g or -m are required")
    return options

def create_actions(options, bookmarks_buffer):
    result = []
    result.append(ReportBookmarkAction(bookmarks_buffer))
    if options.google:
        result.append(ImportGoogleAction(bookmarks_buffer, fileName=options.google))
    if options.gmarks:
        result.append(BookmarksFlattenAction(bookmarks_buffer, fileName=options.gmarks))
    return result

def do_parsing(options, actions):
    parser = BookmarksHtmlParser(*actions)
    parser.feed(codecs.open(options.bookmarks, 'r', 'UTF-8').read())
    parser.close()

def finish_actions(actions):
    return [action.finish() for action in actions]

def main():
    options = parse_args()
    bookmarks_buffer = BookmarksBuffer()
    actions = create_actions(options, bookmarks_buffer)
    do_parsing(options, actions)
    finish_actions(actions)

if __name__ == '__main__':
    main()
