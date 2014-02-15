#! python3
# "Wrapper" for Pandoc (python 3): pandy [file/folder] [from] [to] [other options]
# pylint: disable=W0312, C0103, C0326, C0303
#                 tab instead spaces, invalid names, space operators, trailing whitespace
#
# -*- coding: utf-8 -*-
# tested for pandoc 1.12.3

# remember: when parsing indiv. -o is the folder to save to



# TOC wherever you want
# prob split stuff instead of having one big file
# Enable/disble extensions from cli
# custom css/js: --include-in-header
#
# wikilinks: fix when in sub and using [:file] to refer to one in root


import sys

if sys.version_info[0] < 3:
	print(" Sorry, only python 3")
	exit()

import argparse
import subprocess
import os
import codecs
import re

# ==============================
# ==== info & pandoc config ====
# ==============================

__version__ = "2.0"
_MY_USAGE = ''' %(prog)s [source] [format_from] [format_to] [other options]
 
 [format_to] can be a list of formats; separated with spaces 
 [source]    can be a file, folder or a .list
'''
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
	}

# leave out mmd_title_block and use yaml_metadata_block. Activated by default
# and can include the variables easily in template
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
	'TOC_TAG': '[TOCME]',
	}

# for wiki links mostly
ACCEPTED_MD_EXTENSIONS = ('md', 'txt', 'mdown', 'markdown')

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

	:param:only_exts tuple to include only selected extensions (mainly for html pages saved
		locally (which has folders > images ) )
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
	"""Gets the files from the .list (returns list). If not a .list, calls files_get()"""

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

def get_ini(filepath, keys_upper=False):
	"""Read ini without headers (ignores them). Return dict
	keys_upper: if key (options) are returned as uppercase. If false, returns as they're
	"""

	comment_char = '#'
	option_char  =  '='
	tmp_options  = dict()

	cmd_open = cmd_open_write(filepath, 'r')
	
	with cmd_open as infile:
		for line in infile:
			# ignore sections
			if line.startswith("["):
				continue
				
			# remove inline comments
			if not line.startswith(comment_char) and comment_char in line:
				line, comment = line.split(comment_char)
			
			# get the options / values
			if option_char in line:
				option, value = line.split(option_char)
				option = option.strip()
				value = value.strip()
				
				#cleans those " """' '''''"
				value = value.replace("'", "")
				value = value.replace('"', "")

				#check for booleans, ints, lists
				if value.lower() in ("true", "false"):
					if value.lower() == "true":
						value = True
					else:
						value = False
				elif value.isnumeric():
					value = int(value)
				elif value.startswith("[") and value.endswith("]"):
					value = value[1:len(value)-1]
					value = value.split(",")
					
					for index in range(len(value)):
						value[index] = value[index].strip()

				if keys_upper:
					option = option.upper()
				
				tmp_options[option] = value
	
	return tmp_options

# =========================
# == methods: commands ====
# =========================

def run_subprocess(command, output=False, text=None):
	""" run the cmd (list) 
	normally -> check_call
	if output activated: returns the output to string -> check_output
	if also text: to interact -> Popen (encodes to utf-8)
	"""

	if not output:
		return subprocess.check_call(command, stderr=subprocess.STDOUT)
	elif not text:
		return subprocess.check_output(command)
	else:
		text = text.encode('utf-8')
		tmp  = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
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

