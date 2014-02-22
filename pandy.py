#! python3
# -*- coding: utf-8 -*-

# "Wrapper" for Pandoc (python 3): pandy [file/folder] [options]
# tested for pandoc 1.12.3

"""
	Basically takes a file/folder, input the markup to convert from, the output markup and run it through pandoc.

	More explained:
	From a file/folder/.list/.ini, input the "from" markup and the output format, which can be a list separated with spaces. Formats are stripped down to the most common ones:

		from: docbook, html, json, latex, markdown, markdown_github, markdown_mmd, markdown_phpextra, markdown_strict, mediawiki, mw, opml, rst, textile
		output: all the above +  asciidoc, beamer, docx (or doc), epub, epub3, fb2, html5, odt, opendocument (or opendoc), pdf, plain, rtf, slides (or slide)

		 All "markdown"s can be entered as "md". So: markdown -> md; markdown_github -> md_github; etc
		 
		 And these markdown extensions are automatically added: 'link_attributes', 'hard_line_breaks'

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

	admonitions with my own markup 

	[class/type:optional title]
	  * markdown
	  * super
	  * content

    The "class/type" would be something like "information", "danger", "tip", "hint", "hungry", "duck", "yay" ...
	  
	You can also include a tag for toc ([TOC]) to have that file with a toc instead of remembering to enter --toc. (It just adds it automatically after searching the file, no magic here)
	
	Book converts all files to HTML and adds navigation links. Useful to make simple documentation. 
	
	If you use markdown you have more goodies: create your own index (as index.md) and have "wikiLinks". Wikilinks can be in any file as [:filename][optional title] where filename can have extension or not, and if you don't include a title, it finds the file title. The order of the files in the index affect the sidebar navigation. With this you can create cooler documentation or use it as a poor's man/simple wiki.

	If you wish to create your own template for book, pandy adds some variables for you to include: 

	  * ``side_navigation`` the sidebar navigation 
	  * ``book_navigation`` book navigation (previous/index/next)
	  * ``project-index`` link to index. Useful if you have subfolders 
	  * ``project-title`` Index title. Useful if you create your own index with a title
	
	If you don't like setting the options in the CLI, or having a script, you can create your configuration in a key=value file (like ini). Example: myconfiguration.ini contains:

	PANDOC_DATA_DIR = C:\Program Files\Pandoc
	TEMPLATE = github.html
	HIGHLIGHT = zenburn

	Specify the configuration file with --config (the extension doesn't matter, and INI headers are ignored. Don't worry) or just have a settings.ini where you run pandy.

"""

import sys
import argparse
import subprocess
import os
import codecs
import re

drinkSoup = False
try:
	from bs4 import BeautifulSoup
	drinkSoup = True 
except ImportError:
	# Dale, hacemela mas dificil
	pass


# ==============================
# ==== info & pandoc config ====
# ==============================

__version__ = "2.0.1"
_MY_USAGE = ''' %(prog)s [source] [options] '''
# must replace the lists inside. This is just to have a bit of order.
_MY_DESCRIPTION = '''
 [format_from] can be 
 {{ _FORMATS_BOTHWAYS }}

 All "markdown"s can be entered as "md". So: markdown -> md; markdown_github -> md_github; etc 

   
 [format_to] include above formats plus: 
 {{ _FORMATS_OUTPUT }}

 Choose the slide format with --slides. 
'''

# pandoc's formats. Filtered to remove some that will never be used (by me)
# Includes some synonyms
_FORMATS_BOTHWAYS = [
	'docbook', 'html', 'json', 'latex',
	'markdown', "md",
	'markdown_github', "md_github",
	'markdown_mmd', "md_mmd",
	'markdown_phpextra', "md_phpextra",
	'markdown_strict', "md_strict",
	'mediawiki', "mw", 'opml', 'rst', 'textile',
	]
_FORMATS_OUTPUT   = [
	'odt', 'opendocument', 'opendoc', 'docx', 'doc',
	'asciidoc', 'beamer', 'plain', 'rtf', 
	'epub', 'epub3', 'fb2', 'html5',
	'pdf', #[*for pdf output, use latex or beamer and -o FILENAME.pdf] 
	"slides", "slide", #options slides in another list
	]

_HIGHLIGHT_OPTIONS = ('pygments', 'kate', 'monochrome', 'espresso', 'zenburn',
                     'haddock', 'tango')
_SLIDES_OPTIONS    = ('dzslides', 'slidy', 'reveal', 'slideous', 's5')

_COMMANDS_COMPLETE = {
	'HIGHLIGHT_NO' : "--no-highlight",
	'TOC'          : "--toc",
	'SELF_CONTAINED' : "--self-contained",
	'EMAIL_HIDE'   : "--email-obfuscation=references",
	'CSS'          : "--css=",
	'TOC_DEPTH'    : "--toc-depth=" ,
	'SECTIONS'     : "--section-divs",
	'BIBLIOGRAPHY' : "--bibliography=",
	'TEMPLATE'     : "--template=",
	'PANDOC_DATA_DIR' : "--data-dir=",
	'HIGHLIGHT'    : "--highlight-style=",
	'FILE_HEADER'  : "--include-before-body=",
	'FILE_FOOTER'  : "--include-after-body=",
	'CSL'          : "--csl="
	}

EXTENSIONS_EXTRA  = ('link_attributes', 'hard_line_breaks')

# =======================
# ==== configuration ====
# =======================

DEFAULT_INI_NAME = "settings.ini"

_DEFAULT_CONFIG = {
	'PANDOC': 'pandoc', # pandoc path
	'PANDOC_DATA_DIR': "", # empty for default
	'TEMPLATE': '',
	'HIGHLIGHT': 'pygments',
	'HIGHLIGHT_NO': False,
	'SLIDES': 'dzslides', 
	'TEMPLATE_PANDY': False,
	
	'SOURCE': os.getcwd(),
	'OUTPUT_PATH': '',
	'OUTPUT_FLAT': False,
	'CONFIG_FILE' : DEFAULT_INI_NAME,
	
	'FORMAT_FROM': 'md',
	'FORMAT_TO': ['html'],
	
	'TOC': False,
	'TOC_DEPTH': 3,
	'SECTIONS': False,
	'SELF_CONTAINED': False,
	'CSS_EXTERNAL': '',
	'FILE_FOOTER': '',
	'FILE_HEADER': '',
	
	'MERGE': False,
	'BOOK': False,
	'FILE_INDEX': '',
	'USE_NAV': True, 
	'NAV_TITLE': False,  #book, use title navigation
	'NAV_SIDEBAR': True,  #book, sidebar with titles
	'NAV_SIDEBAR_TOC': True, #book, have current toc in sidebar

	'EMAIL_HIDE': False, # e-mail obfuscation (default none, true = references)
	'BIBLIOGRAPHY': '',
	'HTML_VER': 'html5', # Output html5 instead of html4 (html)
	'TOC_TAG': '[TOC]',
	}

# for wiki links mostly
ACCEPTED_MD_EXTENSIONS = ('md', 'txt', 'mdown', 'markdown')

