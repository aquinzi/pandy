#! python3
# "Wrapper" for Pandoc (python 3): pandy [file/folder] [from] [to] [other options]

# -*- coding: utf-8 -*-
# tested for pandoc 1.12.3


# check if book is really for markdown only
# option to exclude toc from sidebar navigation
# TOC wherever you want
# prob split stuff instead of having one big file
# Enable/disble extensions from cli
# custom css/js: --include-in-header
# remove source, format to/from of required commands. So can use .ini
# 				basically we only need (from) md to html for special processing and they're default
# 

import sys

if sys.version_info[0] < 3:
	print(" Sorry, only python 3")
	exit()

import argparse
import subprocess
import sys
import os
import codecs
import re

# ==============================
# ==== info & pandoc config ====
# ==============================

__version__ = "1.9.5"
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
	'NAV_TITLE': False,  #For book, use title navigation
	'NAV_SIDEBAR': False,  #For book, sidebar with titles

	'EMAIL_HIDE': False, # e-mail obfuscation (default none, true = references)
	'BIBLIOGRAPHY': '',
	'HTML_VER': 'html5', # Output html5 instead of html4 (html)
	'TOC_TAG': '[TOCME]',
	}

# for wiki links mostly
ACCEPTED_MD_EXTENSIONS = ('md', 'txt', 'mdown', 'markdown')

# =========================
# == methods: prettify ====
# =========================

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

def files_get(path, only_exts=(), exclude_files=[]):
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

def if_special_elements(file_path, toc_tag, pandoc_path=None):
	"""open file (file_path) and process trough specials 
	(admonitions, abbreviations, TOC tag, wikilinks)
	:pandoc_path  include pandoc path, if None wikilinks will be skipped
	returns: text (regardless if changed or not ) and hasTOC (bool)
	"""
	
	with cmd_open_write(file_path, 'r') as input_file:
		text_list = input_file.readlines()

		hasTOC, text = find_TOCinFile(text_list, toc_tag)
		text = parse_admonitions(text)
		text = parse_abbreviations(text)
		if pandoc_path:
			text = parse_wikiLinks(text, pandoc_path)

	new_text = "".join(text)

	return new_text, hasTOC

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