def if_special_elements_open(file_path, toc_tag):
	"""open file (file_path) and process trough specials 
	(admonitions, abbreviations, TOC tag, internallinks)
	returns: text (regardless if changed or not ) and hasTOC (bool)
	"""
	
	with cmd_open_write(file_path, 'r') as input_file:
		text_list = input_file.readlines()

	text, hasTOC = if_special_elements(text_list, toc_tag)
	new_text = "".join(text)

	return new_text, hasTOC

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

    should be: Some text with an <abbr title="Abbreviation">ABBR</abbr> and a <abbr title="Abbreviation Reference">REF</abbr>. Ignore REFERENCE and ref.
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

        if line.startswith("[") and (line.endswith("]\n") or line.endswith("]")):
            admon_start = True

            line = line.rstrip()
            line = line[1:len(line)-1]
            
            if ":" in line:
                admon_type, admon_title = line.split(':')
            else:
                admon_type = line
                admon_title = None

            new_str = '<div class="admonition ' + admon_type + '">'
            new_test.append(new_str)

            if admon_title:
                new_test.append('<p class="admonition-title">' + admon_title + '</p>')

            continue 

        if (line.startswith("\t") or line.startswith ("    ") or line == "\n") and admon_start:
            if not line == "\n":
                #remove first set of whitespace
                if line.startswith("\t"):
                   pattern = r'^\t{1}(.+)'
                else:
                   pattern = r'^\s{1,4}'
                
                line = re.sub(pattern, '\\1', line)

            new_test.append(line)

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
		find_me = link_tpl.format(title=link[0],link=link[1])
		replace_me = link_tpl.format(title=link[2],link=link[3])

		textNew = textNew.replace(find_me, replace_me)

	return textNew.split("<<<<SPLITMEOVERHERE>>>>")


def parse_wikilinks(text, list_files):
	"""Parse wikilinks (reference links but inverted): [:filename][title]
	[:filename] can have extension or not.
	[title] is optional. If blank: searches title

	:text   text as list
	:list_files  dict of files: any key and holding (minimum):
	                     path_input, title, output ("future path")

	return processed text (list) and references (list) of the file
	"""

	extensions = "|".join(ACCEPTED_MD_EXTENSIONS)
	links = extractMdLinks(text, extension=extensions, referencestyle=True)

	references = list()
	ref_tpl = "[{thefile}]: {future_html}"
	
	#hold filename, title_old and title_new. For later text replacement
	new_links = list()   

	for link in links:
		filename = link[0]
		title    = link[1]
		future_path  = ""
		future_title = ""

		# find output and title
		for key, thisfile in list(list_files.items()):
			if filename in thisfile['path_input']:
				future_path = thisfile['output']
				if title:
					future_title = title
					break
				if thisfile['title']:
					future_title = thisfile['title']
					break 
		
		# create ref
		tmp = ref_tpl.format(thefile=filename, future_html=future_path)
		if not tmp in references:
			references.append(tmp)

		tmp = [filename, title, future_title]
		if not tmp in new_links:
			new_links.append([filename, title, future_title])

	# replace in text 
	newtext = "<<<<SPLITMEOVERHERE>>>>".join(text)
	search_tpl = "[:{filename}][{title}]"
	replace_tpl = "[{title}][{filename}]"

	for link in new_links:
		filename = link[0]
		title_old = link[1]
		title_new = link[2]
		newtext = newtext.replace(
			search_tpl.format(filename=filename, title=title_old), 
			replace_tpl.format(filename=filename, title=title_new))

	newtext = newtext.split("<<<<SPLITMEOVERHERE>>>>")

	return newtext, references	



def extractMdLinks(text, extension="md", referencestyle=False):
	"""Extract markdown links in text with extension. 
	:text list 
	:extension the allowed extension
	:referencestyle    for [][] links 
	:return a nested list. 
	             normal: holder(title, link)
	             reference: holder(title, id_link)
	"""

	list_links = list()

	expr_normal = "\[(.+?)?\]\((.+?\.(" + extension + "))\)"
	expr_reference = "\[:(.+?[\.(" + extension + ")]?)\]\[(|.+?)\]"

	if referencestyle:
		expr = r'' + expr_reference
	else:
		expr = r'' + expr_normal

	for line in text:
		matches = re.findall(expr, line)
		for m in matches:
			title = m[0].strip()
			link  = m[1].strip()
			if [title, link] not in list_links:
				list_links.append([title, link])

	return list_links