HTML_CSS = """
    *           { margin: 0; padding: 0; }
    html, body  { color: black; }

    body {
        padding: 0px 25px; 
        margin: -1px auto;
        font: 14px helvetica, "Segoe UI", arial, freesans, sans-serif; 
        line-height: 1.8em;
        color: #3A3A3A;
        background-color: #f2f2f2;
    }

    p { margin: 1em 0; }

    a {text-decoration: none; border-bottom: 1px dotted; color: #4183c4; }
    a:hover, a:active { color: #75A837; }

    blockquote {
        margin: 14px 0; padding: 0.7em 11px;
        color: #555;
        font-style: italic;
        border-left: 10px solid #838383;
    }

    img {
        display:          block;
        background-color: #F3F3F2;
        border:           1px solid #D9D9D7;
        margin:           0px auto;   padding: 5px;
    }

    ins { color:#008000; }
    del { color:#ACACAC; }

    hr { border: 0; height: 1px; background: #333; }

    sup, sub, a.footnote-ref {
        height:         0;
        line-height:    1;
        vertical-align: super;
        position:       relative;
    }

    sub             {vertical-align: sub; top: -1px; }
    a.footnote-ref { font-size: 1em; }

    abbr { border-bottom: 1px dotted }

    h1,h2,h3,h4,h5,h6 { margin: 1.5em 0px 1em; padding: 4px 0; border-bottom: 1px solid #e0e0e0; }
    h1 { font-size: 2em;}
    h2 { font-size: 1.571em; }
    h3 { font-size: 1.429em; }
    h4 { font-size: 1.286em; }
    h5 { font-size: 1.143em; color: #4d4d4d;}
    h6 { font-size: 1em; color: #666; }
    h1.title { margin:0 }

    ul, ol  { margin: 21px 0 0px 30px; list-style-position: outside; }
    li      { margin: 7px 0 }
    ul      { list-style-type: disc; }
    ol      { list-style-type: decimal-leading-zero; }

    dl, dt, dd { margin: 0; }
    dl { padding: 0px 1em 10px; }
    dt { padding: 5px 0 5px; font-weight: bold; line-height: normal; }
    dd { padding: 0 10px 20px 3em; font-style: italic; }

    /* based on http://icant.co.uk/csstablegallery/tables/50.php (Blaugrana). */
    table { 
        padding: 0; margin: 0 auto 2em auto;
        border-spacing: 0; border-collapse: collapse;
        min-width: 50%;
        border: 1px solid;
    }
    th, caption {color: #444; font-weight: bold;text-align: center;}
    td, th {padding: .6em .4em; vertical-align: top; border: 1px solid #779; }
    th, tfoot td {border: 1px solid #361; background: #e0e5cf; }
    /*tr { background:#f5f5f5 }*/
    tr { background: #cfe0e5 }
    tr.odd { background: #e5cfe0 }
    tr.odd td, tr.odd th { border-color: #977; }

    pre, code {
        border:         1px solid #ccc;
        font-size:      12px;
        font-family:    Consolas, "Liberation Mono", Courier, monospace;
        background-color:#eee;
    }

    pre  { margin: 5px 0 0; padding: 6px 5px; white-space: pre; overflow: auto; }
    code { margin: 0 2px; padding: 2px 5px; /*white-space: nowrap;*/ }

    pre code {border: none }

    #TOC    { margin-top: 30px; background-color: #e5efdf; border: 1px solid #cedec4;}
    #TOC a  { margin: 0 15px !important; }
    #TOC ul {
        margin: 1px 0 0 15px !important;    
        padding: 0 0 0 1px !important;
        display: block;
        line-height: 20px;
        list-style: none;
    }
    #TOC ul li  { border-left: 1px solid; position: relative; margin:0 !important; }
    #TOC ul > #TOC li { padding-bottom: 10px !important;}
    #TOC ul li:before {
        content: '';
        width: 14px;
        position: absolute;
        border-bottom: 1px solid;
        left: 0px;
        top: 10px;
    }
    #TOC ul li:last-child {border-left:none;}
    #TOC ul li:last-child:before {border-left:1px solid; height: 10px; margin-top:-10px !important; }
    #TOC ul li, #TOC ul li:before, #TOC ul li:last-child:before {border-color: #7A7A7A; }
    .admonition p   { margin: 0.5em 1em 0.5em 1em; padding: 0;}
    .admonition pre { margin: 0.4em 1em 0.4em 1em;}
    .admonition ul, .admonition ol { margin: 0.1em 0.5em 0.5em 3em;   padding: 0;}

    .admonition {
        margin: 2em; padding: 0;
        font-size:        0.9em;
        border:           1px solid #c2c2c2;
        background-color: #e9e9e9;
    }

    .admonition p.admonition-title {
        margin:     0;
        padding:    0.1em 0 0.1em 0.5em;
        font-size:  1.1em;
        font-weight: bold;
        color:      #fff;
        border-bottom: 1px solid #c2c2c2;
        background-color: #999; 
    }

    .admonition.error, .admonition.caution, .admonition.danger
    {border-color: #900000; background-color: #ffe9e9;}

    .error p.admonition-title, .caution p.admonition-title, .danger p.admonition-title
    {background-color: #b04040; border-color: #900000;}

    .admonition.hint
    {background-color: #ECFAE3;  border-color: #609060;}

    .hint p.admonition-title
    {background-color: #70A070; border-color: #609060;}

    .admonition.note, .admonition.tip, .admonition.warning
    {border-color:#e2ba54; background-color:#fcfce1;}

    .note p.admonition-title, .tip p.admonition-title, .warning p.admonition-title
    {background-color: #f1d170; border-color:#e2ba54;}

    .admonition.info, .admonition.attention, .admonition.important
    {background-color: #e8edfc; border-color: #94A7BF;}

    .info p.admonition-title, .attention p.admonition-title, .important p.admonition-title
    {background-color: #7088A0; border-color: #94A7BF;}

    mark {background-color: #e7d600; padding: 0.2em;}

    .bookbar {padding: 10px; border: 1px solid #ccc; border-width: 1px 0; overflow: auto}
    .bookbar li {display: inline-block;}
    .bookbar ul {margin: 0}
    .breadcrumbs {float: left;}
    .breadcrumbs li:after {content: "\\0BB \\020" /* » */; padding-left: 0.6em;}
    .breadcrumbs li:last-child:after {content: ""}
    .booknav {float:right;}
    .booknav li {padding: 0 1.0em;}

    #content {display: table-row;}

    #sidebar {display: table-cell; width: 240px; font-size: small; background-color: #eeeeee;}
    #sidebar ul ul {margin: 5px 0px 0px 5px;}
    #sidebar ul ul li {margin-left: 10px;}
    #sidebar ul {list-style: decimal;}
    #sidebar ul ul {list-style: lower-alpha;}
    #sidebar ul ul ul {list-style: lower-roman;}
    #sidebar li.active > a {font-weight: bold}

    #content-body {padding: 20px; font-size: 16px;}

    #footer {padding: 10px; font-size: small; }
"""

HTML_BEFORE = """
	<div id="wrapper">
	{bookbar}

	<div id="content">

	<div id="sidebar">
	{side_navigation}
	</div>

	<div id="content-body">
"""

HTML_BOOKBAR = """
	<div class="bookbar">
		<ul class="breadcrumbs">
			<li>{projectindex}</li>
			<li class="active">{pagetitle}</li>
		</ul>

		{book_navigation}
	</div>
"""

HTML_AFTER = """
	</div> <!-- contentbody -->
	</div> <!-- content -->

	{bookbar}

	<div id="footer">
	</div>

	</div> <!-- wrapper -->
"""


# =======================
# == methods: system ====
# =======================

def path_mkdir(path):
	""" make tree dirs from path """

	try:
		os.makedirs(path)
	except OSError:
		pass

def path_get(thefile):
	""" Get path from file """

	return os.path.dirname(thefile)

def path_getFilename(file_path):
	""" Get filename from path"""

	return os.path.basename(file_path)

def path_delExtension(file_path):
	""" Delete the extension from path """

	path, _ = os.path.splitext(file_path)
	return path

def path_lastDir(path):
	""" Parent folder name """

	return os.path.split(path)[1]

def path_relative_to(this_path, root, index=False):
	"""Gets the relative path of this_path from root """

	if index:
		return os.path.relpath(this_path, root)
		
	# Delete first "folder" (..\)
	return os.path.relpath(this_path, root)[3:]

def save(path, text):
	""" Saves file using it properties"""

	cmd = cmd_open_write(path, 'w')

	with cmd as outputFile:
		outputFile.write(text)