def parse_wikiLinks(text, pandoc_path):
	""" Process "wiki" links: [](file.md) to [file title](newpath.html).
	It must be a markdown file, opened before (list)

	"""

	extensions = "|".join(ACCEPTED_MD_EXTENSIONS)

	# harvest all links first 
	links = extractMdLinks(text, extension=extensions)

	#find real title and output
	for link in links:
		link_new = path_delExtension(link[1]) + ".html"
		future_path = link_new
		
		title_new = link[0]
		if not title_new: 
			if os.path.exists(future_path):
				title_new = findTitleHtml(future_path, pandocpath=pandoc_path, continueh1=True)
			else:
				title_new = path_delExtension(link[1])

		link.append(title_new)
		link.append(link_new)

	# replace in file
	textNew = "<<<<SPLITMEOVERHERE>>>>".join(text)
	link_tpl = "[{title}]({link})"

	for link in links:
		find_me = link_tpl.format(title=link[0],link=link[1])
		replace_me = link_tpl.format(title=link[2],link=link[3])

		textNew = textNew.replace(find_me, replace_me)

	textNew = textNew.split("<<<<SPLITMEOVERHERE>>>>")
	
	return textNew


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

	description = help_replaceStringFormats(_MY_DESCRIPTION, ['{{ _FORMATS_OUTPUT }}', '{{ _FORMATS_BOTHWAYS }}'])

	parser = argparse.ArgumentParser(add_help=False, usage=_MY_USAGE, description=description,
		                    formatter_class=argparse.RawTextHelpFormatter) 

	required = parser.add_argument_group(' Required')
	required.add_argument("source",      action=InputExist,   help="file, folder or a .list")
	required.add_argument("format_from", action=ValueCorrect, help="Convert from this")
	required.add_argument("format_to",   action=ValueCorrect, help="Convert to this (can be a list)", nargs='+')

	option_file = parser.add_argument_group(' Options:\n\n file related')
	option_file.add_argument("--output", "-o", help="Output folder", metavar="FOLDER")
	option_file.add_argument("--flat", action='store_true', help="Don't keep folder structure")
	option_file.add_argument("--self", help="self contained file", action='store_true')	
	option_file.add_argument("--header", help="Header file. Included as it is (raw, verbatim)", metavar="FILE")
	option_file.add_argument("--footer", help="Footer file. Included as it is (raw, verbatim)", metavar="FILE")
	option_file.add_argument("--html4", help="Use html4 output instead of html5", action="store_true")
	option_file.add_argument("--slides", help="Slides format. Options: " + ", ".join(_SLIDES_OPTIONS) + ". Default: %(default)s", choices=_SLIDES_OPTIONS, default=_DEFAULT_CONFIG['SLIDES'], metavar="")
	option_file.add_argument("--bib", help="Use bibliography file", metavar="FILE")

	exclusive = option_file.add_mutually_exclusive_group()
	exclusive.add_argument("--merge", "-m", action="store_true", help="Merge files.")
	exclusive.add_argument("--book", "-b", action="store_true", help="Make a book with navigation (next/prev) and index")

	style = parser.add_argument_group(' styling')
	style.add_argument("--css", help="External CSS", metavar="FILE")

	style.add_argument("--highlight", choices=_HIGHLIGHT_OPTIONS, default=_DEFAULT_CONFIG['HIGHLIGHT'], help="Highlight style. Options: " + ", ".join(_HIGHLIGHT_OPTIONS) + ". Default: %(default)s", metavar="")
	style.add_argument("--highlight-no", help="No highlight", action='store_true')
	style.add_argument("--tpl", help="Template file. Can enter 'default' for pandoc's default.", metavar="FILE")

	other = parser.add_argument_group(' other')
	other.add_argument("--toc", help="include TOC", action='store_true')
	other.add_argument("--depth", help="TOC depth. Choices: 1, 2, 3, 4, 5, 6. Default: %(default)s", type=int, choices=[1, 2, 3, 4, 5, 6], default=_DEFAULT_CONFIG['TOC_DEPTH'], metavar="")
	other.add_argument("--hide", action='store_true', help="e-mail obfuscation (default none, true = references)")
	other.add_argument("--sections", action='store_true', help="Wrap sections in <sections>, attach identifiers instead of titles")

	other.add_argument("--no-nav", "-nn", help="(For book) disable navigation", action="store_true")
	other.add_argument("--nav-title", "-nt", help="(For book) use titles in navigation", action="store_true")
	other.add_argument("--nav-side", "-ns", help="(For book) Make a sidebar with titles", action="store_true")
	other.add_argument("--config", help="Use a configuration file (option=key values)", metavar="FILE")

	pandoc = parser.add_argument_group(' Pandoc')
	pandoc.add_argument("--pandoc",   default=_DEFAULT_CONFIG['PANDOC'], help="Pandoc path. Default: %(default)s")
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
		'nav_side' : 'NAV_SIDEBAR',
		'no_nav' : 'USE_NAV',
		'config' : 'CONFIG_FILE',
		}

	#just convert to uppercase
	options_noNameChange = ('pandoc', 'highlight', 'slides', 'source', 'sections',
		             'format_from', 'format_to', 'toc', 'merge', 'book', 'highlight_no') 

	settings_args = dict()

	# transfer & translate
	for key, val in arg_dict.items():
		if key in options_noNameChange:
			settings_args[key.upper()] = val 
		else:
			if key == "html4":
				val = 'html' if val else 'html5'
			if key == 'no_nav':
				val = False if val else True 

			settings_args[argsToSettings[key]] = val 

	if settings_args['SOURCE'] == ".":
		settings_args['SOURCE'] = os.getcwd()

	return settings_args

