pandy
======

Basically takes a file/folder, input the markup to convert from, the output markup and runs it through pandoc.

Features
----------

  * A bit easier syntax around pandoc commands and some added by me
  * Output folder keeping or not the folder structure
  * Source can be a file, a folder, .list containing file paths or .ini
  * Formats: some of them have abbreviations (see below)
  * Output format: you can have more than one! just separate them with spaces
  * You can create a nice book (html, just adds navigation links between files) like a wiki or for documentation. If you don't like/want "Next-Prev" navigation links, you can use the file's title. It creates a nice simple index file or you can include your own.
  * Use a config file: so you don't have to remember all the arguments or write a "wrapper" script for a "wrapper" script :)
  * ``[TOC]`` support. That means that a file that has it, will have a TOC. No more separating files: these ones with TOC, these ones without, and finally place them in the same folder.
  * If you use markdown and convert to HTML there are some goodies for you! abbreviations (real abbreviations; they are parsed and not ignored as pandoc does), admonitions and "WikiLinks"
  * No-so-ugly default template for book :)

  
Usage
--------

To use the script, just call it with something like:

	pandy source [options]


	
Explanation
----------

From a file/folder/.list/.ini, input the "from" markup and the output format, which can be a list separated with spaces. Formats are stripped down to the most common ones:

  * from: docbook, html, json, latex, markdown, markdown\_github, markdown\_mmd, markdown\_phpextra, markdown\_strict, mediawiki (or mw), opml, rst, textile
  * output: all the above + asciidoc, beamer, docx (or doc), epub, epub3, fb2, html5, odt, opendocument (or opendoc), pdf, plain, rtf, slides (or slide)

Notes: 

  * All "markdown"s can be entered as "md". So: markdown -> md; markdown\_github -> md\_github; etc.
  * The slides are specified with ``--slides``
  * These markdown extensions are automatically enabled: link\_attributes, hard\_line\_breaks

You can input some options of pandoc but with different names:

	--from , -f           Convert from this format
	--to, -t              Convert to this format (can be a space separated list)
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
	--toc                 include TOC
	--depth               TOC depth.
	--hide                e-mail obfuscation
	--sections            Wrap sections in <sections>, attach identifiers instead of titles
	--pandoc PANDOC       Pandoc path. Default: pandoc
	--data-dir FOLDER     Data directory

If you merge and use output, you must only specify the folder. It takes the name from the parent folder/source 
	
As well as some of my own:

	--flat                Don't keep folder structure
	--book, -b            Make a book with navigation (next/prev) and index
	--no-nav, -nn         (For book) disable book navigation
	--nav-title, -nt      (For book) use titles in book navigation
	--no-side, -ns        (For book) Disable sidebar navigation
	--no-side-toc, -nst   (For book) disable TOC in sidebar (keep in doc)
	--config FILE         Use a configuration file (option=key values)
	--tpl-pandy           (For book) Pandy's embebed template: simple and not so ugly
	
If you use markdown and convert to HTML, there're some goodies for you. You can have abbreviations, as PHP Markdown Extra:

	Some text with an ABBR and a REF. Ignore REFERENCE and ref.

	*[ABBR]: Abbreviation
	*[REF]: Abbreviation Reference

And admonitions with this markup:

	[class/type:optional title]
	  * markdown
	  * super
	  * content

The "class/type" would be something like "information", "danger", "tip", "hint", "hungry", "duck", "yay" ...

You can also include a tag for toc ([TOC]) to have that file with a toc instead of remembering to enter ``--toc``. (It just adds it automatically after searching the file, no magic here)

Book converts all files to HTML and adds navigation links. Useful to make simple documentation. 

If you use markdown you have more goodies: create your own index (as ``index.md``) and have "wikiLinks". Wikilinks can be in any file as ``[:filename][optional title]`` where filename can have extension or not, and if you don't include a title, it finds the file title. The order of the files in the index affect the sidebar navigation. With this you can create cooler documentation or use it as a poor's man/simple wiki.

If you wish to create your own template for book, pandy adds some variables for you to include: 

  * ``side_navigation`` the sidebar navigation 
  * ``book_navigation`` book navigation (previous/index/next)
  * ``project-index`` link to index. Useful if you have subfolders 
  * ``project-title`` Index title. Useful if you create your own index with a title

If you don't like setting the options in the CLI, or having a script, you can create your configuration in a key=value file (like ini). Example: myconfiguration.ini contains:

	PANDOC_DATA_DIR = C:\Program Files\Pandoc
	TEMPLATE = github.html
	HIGHLIGHT = zenburn
	TOC = False

Specify the configuration file with ``--config`` (the extension doesn't matter, INI headers are ignored as well as comments. Don't worry) or just have a ``settings.ini`` where you run pandy.


History
-----------

### Version 2.0

Total rewrite! Many fixes and (internal) cleanup/improvement. Also:

  * new wiki links: like markdown reference links but inverted -> ``[:file][title]``
  * wikilinks in any file (not only index) (book)
  * auto discover index
  * if custom index has title, use it as project title
  * list all titles (and toc) in index
  * order files according to custom index
  * navigation: pages titles in sidebar, next-prev
  * option to hide navigation in book
  * option to exclude toc from sidebar navigation
  * Navigations in pandoc variables
  * built-in template (book)
  * modify command options
  * read .ini automatically in folder where runs/source
  * args take precedence over ini, which take precedence over default
  * change .ini format. See examples (basically remove quotes, lists are space separated)


### Version 1.9

  * only python 3
  * fixes for book
  * prints file being converted
  * Filter extensions for converting, only html (hardcoded)
  * add titles in sidebar for navigation (``--navside``). Include ``$book_navigation$`` in your Pandoc template


### Version 1.8.1

New admonition syntax:

    [class/type:optional title]
      * markdown
      * super
      * content

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