def files_get(path, only_exts=None, exclude_files=None):
	""" Get a list of files in dir. Returns list 

	:param:only_exts   tuple to include only selected extensions (mainly for html pages 
		               saved locally (which has folders > images ) )
	:param:exclude_files tuple to exclude files, mainly to exclude custom index 
	""" 

	theFiles = list()

	if os.path.isfile(path):
		if os.path.exists(path):
			theFiles.append(path)
	else:
		for root, subFolders, files in os.walk(path):
			for filename in files:
				filePath = os.path.join(root, filename)

				if os.path.exists(filePath):
					if only_exts and filePath.endswith(only_exts):
						theFiles.append(filePath)
					else:
						if exclude_files and filePath in exclude_files:
							continue
						theFiles.append(filePath)

	return theFiles	

def files_list(path, only_exts=None, exclude_files=None):
	"""Gets the files from the .list (returns list). If not a .list, calls files_get"""

	if path.endswith(".list"):
		fileList = list()
		cmd      = cmd_open_write(path, 'r')
			
		with cmd as listFiles:
			for line in listFiles:
				line = line.strip()

				if os.path.exists(line):
					fileList.append(line)
		return fileList
	
	return files_get(path, only_exts, exclude_files)

def cmd_open_write(path, mode):
	""" Create the open/write command according to python version 
	mode is: 'r' for read and 'w' for write
	"""

	return codecs.open(path, mode, encoding='utf-8-sig')

def cmd_open_file(path):
	""" Opens file and returns text """

	with cmd_open_write(path, 'r') as readme:
		return readme.read()

def get_ini(filepath, keys_upper=False, space_list=None):
	"""Read ini without headers (ignores them). Return dict

	:keys_upper: if key (options) are returned as uppercase. 
	:space_list  a list/tuple of keys that (the value) is a space separated list
	"""

	# lets be nice and convert to lowercase
	[z.lower() for z in space_list]

	import configparser
	config = configparser.ConfigParser(empty_lines_in_values=False)

	# config parser doesnt parse ini without section, fake it
	dummy_section_name = "sexysettings"
	dummy_file = "[" + dummy_section_name + "]\n"
	
	with open(filepath) as dumb:
	    dummy_file += dumb.read()

	config.read_string(dummy_file, source=filepath)
	
	config = config[dummy_section_name]

	tmp_options  = dict()
	for key, value in list(config.items()):

		#Convert booleans, ints, lists
		if value.isnumeric():
			value = int(value)
		elif value.startswith("[") and value.endswith("]"):
			value = value[1:len(value)-1]
			value = value.split(",")
		else:
			# booleans can accept true/false, yes/no
			try:
				config.getboolean(key)
			except ValueError:
				pass
			else:
				value = config.getboolean(key)

		if key.lower() in space_list:
			# must do checking for string only
			value = value.split()

		if keys_upper:
			key = key.upper()
		
		tmp_options[key] = value	

	return tmp_options


# =========================
# == methods: commands ====
# =========================

def run_subprocess(command, output=False, text=None):
	""" run the cmd (list) 
	normally -> check_call
	if output activated: returns the output to string -> check_output
	if also text: to interact -> Popen (encodes to utf-8)

	Added shell=True because Windows/Python is crazy sometimes and cant find .exe in path. 
	Thank you <http://stackoverflow.com/questions/3022013>
	"""

	if not output:
		return subprocess.check_call(command, stderr=subprocess.STDOUT, shell=True)
	elif not text:
		return subprocess.check_output(command, shell=True)
	else:
		text = text.encode('utf-8')
		tmp  = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
		result = tmp.communicate(text)[0] # send stdin 
		return result

def translate_synonyms(word):
	"""Translate the synonyms to complete words"""

	if word == "md" or word.startswith("md"):
		word = word.replace("md", "markdown")
		return word

	if word == 'slide':
		return "slides"

	if word == 'mw':
		return "mediawiki"

	if word == 'doc':
		return 'docx'

	if word == 'opendoc':
		return 'opendocument'

	return word

def translate_argsPandoc(myarg, value):
	""" translate my arguments to pandoc's """

	if myarg in _COMMANDS_COMPLETE and value:
		pandoc_arg = _COMMANDS_COMPLETE[myarg]

		if isinstance(value, bool):
			return [pandoc_arg]
		else:
			return [pandoc_arg + str(value)]

	return ""

def msg_cli_yesno(msg):
	"""Message for cli when answering y/n questions. 
	msg contains the message without the "Continue (y/n)"
	Returns boolean 
	"""

	answer = ""
	while (not answer.lower() == 'y' and not answer.lower() == 'n'):
		answer = input(msg + " Continue? (y/n) ")

	if answer == 'y':
		return True 
	return False

def check_synonyms(format_from, format_to):
	"""Translate synonyms, return modified values """

	format_from = translate_synonyms(format_from)

	i = 0
	while i < len(format_to):
		format_to[i] = translate_synonyms(format_to[i])
		i += 1

	format_to = list(set(format_to)) # no duplicates

	return format_from, format_to

# ================================
# == methods: special parsing ====
# ================================

def if_special_elements(text, toc_tag):
	"""read text (as list) and process trough specials 
	(admonitions, abbreviations, TOC tag, internallinks)
	returns: text (as list) and hasTOC (bool)
	"""
	
	hasTOC, text = find_TOCinFile(text, toc_tag)
	text = parse_admonitions(text)
	text = parse_abbreviations(text)
	text = parse_internalLinks(text)

	return text, hasTOC

def parse_abbreviations(text):
	""" Find if file has abbreviations, if it does: parse as HTML. 
	text: list (as just opened)
	returns parsed text list 

	abbreviations format as PHP Markdown Extra:

    Some text with an ABBR and a REF. Ignore REFERENCE and ref.
    *[ABBR]: Abbreviation
    *[REF]: Abbreviation Reference

    should be: Some text with an <abbr title="Abbreviation">ABBR</abbr> and a <abbr 
            title="Abbreviation Reference">REF</abbr>. Ignore REFERENCE and ref.
	"""

	p = re.compile(r'\*\[(\w+)\]:\s+(\S.+)')

	newtext = []
	defs = {}

	for line in text:
		m = p.match(line)
		if m:
			abrr = m.group(1).strip()
			title = m.group(2).strip()
			defs[abrr] = title
		else:
			newtext.append(line)

	newtext = "<<<<SPLITMEOVERHERE>>>>".join(newtext)
	for key, value in defs.items():
		newtext = re.sub(r'\s'+key+r'([\s\.,:;\?!]{1}?)', 
			             r' <abbr title="'+value+'">'+key+'</abbr>\\1', 
			             newtext)

	newtext = newtext.split("<<<<SPLITMEOVERHERE>>>>")

	return newtext

def parse_admonitions(text):
	""" Find and parse my admonitions. 
	Input text: as list (just after open)
	returns parsed text as list

	Syntax:
	[class/type:optional title]
      * markdown
      * super
      * content
    
	would be translated as div:
	<div class="admonition class/type">
	<p class="admonition-title"> Optional title </p>
      * markdown
      * super
      * content
	</div>
    """

	new_test = list()
	admon_start = False

	for line in text:
		tmp_line = line.rstrip()

		if tmp_line.count("[") == 1 and tmp_line.startswith("[") and tmp_line.endswith("]"):
			if admon_start:
				# close previous
				new_test.append("</div>")

			admon_start = True

			tmp_line = tmp_line[1:len(tmp_line)-1]
            
			if ":" in tmp_line:
				admon_type, admon_title = tmp_line.split(':')
			else:
				admon_type = tmp_line
				admon_title = None

			new_str = '<div class="admonition ' + admon_type + '">'
			new_test.append(new_str)

			if admon_title:
				new_test.append('<p class="admonition-title">' + admon_title + '</p>')

			continue 

		if (tmp_line.startswith("\t") or tmp_line.startswith ("  ") or not tmp_line) and admon_start:
			if tmp_line:
				#remove first set of whitespace
				if tmp_line.startswith("\t"):
					tmp_line = line.replace("\t", "", 1)
				else:
					tmp_line = re.sub(r'^\s{2,4}(.+)', '\\1', line)
			else:
				tmp_line = "\n"

			new_test.append(tmp_line)

		else:
			if admon_start:
				new_test.append("</div>")

			new_test.append(line)
			admon_start = False

	return new_test