def prepare_args(arg_dict):
	""" Prepares the args to a nice config dictionary. Also reads .ini """
	
	settings_final = dict(_DEFAULT_CONFIG)

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
		answer = msg_cli_yesno("  To convert to PDF needs LaTeX installed (and in PATH).")
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
		if settings_final['NAV_TITLE'] or settings_final['NAV_SIDEBAR'] or settings_final['USE_NAV']:
			settings_final['NAV_TITLE']   = False
			settings_final['NAV_SIDEBAR'] = False
			settings_final['USE_NAV']     = False

		if settings_final['FILE_INDEX']:
			print("  --index only works with book. Skipping that option")
			settings_final['FILE_INDEX'] = ""

	return settings_final


# ==============
# == Pandy! ====
# ==============

class Pandy():
	"""Handles the parsing and related """

	def __init__(self, config_dict):
		""" Preparation, config_dict must been checked and translated before """

		self.settings    = config_dict
		self.input       = config_dict['SOURCE']
		self.output      = config_dict['OUTPUT_PATH']
		self.format_from = config_dict['FORMAT_FROM']
		self.format_to   = config_dict['FORMAT_TO']
		self.files       = []
		self.command     = []

		exts = tuple()
		if self.format_from == "html":
			exts = (".html", ".htm")

		excl = [DEFAULT_INI_NAME]

		self.files = files_list(self.input, only_exts=exts, exclude_files=excl)
		
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

		# make base pandoc command. 
		self.command.append(self.settings['PANDOC'])
		self.command.append('--standalone')  # complete html --standalone

		# Exclude: do not treat right now or already done
		exclude = ("FORMAT_TO", "FORMAT_FROM", "SOURCE", "OUTPUT_PATH", 
			"OUTPUT_FLAT", "MERGE", "SLIDES", "BOOK", "HTML_VER", "PANDOC", "FILE_INDEX" )

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
	 
				# check if there is html in the output formats. 
				# If there are more than html or none, inform
				if "html" not in self.format_to:
					print ("  Book only works for HTML")
					exit()

				if len(self.format_to) > 1 and "html" in self.format_to:
					answer = msg_cli_yesno("  Only HTML is being converted.")
					if not answer:
						exit()

				if self.settings['FILE_INDEX'] and not self.format_from == 'markdown':
					print ("\n  If the custom index file contains wiki links, ",
						"it should be in markdown. It appears that you haven't specified it.",
						"The wiki links won't be parsed")

				print ("  Parsing files and making book ... \n")
				self._parseBook()

	def _parseIndividually(self):
		"""Parses file individually """

		for filey in self.files:
			newcommand = list(self.command)
			path       = self._getOutputPath(filey)
			print (" Converting: " + path_getFilename(filey))

			for ext in self.format_to:
				if not ext == "html":
					stdin = False 
					is_from = [filey] 
				else:
					stdin = True 
					is_from, toc = if_special_elements(filey, self.settings['TOC_TAG'])

					if toc and not "--toc" in newcommand:
						newcommand.append('--toc')

				cmd_to  = self._cmdFromToOut('t', ext)
				cmd_out = self._cmdFromToOut('o', ext, path) 
				newcommand += cmd_to + cmd_out

				if not stdin:
					newcommand += is_from
					run_subprocess(newcommand)
				else:
					run_subprocess(newcommand, True, is_from)

	def _parseMerge(self):
		""" pandoc already has a merge command when specified multiple files. 
		Special treatment for HTML output """

		if not self.output:
			self.output = os.getcwd()

		name = path_lastDir(self.input)
		path = os.path.join(self.output, name)

		default_template = "--template=default.html5"
		meta_name = "--metadata=title:" + name
		
		for ext in self.format_to:
			command_base = list(self.command)

			cmd_out = self._cmdFromToOut('o', ext, path) 
			command_base += self._cmdFromToOut('t', ext)

			if "--standalone" in command_base:
				wasStandalone = "--standalone"
			else:
				wasStandalone = False 

			if "--toc" in command_base:
				wasTOC = True 
			else:
				wasTOC = False


			if not ext == "html":
				command_base += [self.files] + cmd_out + [meta_name]
				run_subprocess(command_base)
			else:
				# remove template to have less clutter
				template = ""
				for index in range(len(command_base)):
					if command_base[index].startswith("--template"):
						template = command_base[index]
						del command_base[index]
						break 

				# activate default template to have TOC
				if wasTOC:
					command_base.append(default_template)
				elif wasStandalone:
					#remove everything to make it a fragment
					command_base.remove(wasStandalone)

				# now process
				merged_files = ""
				all_bodies   = ""
				all_tocs     = ""

				for thisFile in self.files:
					
					new_text, toc = if_special_elements(thisFile, self.settings['TOC_TAG'])		
					new_text = run_subprocess(command_base, True, new_text)

					if not wasTOC:
						merged_files += new_text
					else:
						toc, body   = getSplitTocBody(new_text)
						all_tocs   += toc 
						all_bodies += body 

				# go back to full HTML
				if wasTOC:
					command_base.remove(default_template)
					all_tocs = '<div id="TOC">\n' + all_tocs + '\n</div>'
					merged_files = all_tocs + all_bodies
				
				if wasStandalone:
					command_base.append(wasStandalone)

				if template:
					command_base.append(template)

				# finally save
				newcommand = command_base + cmd_out + [meta_name]
				run_subprocess(newcommand, True, merged_files)


	def _parseBook(self):
		"""Make a book with navigation between files """

		# to get properties for all files
		db_files = list()
		db_files.append({
			'title': "Index",
			'toc': '', 
			'path_output' : os.path.join(self.output, "index.html"),
			'path_input' : "noindex.",
			'text' : '',
			})

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

		self._listChapters()

		tmp = list(self.files) 
		tmp.append(index_file)

		# get other files properties
		for picked in tmp:
			if not os.path.exists(picked):
				continue

			if not 'index.' in picked.lower():
				print (" Converting: " + path_getFilename(picked))

			props = self._singleFileProperties(picked, self.command, specials=True)

			# should be in another way, but too lazy
			text_for_toc = "dfgdfg <body>" + props['text'] + "</body> dfghdkfjdhjkf"
			current_toc, props['text'] = getSplitTocBody(text_for_toc)
			props['toc'] = "<ul>" + current_toc + "</ul>"

			if 'index.' in picked.lower():
				db_files[0].update(props)
			else:
				db_files.append(props)


		filesTotal = len(db_files)
		# processing, ommiting index 
		for i in range(1, filesTotal):

			current = db_files[i]
			prev = db_files[i - 1]

			try:
				db_files[i + 1]
			except IndexError:
				nextt = dict() 
				nextt['path_output'] = ""
				nextt['title']       = ""
			else:
				nextt = db_files[i + 1]

			newcommand = list(self.command)
			newcommand += ['-t', 'html', '-o', current['path_output']]

			path_mkdir(path_get(current['path_output']))

			# re add title (for <title> and first heading)
			newcommand.append('--metadata=title:' + current['title'])

			# navigations
			if 'index.' in prev['path_input']:
				prev = dict()
				prev['path_output'] = ""
				prev['title'] = ""

			book_navigation = self._bookNavigation(current['path_output'], 
				                          prev['path_output'], prev['title'], 
				                          nextt['path_output'], nextt['title'])
			sidebar_navigation = makeNavigationLinks(self.listChapters, 
				                  title_active=current['title'], toc_active=current['toc'])

			if self.settings['NAV_SIDEBAR']:
				newcommand.append('--variable=side_navigation:' + sidebar_navigation)

			if self.settings['USE_NAV']:
				newcommand.append('--variable=book_navigation:' + book_navigation)

			newcommand.append('--variable=project-title:' + db_files[0]['title'])

			run_subprocess(newcommand, True, current['text'])


		# finish index 
		index_cmd = list(self.command)
		if "--toc" in index_cmd:
			index_cmd.remove("--toc")

		if not db_files[0]['text']:
			db_files[0]['text'] = makeNavigationLinks(self.listChapters, files_tocs=db_files[1:])

		index_cmd += ['-o', db_files[0]['path_output'], '--metadata=title:' + db_files[0]['title']]
		run_subprocess(index_cmd, True, db_files[0]['text'])
		



	def _getOutputPath(self, filepath):
		"""Get output path"""

		if not self.output:
			return path_delExtension(filepath)

		if self.settings['OUTPUT_FLAT'] or (not self.settings['OUTPUT_FLAT'] and filepath == self.input):
			return os.path.join(self.output, path_delExtension(path_getFilename(filepath)))
		else:
			return os.path.join(self.output, path_delExtension(filepath)[len(self.input) + 1:])

	def _singleFileProperties(self, filepath, cmd=None, specials=False):
		"""for book. Instead of object use this which returns a dictionary with:
		output path, input path, title and text. Does the file processing and gets the title and html

		cmd: the command as starting point 
		specials: check for abbreviations, admonitions, toc, wikilinks
		"""

		#sketch
		properties = {
		          'path_output' : '',
		          'path_input' : '',
		          'title' : '', 'text' : '',
		          }

		if filepath:
			properties['path_input']  = filepath
			properties['path_output'] = self._getOutputPath(filepath) + ".html"

		properties['title'] = path_delExtension(path_getFilename(properties['path_output']))

		if not cmd:
			return properties

		# Magic begins! (Get title and (parsed) body)
		cmd = list(cmd) 
		cmd += ['-t', 'html']

		# remove the --template, this way can extract title easily
		for index, item in enumerate(cmd):
			if item.startswith("--template"):
				del cmd[index]
				break 			
		
		# special treatment for specials 
		if specials:
			cmd_text, toc = if_special_elements(properties['path_input'], 
				            self.settings['TOC_TAG'], pandoc_path=self.settings['PANDOC'])

			if toc and not "--toc" in cmd:
				cmd.append('--toc')
		else:
			cmd_text = None 
			cmd.append(properties['path_input'])

		minimum = run_subprocess(cmd, True, cmd_text)
		minimum = str(minimum, encoding='utf8')

		# get the body (this is to also have the metadata; otherwise, 
		# with --standalone it gets the body but not header-block)
		properties['text'] = htmlSplitter(minimum, 'body')

		properties['title'] = findTitleHtml(text_html=minimum, continueh1=True)
		
		return properties

	def _bookNavigation(self, current_path, prev_path, prev_title, next_path, next_title):
		""" Makes the navigation links """

		navPre  = ""
		navNext = ""
		navIndex = ""

		index_url = path_relative_to(os.path.join(self.output, 'index.html'),
							current_path)

		use_titles = self.settings['NAV_TITLE']
		link_tpl = '<li><a href="{ref}">{title}</a></li>'

		navIndex = link_tpl.format(ref=index_url, title="index")

		if prev_path:
			prev_path = path_relative_to(prev_path, current_path)

			navLink = prev_title if use_titles else 'prev'	
			navPre = link_tpl.format(ref=prev_path, title="&lt; " + navLink)

		if next_path:
			next_path = path_relative_to(next_path, current_path)

			navLink = next_title if use_titles else 'next'
			navNext = link_tpl.format(ref=next_path, title=navLink + " &gt;")

		return '<div class="nav"><ul>' + navPre + navIndex + navNext + '</ul></div>'







	def _listChapters(self):
		""" list of titles in project with properties
		:returns list 
		"""

		tmp_list = list()  # holds tuple: title, href

		for the_savior in self.files:
			newcommand = list(self.command)
			file_current = self._singleFileProperties(the_savior, newcommand, True)
			relative = path_relative_to(file_current['path_output'], self.output, True)

			tmp_list.append((file_current['title'], relative))

		self.listChapters = tmp_list