def findTitleMd(filepath=None, text_lines=None):
	"""Find title in markdown file. All possibilities (% , title: # and =====)
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
			return line[1:]
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

class ValueCorrect(argparse.Action):
	""" Custom action for args, if value is correct """

	def __call__(self, parser, namespace, values, option_string=None):

		if self.dest == "format_from" and values not in _FORMATS_BOTHWAYS:
			parser.error('Incorrect format')

		if self.dest == "format_to":
			FORMATS_TO = _FORMATS_BOTHWAYS + _FORMATS_OUTPUT

			for val in values:
				if val not in FORMATS_TO:
					parser.error('Incorrect format')
					break

		setattr(namespace, self.dest, values)

def get_args():
	""" Args parsing and translation to nice configs"""

	parser = argparse.ArgumentParser(add_help=False, usage=_MY_USAGE 
		        , description=help_replaceStringFormats(_MY_DESCRIPTION, 
		        	            ['{{ _FORMATS_OUTPUT }}', '{{ _FORMATS_BOTHWAYS }}'])
		        , formatter_class=argparse.RawTextHelpFormatter) 

	required = parser.add_argument_group(' Required')
	required.add_argument("source", action=InputExist, help="file, folder, .list or config file")
	
	option_file = parser.add_argument_group(' Options:\n\n file related')
	option_file.add_argument("--from", '-f', action=ValueCorrect, help="Convert from this")
	option_file.add_argument("--to", '-t',   action=ValueCorrect, nargs='+', 
		    help="Convert to this (can be a list)")

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
		settings_file = get_ini(settings_final['CONFIG_FILE'], True)
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

	if not settings_final['TOC']:
		settings_final['TOC_DEPTH'] = False	

	if settings_final['SOURCE'].endswith(".list") and not settings_final['OUTPUT_FLAT']:
		print("  Keeping folder structure with .list not supported. Skipping option")
		settings_final['OUTPUT_FLAT'] = True 

	#Special belonging if not book, just to clean up
	if not settings_final['BOOK']:
		if (settings_final['NAV_TITLE'] or settings_final['NAV_SIDEBAR'] 
			or settings_final['USE_NAV']):

			settings_final['NAV_TITLE']   = False
			settings_final['NAV_SIDEBAR'] = False
			settings_final['USE_NAV']     = False

	return settings_final

# =================================
# == Html stuff: shouldn't be... ==
# =================================

def htmlSplitter(text, tag, special_start=None, find=False):
	"""Split html, getting only what is in tag 
	
	:special_start if beginning has id or class 
	:find  if not found, return None 
	"""
	
	tpl_start = "<" + tag + ">"
	if special_start:
		tpl_start = special_start

	tpl_end = "</" + tag + ">"

	splitting = text.split(tpl_start)
	if find:
		if len(splitting) <= 1:
			return None 

	return splitting[1].split(tpl_end)[0]

def getSplitTocBody(html, html_ver):
	"""Returns the TOC list and the rest of the html body.
	(splitting from <body>)

	toc    str 
	body   str, whatever after toc

	:html_ver   for toc splitting.
	            html5 -> nav 
	            html -> div 
	"""

	text = htmlSplitter(html, 'body')
	
	toc_tag = "nav"
	if not html_ver == "html5":
		toc_tag = "div"

	if not 'id="TOC">' in text:
		print("no toc ")
		return '', text.split('</' + toc_tag + '>')[1]

	text = text.split('<div id="TOC">')[1]
	text_parts = text.split('</div>')
	body = text_parts[1]
	toc = text_parts[0]
	toc = toc.splitlines()
	toc = [line for line in toc if line]
	toc = toc[1:-1] # remove first <ul> and last </ul>
	toc = "".join(toc)

	return toc, body

# ============
# == Misc ====
# ============

def orderListFromList(orderthis, fromthis, bythiscol):
	"""Order a list, based on another by value. 
	:orderthis    list to be ordered 
	:fromthis     new order list 
	:bythiscol    "column" number to order by this value set 
	"""

	tmp_list = list()


	for new_order in fromthis:
		for index, item in enumerate(orderthis):
			#we trust the user that will be no files with same name
			if new_order[bythiscol] in item:
				tmp_list.append(item)
				break 

	return tmp_list

def help_replaceStringFormats(string, placeholders):
	"""Replaces placeholders in string, with _FORMATS_BOTHWAYS and _FORMATS_OUTPUT
	
	string      : complete string 
	placeholders: list of placeholders; what to replace -> converts to list to join

	returns processed string 
	"""

	tmp = ""

	for placeholder in placeholders:

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

			if the_choosen_one == "_FORMATS_BOTHWAYS":
				if item.startswith("md"):
					continue 

				is_synom = True if item == 'md' else False 

			if is_synom:
				tmp += " (or " + item + ")"
			else:
				tmp += ", " + item

		tmp = tmp[2:] # delete fist ", "
		string = string.replace(placeholder, tmp)
		tmp = ""

	return string

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
		self.command.append('--standalone')  # complete html --standalone

		# Exclude: do not treat right now or already done
		exclude = ("FORMAT_TO", "FORMAT_FROM", "SOURCE", "OUTPUT_PATH", "MERGE",
			"OUTPUT_FLAT", "SLIDES", "BOOK", "HTML_VER", "PANDOC", "FILE_INDEX")

		# Add the options
		for key, val in self.settings.items():
			if key in exclude:
				continue
			self.command += translate_argsPandoc(key, val)

		self.command += self._cmdFromToOut('f', self.format_from)

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

		print("")
		# File or files in folder / list
		if not merge and not book:
			print ("  Parsing files individually ... \n")
			self._parseIndividually()

		else:
			if merge:
				print ("  Parsing files and merging ... \n")
				self._parseMerge()
			else:
				# book
				if not self.format_from == 'markdown':
					print(" Book only for markdown, sorry")
					exit()

				# check if there is html in the output formats. 
				# If there are more than html or none, inform
				if "html" not in self.format_to:
					print ("  Book only works for HTML")
					exit()

				if len(self.format_to) > 1 and "html" in self.format_to:
					answer = msg_cli_yesno("  Only HTML is being converted.")
					if not answer:
						exit()

				if len(self.files) < 3:
					print ("  Feed me more files to make something pretty :) . ")
					exit()

				# check if there is an output path, if not use
				# current working ONLY if source is not current working directory
				if not self.output:
					if not self.input == os.getcwd():
						self.output = os.getcwd()
					else:
						print ("  How can I put this... You haven't specified",
						'an output directory and the source is the \n',
						"current running directory.", 
						"Sorry, this is out of my league; check and run again")
						exit()
	 
				print ("  Parsing files and making book ... \n")
				self._parseBook()

	def _parseIndividually(self):
		"""Parses file individually """

		for filey in self.files:
			newcommand = list(self.command)
			path       = self._getOutputPath(filey)
			print (" Converting: " + path_getFilename(filey))

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

		# if we have a navigation file, have that as the file order
		index_file = self.settings['FILE_INDEX']
		if index_file and os.path.exists(index_file):
			index_text = cmd_open_file(index_file).splitlines()
			files_order = extractMdLinks(index_text, extension="md")
			self.files = orderListFromList(self.files, files_order, 1)
			
			#del dups 
			tmp = list()
			[tmp.append(h) for h in self.files if h not in tmp]

			self.files = tmp
		else:
			index_file = "noindex."

		self.settings['FILE_INDEX'] = index_file
		self._dbInit()

		# process files 
		for i in range(0, len(self.files)):
			if 'index.' in self.db_files[self.files[i]]['path_input']:
				continue

			current = self.db_files[self.files[i]]
			print (" Processing: " + path_getFilename(current['path_input']))

			prev = self.db_files[self.files[i - 1]]

			if (i + 1) < len(self.files):
				nextt = self.db_files[self.files[i + 1]]
			else: 
				nextt = dict() 
				nextt['real_output'] = ""
				nextt['title']       = ""		

			newcommand = list(self.command)

			#finish processing text
			current = self._fileParseBody(current, newcommand)

			newcommand += ['-t', 'html', '-o', current['real_output']]

			path_mkdir(path_get(current['real_output']))

			# re add title (for <title> and first heading)
			newcommand.append('--metadata=title:' + current['title'])
			newcommand.append('--variable=project-title:' + self.db_files['index']['title'])

			tmp = '<a href="' + current['index_url'] +'">' +  self.db_files['index']['title'] + "</a>"
			newcommand.append('--variable=project-index:' + tmp)

			# navigations
			if 'index.' in prev['path_input']:
				prev = dict()
				prev['real_output'] = ""
				prev['title'] = ""

			book_navigation = self._bookNavigation(current, prev, nextt)

			sidebar_navigation = self.makeNavigationLinks(href_active=current['output'])

			if self.settings['NAV_SIDEBAR']:
				newcommand.append('--variable=side_navigation:' + sidebar_navigation)

			if self.settings['USE_NAV']:
				newcommand.append('--variable=book_navigation:' + book_navigation)

			current['text'] = current['text'].replace('<div class="references">', "")
			run_subprocess(newcommand, True, current['text'])


		# process index 
		index_cmd = list(self.command)
		if "--toc" in index_cmd:
			index_cmd.remove("--toc")

		print (" Processing: index.md")

		if os.path.exists(self.db_files['index']['path_input']):
			self.db_files['index'] = self._fileParseBody(self.db_files['index'], index_cmd)

		else:
			self.db_files['index']['text'] = self.makeNavigationLinks(isIndex=True)
		index_cmd += ['-o', self.db_files['index']['real_output'], '--metadata=title:' + self.db_files['index']['title']]
		run_subprocess(index_cmd, True, self.db_files['index']['text'])		

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

		navPre  = ""
		navNext = ""
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

	def _dbInit(self, index_path=None):
		"""Init dbfiles with props """

		self.db_files['index'] = {
			'title': "Index",
			'real_output' : os.path.join(self.output, "index.html"),
			'path_input' :self.settings['FILE_INDEX'],
		     }

		for the_savior in self.files:

			props = self._fileMetadata(the_savior)
			self.db_files[the_savior] = props 

			# create references, with and without extension
			self.references_list[the_savior] = self.db_files[the_savior]['output']
			self.references_list[path_delExtension(the_savior)] =  self.db_files[the_savior]['output']
			
		if os.path.exists(self.settings['FILE_INDEX']):
			props = self._fileMetadata(self.settings['FILE_INDEX'])
			self.db_files['index']['title'] = props['title']

		ref_tpl = "[{thefile}]: {future_html}\n\n"
		for title, path in list(self.references_list.items()):
			tmp = ref_tpl.format(thefile=title, future_html=path)
			self.references_all += tmp 

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

		tmp = findTitleMd(filepath)
		if tmp:
			properties['title'] = tmp

		return properties

	def _fileParseBody(self, fileprops, cmd):

		# Magic begins! 
		cmd = list(cmd) 
		cmd += ['-t', 'html']
		
		# remove the --template, this way can extract title easily
		for index, item in enumerate(cmd):
			if item.startswith("--template"):
				del cmd[index]
				break 			
		
		# Special syntax 
		with cmd_open_write(fileprops['path_input'], 'r') as tmp:
			cmd_text = tmp.readlines()

		cmd.append('--toc')
		cmd_text, toc = if_special_elements(cmd_text, self.settings['TOC_TAG'])

		cmd_text, references = parse_wikilinks(cmd_text, self.db_files)
		cmd_text = "".join(cmd_text)

		references = "\n\n".join(references)
		cmd_text += "\n\n" + references

		minimum = run_subprocess(cmd, True, cmd_text)
		minimum = str(minimum, encoding='utf8')
	
		#extract toc
		fileprops['toc'] = ""
		this_toc, fileprops['text'] = getSplitTocBody(minimum, html_ver=self.settings['HTML_VER']) 

		if this_toc:
			fileprops['toc'] = "<ul>" + this_toc + "</ul>"



		return fileprops


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
			li = "<li{active}>" + anchor + "{toc}</li>\n"
			li = li.format(active=info_active, toc=info_toc)
			
			final += li

		return "<ul>\n" + final + "</ul>"





if __name__ == '__main__':

	args = get_args()

	print ("\n  ------------------ STARTING ------------------------------")
	CONFIG = prepare_args(args)

	# steady, ready, go!
	Pandy(CONFIG)
	
	print ("\n  ------------------ DONE! :) ------------------------------")