def find_TOCinFile(text, placeholder, replace_with='<!-- TOCatized -->'):
	""" automatically check if text (as list) has the TOC tag. Replaces 
	placeholder with another string. Returns boolean and text (as list) 
	only for occurence
	"""

	for index in range(len(text)):
		if text[index].startswith(placeholder):
			text[index] = text[index].replace(placeholder, replace_with)
			return True, text 

	return False, text 

def parse_internalLinks(text):
	""" Process "internal links": [nicetitle](file.md) to [nicetitle](file.html)
	Markdown file opened before as list  
	return  text 
	No guessing of title

	ex: wikilinks
	"""

	extensions = "|".join(ACCEPTED_MD_EXTENSIONS)

	# harvest all links first 
	links = extractMdLinks(text, extension=extensions)

	for link in links:
		link_new = path_delExtension(link[1]) + ".html"
		title_new = link[0]

		link.append(title_new)
		link.append(link_new)

	# replace in file
	textNew = "<<<<SPLITMEOVERHERE>>>>".join(text)
	link_tpl = "[{title}]({link})"

	for link in links:
		find_me    = link_tpl.format(title=link[0], link=link[1])
		replace_me = link_tpl.format(title=link[2], link=link[3])

		textNew = textNew.replace(find_me, replace_me)

	return textNew.split("<<<<SPLITMEOVERHERE>>>>")

def parse_wikilinks(text, list_files=None, this_references=None):
	"""Parse wikilinks (reference links but inverted): [:filename][title]
	[:filename] can have extension or not.
	[title] is optional. If blank: searches title

	:text             text as list
	:list_files       dict. files: any key and holding (minimum):
	                      path_input, title, output ("future path")
	:this_references  dict. use this as reference list (do not search in files)
	                    key: ref id. ex. filenames, can be joined (search w/ "in")
	                    value['output']: output path ("future path"/html)
	                    value['title']: file future title 

	return processed text (list) and references (list) of the file
	"""

	# prefere this_references 
	if list_files and this_references:
		list_files = None 

	extensions = "|".join(ACCEPTED_MD_EXTENSIONS)
	links = extractMdLinks(text, extension=extensions, style='wiki')

	references = list()
	ref_tpl    = "[{thefile}]: {future_html}"
	new_links  = list() #filename, title_old and title_new. Later text replacement

	search_in_prop = False
	listing = this_references
	if list_files is not None:
		listing = list_files
		search_in_prop = True 

	for link in links:
		filename    = link[0]
		title_old   = link[1]
		future_path = ""
		title_new   = title_old

		for key in listing:
			look_here = key
			if search_in_prop:
				look_here = listing[key]['path_input']

			if filename in look_here:
				future_path = listing[key]['output']
					
				if not title_old:
					title_new = listing[key]['title']

				# create ref
				tmp = ref_tpl.format(thefile=filename, future_html=future_path)
				if not tmp in references:
					references.append(tmp)

				tmp = [filename, title_old, title_new]
				if not tmp in new_links:
					new_links.append([filename, title_old, title_new])

				break 				

	# replace in text 
	newtext     = "<<<<SPLITMEOVERHERE>>>>".join(text)
	search_tpl  = "[:{filename}][{title}]"
	replace_tpl = "[{title}][{filename}]"

	for link in new_links:
		filename  = link[0]
		title_old = link[1]
		title_new = link[2]

		newtext = newtext.replace(
			search_tpl.format(filename=filename, title=title_old), 
			replace_tpl.format(filename=filename, title=title_new))

	newtext = newtext.split("<<<<SPLITMEOVERHERE>>>>")

	return newtext, references

def extractMdLinks(text, extension="md", style='inline'):
	"""Extract markdown links in text with extension. 
	:text list 
	:extension the allowed extension
	:referencestyle    for [][] links 
	:return a nested list. 
	             normal: holder(title, link)
	             reference: holder(title, id_link)
	:style      style of links. Options: inline | reference | wiki | all or both
	"""

	list_links = list()

	expr_normal    = "\[(.+?)?\]\((.+?\.(" + extension + "))\)"
	expr_wiki = "\[:(.+?[\.(" + extension + ")]?)\]\[(|.+?)\]"
	expr_reference = "\[(.+?[\.(" + extension + ")]?)\]\[(|.+?)\]"
	# all = inline + reference
	expr_all = "\[\:?(.+?[\.(" + extension + ")]?)\](?:\[(|.+?)\]|\((.+?[\.(" + extension + ")]?)\))"

	if style == "reference":
		expr = r'' + expr_reference
	elif style == "wiki":
		expr = r'' + expr_wiki
	elif style == "inline":
		expr = r'' + expr_normal
	elif style in ('all', 'both'):
		expr = r'' + expr_all

	for line in text:
		matches = re.findall(expr, line)
		for m in matches:
			title = m[0].strip()
			if not style == 'all':
				link  = m[1].strip()
			else:
				link  = m[2].strip()

			if [title, link] not in list_links:
				list_links.append([title, link])

	return list_links

def findTitleMd(filepath=None, text_lines=None):
	"""Find title in markdown file. All posibilities (% , title: # and =====)
	:filepath   path to open file 
	:text_lines   text in list
	"""

	if filepath:
		with cmd_open_write(filepath, 'r') as tmp:
			the_text = tmp.readlines()
	if text_lines:
		the_text = text_lines

	max_meta = 30 #max lines to look for metadata title

	for number, line in enumerate(the_text):
		if line.startswith("% "):
			return line[1:].strip()
		
		if line.startswith("title: "):
			tmp = line[7:]
			if tmp.startswith(("'", '"')) and tmp.endswith(("'", '"')):
				tmp = tmp[1:len(tmp) - 1]
			return tmp.strip()

		if number == max_meta:
			break 

	# nothing found. I'm doing extra work for you, ok? Next time use metadata
	for number, line in enumerate(the_text):
		if line.startswith("# "):
			return line[2:]
		if line.startswith("======="):
			return the_text[number - 1].strip()

	return False

# =============================
# == methods: Args/options ====
# =============================

class InputExist(argparse.Action):
	""" Custom action for args, check if input exists """

	def __call__(self, parser, namespace, values, option_string=None):
		if not os.path.exists(values):
			parser.error('Source file or folder doesn\'t exist')

		setattr(namespace, self.dest, values)