def makeNavigationLinks(links, title_active=None, toc_active='', files_tocs=None):
	"""make the whole book navigation: 

	:links   a nested list (or tuple) as title, href
	:title_selected    item to apply active class and insert toc 
	:toc_active      toc for selected item
	:files_tocs      all the tocs from project, for index 
	"""

	final = ""
	anchor_tpl = '<a href="{href}">{title}</a>'

	for link in links:
		title = link[0]
		href = link[1]
		anchor = anchor_tpl.format(href=href, title=title)
		
		info_active = ""
		info_toc = ""

		#sidebar 
		if title_active is not None and toc_active:
			if title == title_active:
				info_active = " class='active'"
				info_toc = toc_active
		
		#index 
		if files_tocs:
			for findtoc in files_tocs:
				if path_getFilename(findtoc['path_output']) == href:
					#fix links so they point to page 
					info_toc = findtoc['toc'].replace('<a href="#', '<a href="' + href + "#")

					break

		li = "<li{active}>" + anchor + "{toc}</li>\n"
		li = li.format(active=info_active, toc=info_toc)
		
		final += li

	return "<ul>\n" + final + "</ul>"

def getSplitTocBody(html):
	"""Returns the TOC list and the rest of the html body.
	(splitting from <body>)
	"""

	text = htmlSplitter(html, 'body')

	if not '<div id="TOC">' in text:
		return '', text 
	
	text = text.split('<div id="TOC">')[1]
	text_parts = text.split('</div>')
	body = text_parts[1]
	toc = text_parts[0]
	toc = toc.splitlines()
	toc = [line for line in toc if line]
	toc = toc[1:-1] # remove first <ul> and last </ul>
	toc = "".join(toc)

	return toc, body


