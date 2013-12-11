pandy
======

Basically takes a file/folder, input the markup to convert from, the output markup and runs it through pandoc.

Usage
--------

To use the script, just call it with something like:

	pandy source format_from format/s_to [other options]

Explanation somewhere below.

Features
----------

  * A bit easier syntax around pandoc commands (I can't never remember them)
  * Output folder keeping or not the folder structure
  * Source can be a file, a folder or a .list containing file paths
  * Formats: some of them have abbreviations (see below)
  * Output format: you can have more than one! just separate them with spaces
  * You can create a nice book (html, just adds navigation links between files). If you don't like/want "Next-Prev" navigation links, you can use the file's title. It creates a nice simple index file or you can include your own.
  * Use a config file: so you don't have to remember all the arguments or write a "wrapper" script for a "wrapper" script :)
  * ``[TOCME]`` support. That means that a file that has it, will have a TOC. No more separating files: these ones with TOC, these ones without, and finally place them in the same folder.
  * If you use markdown and convert to HTML there are some goodies for you! abbreviations (real abbreviations, like that they are parsed and not ignored as pandoc does) and admonitions.
  * "WikiLinks" for your custom index file!


Explanation
----------

From a file/folder/.list, input the "from" markup and the output format, which can be a list separated with spaces. Formats are stripped down to the most common ones:

  * from: docbook, html, json, latex, markdown, markdown\_github, markdown\_mmd, markdown\_phpextra, markdown\_strict, mediawiki (or mw), opml, rst, textile
  * output: all the above +  asciidoc, beamer, docx (or doc), epub, epub3, fb2, html5, odt, opendocument (or opendoc), pdf, plain, rtf, slides (or slide)

Notes: 

  * All "markdown"s can be entered as "md". So: markdown -> md; markdown\_github -> md\_github; etc.
  * The slides are specified with ``--slides``
  * These markdown extensions are automatically enabled: link\_attributes, hard\_line\_breaks

You can input some options of pandoc but with different names:

	--output, -o          Output folder
	--self                self contained file
	--header FILE         Header file. Included as it is (raw, verbatim)
	--footer FILE         Footer file. Included as it is (raw, verbatim)
	--index FILE          Custom index file for book. Can use wiki links
	--html4               Use html4 output instead of html5
	--merge, -m           Merge files.
	--slides              Slides format.
	--bib FILE            Use bibliography file
	--css FILE            External CSS
	--highlight           Highlight style. 
	--highlight-no        No highlight
	--tpl FILE            Template file.
	--toc, -t             include TOC
	--depth               TOC depth.
	--hide                e-mail obfuscation
	--sections            Wrap sections in <sections>, attach identifiers instead of titles
	--pandoc PANDOC       Pandoc path. Default: pandoc
	--data-dir FOLDER     Data directory

As well as some of my own:

	--flat                Don't keep folder structure
	--book, -b            Make a book with navigation (next/prev) and index
	--nav, -n             (For book) use titles in navigation
	--config FILE         Use a configuration file (option=key values)

If you use markdown and convert to HTML, there're some goodies for you. You can have abbreviations, as PHP Markdown Extra:

	Some text with an ABBR and a REF. Ignore REFERENCE and ref.

	*[ABBR]: Abbreviation
	*[REF]: Abbreviation Reference

And admonitions with this markup:

	<admon "class/type" "optional title">
	  * markdown
	  * super
	  * content
	</admon>

The "class/type" would be something like "information", "danger", "tip", "hint", "hungry", "duck", "yay" ...




You can also include a tag for TOC (``[TOCME]``) to have that file with a TOC instead of remembering to enter --toc or separating files in two groups and then placing them together. (It just adds it automatically after searching the file, no magic here)

For book: you can create your own index and have "wikiLinks" as ``[](file|nice_file.txt)``. It will render as ``[title of file](nice_file.html)``

If you don't like setting the options in the CLI, or having a script which calls pandy with the arguments you prefer, you can create your configuration in a key=value file (like ini). Example: 

	PANDOC_DATA_DIR = "C:\Program Files\Pandoc"
	TEMPLATE = 'github.html'
	HIGHLIGHT= 'zenburn'
	FORMATS_TO = [html, pdf]
	NAV = True

Specify the configuration file with ``--config`` (the extension doesn't matter, INI headers are ignored as well as comments (line or inline). Don't worry)


History
-----------

### Version 1.8

  * Clean up code and refactoring 
  * default config in dictionary
  * minor fix for admonitions
  * Fix finding H1s
  * config file support (ini without sections)
  * changes to args
  * add processing messages 
  * no more tmp files  
  * Fix merging
  * merge (HTML): now can parse metadata block and have toc for full document
  * Book: include toc ONLY on selected file
  * book: fix having title twice in file when declared with meta-block
  * fix titles in book: add them, if not found add the filename (no ext)
  * wikiLinks: if md link has no title and it's an existing file, use the filename as title 
  * Book: warn if no output path (defaults to current dir) and source dir is the running one
  * config dict takes precedence over args


### Version 1.5

Rewritten and to include cool stuff:

  * Add abbreviations parsing: markdown -> html
  * Add admonition parsing
  * Add warning when book also have other output formatting & html
  * Add warning custom index with wiki links only for markdown
  * Add more formats for input and output            
  * fix: formats_to: no duplicates
  * fix: ``--nav`` only for book
  * fix: add html5 output default, can change to html with ``--html4``
  * fix: when merging add ``<title>``

  
### Version 1.0 

Basic wrapper for pandoc with: 

  * folder (recursive) support
  * merge files in directory (automatically)