def get_args():
	""" Args parsing and translation to nice configs"""

	parser = argparse.ArgumentParser(add_help=False, usage=_MY_USAGE 
		        , description=help_replaceStringFormats(_MY_DESCRIPTION, 
		        	            ['{{ _FORMATS_OUTPUT }}', '{{ _FORMATS_BOTHWAYS }}'])
		        , formatter_class=argparse.RawTextHelpFormatter) 

	required = parser.add_argument_group(' Required')
	required.add_argument("source", action=InputExist, help="file, folder, .list or config file (.ini)")
	
	option_file = parser.add_argument_group(' Options:\n\n file related')
	option_file.add_argument("--from", '-f', metavar="", choices= _FORMATS_BOTHWAYS, help="Convert from this")
	option_file.add_argument("--to", '-t', nargs='*', choices= _FORMATS_BOTHWAYS + _FORMATS_OUTPUT, 
		    metavar="", help="Convert to this (can be a space separated list)")
	option_file.add_argument("--output", "-o", help="Output folder", metavar="FOLDER")
	option_file.add_argument("--flat", action='store_true', help="Don't keep folder structure")
	option_file.add_argument("--self", help="self contained file", action='store_true')	
	option_file.add_argument("--header", metavar="FILE", 
		    help="Header file. Included as it is (raw, verbatim)")
	option_file.add_argument("--footer", metavar="FILE", 
		    help="Footer file. Included as it is (raw, verbatim)")
	option_file.add_argument("--html4", action="store_true", 
		    help="Use html4 output instead of html5")
	option_file.add_argument("--slides", choices=_SLIDES_OPTIONS, metavar="",
		    help="Slides format. Options: " + ", ".join(_SLIDES_OPTIONS) + ". Default: %(default)s",  
		    default=_DEFAULT_CONFIG['SLIDES'])
	option_file.add_argument("--bib", help="Use bibliography file", metavar="FILE")
	option_file.add_argument("--csl", help="CSL file", metavar="FILE")

	exclusive = option_file.add_mutually_exclusive_group()
	exclusive.add_argument("--merge", "-m", action="store_true", help="Merge files")
	exclusive.add_argument("--book", "-b",  action="store_true", 
		    help="Make a book with navigation (next/prev) and index")

	style = parser.add_argument_group(' styling')
	style.add_argument("--css", help="External CSS", metavar="FILE")

	style.add_argument("--highlight", choices=_HIGHLIGHT_OPTIONS,  metavar="",
		    default=_DEFAULT_CONFIG['HIGHLIGHT'], 
		    help="Highlight style. Options: " + ", ".join(_HIGHLIGHT_OPTIONS) + ". Default: %(default)s")
	style.add_argument("--highlight-no", help="No highlight", action='store_true')
	style.add_argument("--tpl", metavar="FILE",
		    help="Template file. Can enter 'default' for pandoc's default.")
	style.add_argument("--tpl-pandy", help="Pandy's embebed template: simple and not that ugly", 
		                              action='store_true')

	other = parser.add_argument_group(' other')
	other.add_argument("--toc", help="include TOC", action='store_true')
	other.add_argument("--depth", type=int, choices=[1, 2, 3, 4, 5, 6], metavar="",
		    help="TOC depth. Choices: 1, 2, 3, 4, 5, 6. Default: %(default)s", 
		    default=_DEFAULT_CONFIG['TOC_DEPTH'])
	other.add_argument("--hide", action='store_true', 
		    help="e-mail obfuscation (default none, true = references)")
	other.add_argument("--sections", action='store_true', 
		    help="Wrap sections in <sections>, attach identifiers instead of titles")
	other.add_argument("--config", metavar="FILE", 
		    help="Use a configuration file (option=key values)")

	other.add_argument("--no-nav", "-nn", action="store_true", 
		    help="(For book) disable book navigation")
	other.add_argument("--nav-title", "-nt", action="store_true", 
		    help="(For book) use titles in book navigation")
	other.add_argument("--no-side", "-ns", action="store_true", 
		    help="(For book) Disable sidebar navigation")
	other.add_argument("--no-side-toc", "-nst", action="store_true", 
		    help="(For book) disable TOC in sidebar (keep in doc)")

	pandoc = parser.add_argument_group(' Pandoc')
	pandoc.add_argument("--pandoc",   default=_DEFAULT_CONFIG['PANDOC'], 
		    help="Pandoc path. Default: %(default)s")
	pandoc.add_argument("--data-dir", default="", help="Data directory", metavar="FOLDER")

	nocateg = parser.add_argument_group(' Last but not least')
	nocateg.add_argument("--help", "-h", help="show this help message and exit", action="help") 
	nocateg.add_argument('--version', action='version', version='%(prog)s ' + __version__)

	arg_dict = vars(parser.parse_args())
	if arg_dict['to'] is not None:
		arg_dict['to'] = set(arg_dict['to'])

	#convert those ugly names to the nice ones
	argsToSettings = {
		'output': 'OUTPUT_PATH',
		'flat': 'OUTPUT_FLAT',
		'self': 'SELF_CONTAINED',
		'css': 'CSS_EXTERNAL',
		'tpl': 'TEMPLATE',
		'hide': 'EMAIL_HIDE',
		'bib': 'BIBLIOGRAPHY',
		'nav_title': 'NAV_TITLE',
		'data_dir': 'PANDOC_DATA_DIR',
		'html4': 'HTML_VER',
		'header': 'FILE_HEADER',
		'footer': 'FILE_FOOTER',
		'depth' : 'TOC_DEPTH',
		'no_side' : 'NAV_SIDEBAR',
		'no_nav' : 'USE_NAV',
		'config' : 'CONFIG_FILE',
		'no_side_toc' : 'NAV_SIDEBAR_TOC',
		'from': 'FORMAT_FROM',
		'to': 'FORMAT_TO',
		'tpl_pandy': "TEMPLATE_PANDY",

		#convert to upper
		'pandoc': 'PANDOC',
		'highlight': 'HIGHLIGHT',
		'slides': 'SLIDES',
		'source': 'SOURCE',
		'sections': 'SECTIONS',
		'toc': 'TOC',
		'merge': 'MERGE',
		'book': 'BOOK',
		'highlight_no': 'HIGHLIGHT_NO',
		'csl': "CSL",
		}

	settings_args = dict()

	def toggleBool(val):
		if val:
			return False 
		return True 

	# transfer & translate
	for key, val in arg_dict.items():
		if key == "html4":
			val = 'html' if val else 'html5'

		if key in ('no_nav', 'no_side_toc', 'no_side'):
			val = toggleBool(val)

		settings_args[argsToSettings[key]] = val 

	if settings_args['SOURCE'] == ".":
		settings_args['SOURCE'] = os.getcwd()

	return settings_args

def prepare_args(arg_dict):
	""" Prepares the args to a nice config dictionary. Also reads .ini """
	
	settings_final = dict(_DEFAULT_CONFIG)

	if arg_dict['SOURCE'].endswith(".ini"):
		settings_final['CONFIG_FILE'] = arg_dict['SOURCE']
		del arg_dict['SOURCE']

	# complete missing options. default <- .ini <- args 
	# read ini and replace default
	if os.path.exists(settings_final['CONFIG_FILE']):
		settings_file = get_ini(settings_final['CONFIG_FILE'], True, space_list=('format_to'))
		settings_final.update(settings_file)

	#remove config option (just because)
	del settings_final['CONFIG_FILE']

	# now args
	# remove default values from arg_dic -> not overwrite
	for key, val in _DEFAULT_CONFIG.items():
		if key in arg_dict and arg_dict[key] == val:
			del arg_dict[key]

	#Take care of specials
	for key, val in list(arg_dict.items()):
		if val is None:
			del arg_dict[key]

	settings_final.update(arg_dict)

	# Check option belonging, replace special keys, etc 
	# if pdf, warn that needs latex 
	if "pdf" in settings_final['FORMAT_TO']:
		answer = msg_cli_yesno("  To convert to PDF needs LaTeX installed (and in PATH)")
		if not answer:
			exit()

	if settings_final['TEMPLATE'] == "NONE":
		settings_final['TEMPLATE'] = ""

	if settings_final['SOURCE'].endswith(".list") and not settings_final['OUTPUT_FLAT']:
		msg("Keeping folder structure with .list not supported. Skipping option")
		settings_final['OUTPUT_FLAT'] = True 

	#Special belonging if not book, just to clean up
	if not settings_final['BOOK']:
		if (settings_final['NAV_TITLE'] or settings_final['NAV_SIDEBAR'] 
			or settings_final['USE_NAV']):

			settings_final['NAV_TITLE']   = False
			settings_final['NAV_SIDEBAR'] = False
			settings_final['USE_NAV']     = False

	if settings_final['TEMPLATE_PANDY'] and settings_final['TEMPLATE']:
		msg("How cute, but you have to specify only one. Disabling pandy's")
		settings_final['TEMPLATE_PANDY'] = False 

	return settings_final

# ============
# == Misc ====
# ============