def findTitleHtml(filepath=None, pandocpath=None, text_md=None, text_html=None, continueh1=False):
	"""Find the title in HTML. First with <title>, then first <h1>"""

	the_title = ""
	if not filepath and text_md is None and text_html is None:
		# how do you me want to work!?!?!
		return the_title

	if filepath:
		the_title = path_delExtension(path_getFilename(filepath))

	if pandocpath is None and text_md is None and text_html is None:
		#why did you even bother....
		return the_title

	if text_html is None and text_md is None and filepath is None:
		# I dont do magic 
		return the_title

	if text_html is None:
		if text_md is None:
			text_md = cmd_open_file(filepath)

		if not filepath.endswith(".html"):
			command = [pandocpath, '--standalone', '-t', 'html']
			text_html = run_subprocess(command, True, text_md)
		else:
			text_html = text_md

	html_pieces = text_html.split("<body>")
	title_html = html_pieces[0].split("<title>")[1].strip()
	title_html = title_html.split("</title>")[0].replace(os.linesep, '')

	if title_html:
		return title_html

	if continueh1:
		title_h1 = htmlSplitter(html_pieces[1], "h1", special_start="<h1 ", find=True)
		if not title_h1:
			return the_title

		return title_h1.split(">")[1]

	return the_title

def htmlSplitter(text, tag, special_start=None, find=False):
	
	tpl_start = "<" + tag + ">"
	if special_start:
		tpl_start = special_start

	tpl_end = "</" + tag + ">"

	splitting = text.split(tpl_start)
	if find:
		if len(splitting) <= 1:
			return None 

	return splitting[1].split(tpl_end)[0]

def extractMdLinks(text, extension="md"):
	"""Extract markdown links in text with extension. 
	:text list 
	:extension the allowed extension
	:return a nested list. holder(title, link)
	"""

	list_links = list()

	expr = "\[(.+?)?\]\((.+?\.(" + extension + "))\)"
	expr = r'' + expr

	for line in text:
		
		matches = re.findall(expr, line)
		for m in matches:
			title = m[0]
			link  = m[1]
			if [title, link] not in list_links:
				list_links.append([title, link])

	return list_links

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

if __name__ == '__main__':

	args = get_args()

	print ("\n  ------------------ STARTING ------------------------------")
	CONFIG = prepare_args(args)

	# steady, ready, go!
	Pandy(CONFIG)
	
	print ("\n  ------------------ DONE! :) ------------------------------")