def getTOC(html):
	"""Returns the TOC list as str (splitting from <body>) """

	if drinkSoup:
		soup = BeautifulSoup(html)
		soup = soup.body

		toc = soup.find(id='TOC')
		if toc:
			toc = toc.extract()
			toc = toc.ul
			return str(toc)

		return ''

	else:		
		text = html.split("<body>")[1]
		text = text.split("</body>")[0]

		if not '<div id="TOC">' in text:
			return ''

		text = text.split('<div id="TOC">')[1]
		text_parts = text.split('</div>')
		toc = text_parts[0]
		toc = toc.splitlines()
		toc = [line for line in toc if line]
		#toc = toc[1:-1] # remove first <ul> and last </ul>
		return "".join(toc)

def orderListFromList(orderthis, fromthis, bythiscol=None):
	"""Order a list, based on another by value. 

	:orderthis    list to be ordered 
	:fromthis     new order list 
	:bythiscol    "column" number to order by this value set 
	"""

	tmp_list = list()

	for new_order in fromthis:
		for item in orderthis:
			checkthis = new_order
			if bythiscol is not None:
				checkthis = new_order[bythiscol]

			#we trust the user that will be no files with same name
			if checkthis in item:
				tmp_list.append(item)
				break 

	return tmp_list

def help_replaceStringFormats(string, placeholders):
	"""Replaces placeholders in string, with _FORMATS_BOTHWAYS and _FORMATS_OUTPUT
	
	string      : complete string 
	placeholders: list of placeholders; what to replace -> converts to list to join

	returns processed string 
	"""

	for placeholder in placeholders:
		tmp = ""
		# get the list name
		the_choosen_one = placeholder[3:len(placeholder) - 3] 

		if the_choosen_one == "_FORMATS_OUTPUT":
			the_list = _FORMATS_OUTPUT
		else:
			the_list = _FORMATS_BOTHWAYS

		is_synom = False
		
		for item in the_list:

			if the_choosen_one == "_FORMATS_OUTPUT":
				is_synom = True if item in ["doc", "opendoc", "slide"] else False 
			else:
				if item.startswith("md"):
					continue 

				is_synom = True if item == 'md' else False 

			if is_synom:
				tmp += " (or " + item + ")"
			else:
				tmp += ", " + item

		tmp = tmp[2:] # delete fist ", "
		string = string.replace(placeholder, tmp)

	return string

def msg(message, indent=2):
	""" Because I always forget to include X spaces in the beginning 

	:message     string message
	:indent  amount of spaces
	"""

	print(" "*indent + message)

def builtintpl(html, book_nav='', sidebar='', projindex='', pagetitle=''):
	"""Custom/embebed template; using pandoc's default"""

	#plain splitting

	head_split = html.split("</head>")
	head = head_split[0]
	body = head_split[1]

	head_final = head + '<style type="text/css">' + HTML_CSS +  "</style>" + "</head>"

	bookbar = HTML_BOOKBAR.format(projectindex=projindex, pagetitle=pagetitle, 
		           book_navigation=book_nav)

	code_before = HTML_BEFORE.format(bookbar=bookbar, side_navigation=sidebar)
	code_after = HTML_AFTER.format(bookbar=bookbar)

	body_split = body.split('<body>')
	body = body_split[1]

	body_final = '<body>' + code_before + body 
	body_split = body_final.split('</body>')
	body = body_split[0]
	body_final = body + code_after + '</body>' + body_split[1]

	return head_final + body_final


# ==============
# == Pandy! ====
# ==============

class Pandy(object):
	"""Handles the parsing and related """

	def __init__(self, config_dict):
		""" Preparation, config_dict must been checked and translated before """

		self.settings        = config_dict
		self.input           = config_dict['SOURCE']
		self.output          = config_dict['OUTPUT_PATH']
		self.format_from     = config_dict['FORMAT_FROM']
		self.format_to       = config_dict['FORMAT_TO']
		self.files           = []
		self.command         = []
		self.db_files        = dict()
		self.references_list = dict()
		self.references_all  = ""

		exts = tuple()
		if self.format_from == "html":
			exts = (".html", ".htm")

		self.files = files_list(self.input, only_exts=exts, exclude_files=[DEFAULT_INI_NAME])

		# find index. file
		i = 0
		total = len(self.files)
		while i < total:
			if "index." in self.files[i]:
				self.settings['FILE_INDEX'] = self.files[i]
				del self.files[i]
				break
			i += 1

		self.format_from, self.format_to = check_synonyms(self.format_from, self.format_to)

		# make base pandoc command
		self.command.append(self.settings['PANDOC'])
		self.command += self._cmdFromToOut('f', self.format_from)
		self.command.append('--standalone')  # complete html --standalone

		# Exclude: do not treat right now or already done
		exclude = ("FORMAT_TO", "FORMAT_FROM", "SOURCE", "OUTPUT_PATH", "MERGE",
			"OUTPUT_FLAT", "SLIDES", "BOOK", "HTML_VER", "PANDOC", "FILE_INDEX")

		# Add the options
		for key, val in self.settings.items():
			if key in exclude:
				continue
			self.command += translate_argsPandoc(key, val)
	
		# and run!
		self.run()

	def _cmdFromToOut(self, way, markup, outputpath=None):
		""" Create from/to/output (way param) command. returns the command (list)
		way is a char string: f, t, o 
		"""

		makeme = ["-" + way]

		if way in ['f', 't']:
			if markup == 'markdown':
				extensions = "+".join(EXTENSIONS_EXTRA)
				makeme += ["markdown+" + extensions]

			elif markup == "slides":
				makeme.append(self.settings['SLIDES'])

			elif markup == 'html' and way == 't':
				makeme.append(self.settings['HTML_VER'])
			else:
				makeme.append(markup)
		
		else:
			# complete extension
			if markup not in ['html', 'slides', 'markdown']:
				ext = markup
			else:
				if markup == "markdown":
					ext = "md"
				else:
					ext = "html"

			complete_path = outputpath + "." + ext

			makeme.append(complete_path)

			path_mkdir(path_get(complete_path))

		return makeme

	def run(self):
		"""Start the program !"""

		merge = self.settings['MERGE']
		book  = self.settings['BOOK']

		# File or files in folder / list
		if not merge and not book:
			msg("Parsing files individually ... \n")
			self._parseIndividually()

		if merge:
			msg("Parsing files and merging ... \n")
			self._parseMerge()

		if book:
			if "html" not in self.format_to:
				msg("Book only works for HTML")
				exit()

			if len(self.format_to) > 1 and "html" in self.format_to:
				answer = msg_cli_yesno("  Only HTML is being converted.")
				if not answer:
					exit()

			if len(self.files) < 3:
				msg("Feed me more files to make something pretty :) ")
				exit()

			# check if there is an output path, if not use
			# current working ONLY if source is not current working directory
			if not self.output:
				if not self.input == os.getcwd():
					self.output = os.getcwd()
				else:
					msg("How can I put this... You haven't specified an output directory and the source is the \n current running directory.")
					msg("Sorry, this is out of my league; check and run again")
					exit()

			if not self.format_from == 'markdown':
				msg("Not using markdown; no goodies for you.") 

			msg("Parsing files and making book ... \n")
			self._parseBook()

	def _parseIndividually(self):
		"""Parses file individually """

		for filey in self.files:
			newcommand = list(self.command)
			path       = self._getOutputPath(filey)
			msg("Converting: " + path_getFilename(filey))

			for ext in self.format_to:

				cmd_to  = self._cmdFromToOut('t', ext)
				cmd_out = self._cmdFromToOut('o', ext, path) 
				newcommand += cmd_to + cmd_out

				self._processOneFile(filey, newcommand, ext)

	def _parseMerge(self):
		""" pandoc already has a merge command when specified multiple files. 
		Special treatment for markdown input to html output"""

		if not self.output:
			self.output = os.getcwd()

		name = path_lastDir(self.input)

		meta_name        = "--metadata=title:" + name
		
		for ext in self.format_to:
			command_base = list(self.command)

			command_base += self._cmdFromToOut('t', ext)
			command_base += self._cmdFromToOut('o', ext, os.path.join(self.output, name)) 
			command_base += [meta_name]

			self._processOneFile(self.files, command_base, ext)

	def _processOneFile(self, filey, cmd, ext_to):
		"""Process one file separatelly (for merge and individually)
		:filey     one file or file list 
		:cmd       command starting point 
		:ext_to    current extension in format to
		"""

		this_cmd = list(cmd)

		if not ext_to == 'html' or (ext_to == 'html' and not self.format_from == 'markdown'):
			if isinstance(filey, list):
				this_cmd += filey
			else:
				this_cmd += [filey] 

			run_subprocess(this_cmd)
		else:
			cmd_special = list(this_cmd)
			#merge 
			if isinstance(filey, list):
				# join  all texts
				all_texts = list()
				for this_file in filey:
					with cmd_open_write(this_file, 'r') as tmp:
						all_texts += tmp.readlines()
			# individual
			else:
				with cmd_open_write(filey, 'r') as tmp:
					all_texts = tmp.readlines()

			all_texts, toc = if_special_elements(all_texts, self.settings['TOC_TAG'])
			if toc:
				cmd_special.append('--toc')

			all_texts = "".join(all_texts)
			run_subprocess(cmd_special, True, all_texts)		

	def _parseBook(self):
		"""Make a book with navigation between files """

		if "--toc" in self.command:
			self.command.remove("--toc")

		index_file = "noindex."
		# if we have a navigation file, have that as the file order (only markdown)
		if self.settings['FILE_INDEX'] and os.path.exists(self.settings['FILE_INDEX']) and self.format_from == 'markdown':
			index_file = self.settings['FILE_INDEX']

		self.settings['FILE_INDEX'] = index_file

		msg("Scanning files, hold on...")
		self._dbInit()

		index_title = self.db_files['index']['title']
		self.command.append('--variable=project-title:' + index_title)

		if self.settings['TEMPLATE_PANDY']:
			#just in case
			for index in range(len(self.command)):
				if self.command[index].startswith("--template"):
					del self.command[index]
					break 

		# process files 
		totalFiles = len(self.files)
		for i in range(0, totalFiles):

			if 'index.' in self.db_files[self.files[i]]['path_input']:
				continue

			current = self.db_files[self.files[i]]
			msg("Processing: " + path_getFilename(current['path_input']))
			current['text'] = self._parseBody(current['text'])

			prev = self.db_files[self.files[i - 1]]
			if 'index.' in prev['path_input'] or i == 0:
				prev = dict()
				prev['real_output'] = ""
				prev['title']       = ""

			if (i + 1) < totalFiles:
				nextt = self.db_files[self.files[i + 1]]
			else: 
				nextt = dict() 
				nextt['real_output'] = ""
				nextt['title']       = ""		

			newcommand = list(self.command)
			path_mkdir(path_get(current['real_output']))

			proj_index = '<a href="' + current['index_url'] +'">' +  index_title + "</a>"
			newcommand.append('--variable=project-index:' + proj_index)

			book_navigation    = self._bookNavigation(current, prev, nextt)
			sidebar_navigation = self.makeNavigationLinks(href_active=current['output'])

			if self.settings['NAV_SIDEBAR']:
				newcommand.append('--variable=side_navigation:' +sidebar_navigation)

			if self.settings['USE_NAV']:
				newcommand.append('--variable=book_navigation:' + book_navigation)

			self.finallySave(newcommand, current, book_nav=book_navigation, sidebar=sidebar_navigation, 
				            projindex=proj_index, pagetitle=current['title'])
		
		msg("Processing: index")

		index_cmd = list(self.command)
		if "--toc" in index_cmd:
			index_cmd.remove("--toc")

		index_cmd.append('--metadata=title:' + index_title)

		self.finallySave(index_cmd, self.db_files['index'], projindex=self.db_files['index']['title'])

	def finallySave(self, command, current_file, **kwargs):
		""" (book) Save according to template option 

		:command       current state of command 
		:current file  current file properties/dict 
		:**kwargs      key=value for builtintpl (book_nav, sidebar, projindex, pagetitle)
		"""

		local_cmd = list(command)

		if not self.settings['TEMPLATE_PANDY']:
			local_cmd += ['-o', current_file['real_output']]
			run_subprocess(local_cmd, True, current_file['text'])
		else: 
			trying = run_subprocess(local_cmd, True, current_file['text'])
			this_text = builtintpl(str(trying, encoding='utf-8'), **kwargs)		
			
			save(current_file['real_output'], this_text)			

	def _getOutputPath(self, filepath, strip_root=False):
		"""Get output path"""

		if not self.output:
			return path_delExtension(filepath)

		cooking = ""

		if self.settings['OUTPUT_FLAT'] or (not self.settings['OUTPUT_FLAT'] and filepath == self.input):
			cooking = path_delExtension(path_getFilename(filepath))
		else:
			cooking = path_delExtension(filepath)[len(self.input) + 1:]

		if strip_root:
			return cooking
		
		return os.path.join(self.output, cooking)

	def _bookNavigation(self, prop_current, prop_prev, prop_next):
		""" Makes the navigation links """

		navPre   = ""
		navNext  = ""
		navIndex = ""

		use_titles = self.settings['NAV_TITLE']
		link_tpl = '<li><a href="{ref}">{title}</a></li>'

		navIndex = link_tpl.format(ref=prop_current['index_url'], title="index")

		if prop_prev['real_output']:
			prev_path = path_relative_to(prop_prev['real_output'], prop_current['real_output'])

			navLink = prop_prev['title'] if use_titles else 'previous'	
			navPre = link_tpl.format(ref=prev_path, title="&lt; " + navLink)

		if prop_next['real_output']:
			next_path = path_relative_to(prop_next['real_output'], prop_current['real_output'])

			navLink = prop_next['title'] if use_titles else 'next'
			navNext = link_tpl.format(ref=next_path, title=navLink + " &gt;")

		return '<ul class="booknav">' + navPre + navIndex + navNext + '</ul>'

	def _dbInit(self):
		"""Init dbfiles with properties """

		self.db_files['index'] = {
			'title': "Index", 'path_input' :self.settings['FILE_INDEX'],
			'real_output' : os.path.join(self.output, "index.html"),
		     }

		ref_tpl = "[{thefile}]: {future_html}"

		for the_savior in self.files:

			props = self._fileMetadata(the_savior)
			self.db_files[the_savior] = props 

			# create references, with and without extension and prepare string 
			# only for markdown, but memory is inexpensive
			tmp_output       = self.db_files[the_savior]['output']
			tmp_file         = path_getFilename(the_savior)
			tmp_file_extless = path_delExtension(tmp_file)
			key_name         = tmp_file_extless + "|" + tmp_file
			tmp = ""

			self.references_list[key_name] = dict()
			self.references_list[key_name]['output'] = tmp_output
			self.references_list[key_name]['title']  = self.db_files[the_savior]['title']

			tmp =  "\n\n" + ref_tpl.format(thefile=tmp_file, future_html=tmp_output)
			tmp += "\n\n" + ref_tpl.format(thefile=tmp_file_extless, future_html=tmp_output)
			self.references_all += tmp
			
		if os.path.exists(self.settings['FILE_INDEX']):
			props = self._fileMetadata(self.settings['FILE_INDEX'])
			self.db_files['index'].update(props)
			self._fileOrderByIndex()
			self.db_files['index']['text'] = self._parseBody(self.db_files['index']['text'])
		else:
			self.db_files['index']['text'] = self.makeNavigationLinks(isIndex=True)


	def _fileOrderByIndex(self):
		"""Order list of files from custom index"""

		index_text = self.db_files['index']['text']

		extensions = "|".join(ACCEPTED_MD_EXTENSIONS)

		# gather internal and wikilinks (returned sub list items are different in position)
		links_internal = extractMdLinks(index_text, extension=extensions, style='inline') 
		links_wiki     = extractMdLinks(index_text, extension=extensions, style='wiki') 
		
		# join both list, getting only filename
		tmp_links = list()

		for wiki in links_wiki:
			tmp_links.append(wiki[0])

		for internal in links_internal:
			tmp_links.append(internal[1])

		# order, delete duplicates and overwrite original listing
		self.files = orderListFromList(self.files, tmp_links)

		tmp = list()
		[tmp.append(h) for h in self.files if h not in tmp]

		self.files = tmp		

	def _fileMetadata(self, filepath):
		"""for book. Get file properties: output path, input path, md title """

		properties = {'real_output' : '', 'path_input' : '', 'toc':'', 
		             'title' : '', 'text': '', 'index_url': ''}

		properties['path_input']  = filepath
		properties['real_output'] = self._getOutputPath(filepath) + ".html"
		properties['output']      = self._getOutputPath(filepath, strip_root=True) + ".html"
		properties['title']       = properties['output']
		properties['index_url']   = path_relative_to(
				            os.path.join(self.output, 'index.html'), properties['real_output'])

		# Magic begins! extract TOC
		cmd = list() 
		cmd.append(self.settings['PANDOC'])
		cmd.append('--toc')
		cmd.append('--standalone')

		with cmd_open_write(filepath, 'r') as tmp:
			cmd_text = tmp.readlines()

		# save for later
		properties['text'] = cmd_text

		if self.format_from == 'markdown':
			tmp = findTitleMd(text_lines=cmd_text)
			if tmp:
				properties['title'] = tmp

		cmd_text = "".join(cmd_text)
		minimum = run_subprocess(cmd, True, cmd_text)
		minimum = str(minimum, encoding='utf8')

		#remove new lines to not break pandoc
		minimum = minimum.splitlines()
		minimum = "".join(minimum)
		
		properties['toc'] = getTOC(minimum) 
		
		return properties

	def _parseBody(self, text_lines):
		"""Parse properly the text """

		cmd_text = text_lines

		if not self.format_from == 'markdown':
			cmd_text = "".join(cmd_text)
		else:
			cmd_text, _ = if_special_elements(cmd_text, self.settings['TOC_TAG'])
			cmd_text, _ = parse_wikilinks(cmd_text, this_references=self.references_list)
			cmd_text = "".join(cmd_text)
			cmd_text += "\n\n" + self.references_all

		return cmd_text

	def makeNavigationLinks(self, href_active=None, isIndex=False):
		"""make the whole book navigation: 

		:href_selected    item to apply active class and insert toc 
		"""

		final = ""
		anchor_tpl = '<a href="{href}">{title}</a>'

		for i in range(0, len(self.files)):
			current = self.db_files[self.files[i]]

			if current == "index":
				continue			
			
			title = current['title']
			href  = current['output']
			
			info_active = ""
			info_toc    = ""

			if not isIndex:
				real_href = path_relative_to(href, href_active)

				if href == href_active:
					info_active = " class='active'"
					info_toc = current['toc']
			else:
				real_href = href
				info_toc = current['toc'].replace('<a href="#', '<a href="' + real_href + "#")

			anchor = anchor_tpl.format(href=real_href, title=title)
			li = "<li{active}>" + anchor + "{toc}</li>"
			li = li.format(active=info_active, toc=info_toc)
			
			final += li

		return "<ul>" + final + "</ul>"




if __name__ == '__main__':

	if sys.version_info[0] < 3:
		print(" Sorry, only python 3")
		exit()

	args = get_args()

	print ("\n  ------------------ STARTING... ---------------------------\n ")
	CONFIG = prepare_args(args)

	# steady, ready, go!
	Pandy(CONFIG)
	
	print ("\n  ------------------ DONE! :) ------------------------------")

# History 

# 2014-02-18:  wikilinks fixes
# 2014-02-16:  Version 2.0 (released)
#              updated tests
#              fix references creation: only add found
#              Add built-in template
#              book should work with any file format. On markdown you get goodies.
#              args: proper list for format-to option
#                    -> in settings, use space separated list
#              .ini now parsed with configparser. Values in .ini must not have quotes
#              fixes
#              clean up
#  
# 2014-02-15:  complete ref list added
#              wikilinks: use a ref "database" to search (instead of files)
#              fixes
#  
# 2014-02-14:  if found, use beautifulsoup
#              new syntax for wikilinks [:file][title]
#              fixes for merging
#              Change whole navigation handling
#              fix index creation (toc) when subfolders
#              fix sidebar navigation when subfolders
#              fix wikilinks (reference)
#              find title in md and not in html
#              fixes
#              clean up
# 
# 2014-02-13:  source also accept a .ini (no force source and use only from config)
#              option to exclude toc from sidebar navigation
#              auto discover index
#              Navigations in own pandoc variables
#              check duplicates from custom index (while adding them to process)
#              if custom index has title, use it as project title
#              new wiki links: like md reference links but inverted -> [file][title]
#              no required: format to/from (so can use .ini)
#              book only for markdown
#              list all titles (and toc) in index
#              New way for handling files in book
#              chg db_files format
#              Remove toc for index
#              fixes
#  
# 2014-02-12:  rewriting. fixes
#              order files according to custom index
#              navigation: pages titles in sidebar, next-prev
#              sidebar -> highlight active
#              nav_pre according to index
#              read .ini automatically in folder where runs/source
#              remove some methods/cleanup
#              args take precedence over ini, which take precedence over default
#              wikilinks without file| prefix. Must use markdown extension
#              wikilinks in any file (not only index) (book)
#  
# 2014-02-11: ini fixes
#             option to hide navigation in book
#             modify command options
#             
# 2014-02-11: version 1.9 (released)
#             only python 3
#             fixes for book
# 
# 2014-01-30: prints file being converted
#             Filter extensions for converting, only html (hardcoded)
# 
# 2014-01-23: add titles in sidebar for navigation
# 
# 2014-01-21: version 1.8.1 (released)
#             new syntax for admonition
# 
# 2013-12-10: version 1.8 (released)
#             code refactoring
#             Less call to globals/obvious params
#             wikiLinks: if md link has no title and it's an existing file, use the filename as title 
#             Book: warn if no output path (defaults to current dir) and source dir is the running one
#             minor fixes
#             remove object creation to get file properties -> now dict
#             code refactoring, now using a class
#             config dict takes precedence over args
#
# 2013-12-09: less calls to globals
#             changes to args
#             + processing messages
#             no more tmp files
#             + more tests
#             modified test findH1
#             change findH1 method
#             Fix merging
#             merge (HTML): now can parse metadata block and have toc for full document
#             Book: include toc ONLY on selected file
#             book: fix having title twice in file when declared with meta-block
#             fix titles in book: add them, if not found add the filename (no ext)
#
# 2013-12-08: fixing nasty bugs
#             Fix finding H1s
#             code fixing / rewriting, less call to globals
#             + config file support (ini without sections)
#
# 2013-12-06: Clean up code
#             default config in dictionary
#             minor fix for admonitions
#             add simple tests / debug
#             Finish admonition parsing
#
# 2013-12-05: version 1.5 (released)
#             rewritten and to include cool stuff
#             + admonition parsing
#             + Abbreviations parsing markdown -> html
#             + warning when book also have other output formatting & html
#             + warning custom index with wiki links only for markdown
#             + more formats for input and output
#             fix: formats_to: no duplicates
#             fix: --nav only for book
#             fix: add html5 output default, can change to 'html'
#             fix: when merging: add <title>
#
# 2013-11-10: Added: merge files in directory -> end up with one output
#
# 2013-07-25: CHG data dir path
#
# 2013-07-21: version 1.0
#             Add folder (recursive) support
#             Add pandy script: "wrapper" for Pandoc.
