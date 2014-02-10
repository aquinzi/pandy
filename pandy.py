# "Wrapper" for Pandoc (python 2.7): pandy [file/folder] [from] [to] [other options]
# -*- coding: utf-8 -*-

# tested for pandoc 1.12.3

"""
	Basically takes a file/folder, input the markup to convert from, the output markup and run it through pandoc.

	More explained:
	From a file/folder/.list, input the "from" markup and the output format, which can be a list separated with spaces. Formats are stripped down to the most common ones:

		from: docbook, html, json, latex, markdown, markdown_github, markdown_mmd, markdown_phpextra, markdown_strict, mediawiki, mw, opml, rst, textile
		output: all the above +  asciidoc, beamer, docx (or doc), epub, epub3, fb2, html5, odt, opendocument (or opendoc), pdf, plain, rtf, slides (or slide)

		 All "markdown"s can be entered as "md". So: markdown -> md; markdown_github -> md_github; etc

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

	admonitions with my own markup 

	[class/type:optional title]
	  * markdown
	  * super
	  * content

	And these markdown extensions are automatically added: 'link_attributes', 'hard_line_breaks'

	You can also include a tag for toc ([TOCME]) to have that file with a toc instead of remembering to enter --toc. (It just adds it automatically after searching the file, no magic here)

	For book: you can create your own index and have "wikiLinks" as [](file|nice_file.txt). It will render as [title of file](nice_file.html) 

	If you don't like setting the options in the CLI, or having a script, you can create your configuration in a key=value file (like ini). Example: myconfiguration.ini contains:

	PANDOC_DATA_DIR = "C:\Program Files\Pandoc"
	TEMPLATE = 'github.html'
	HIGHLIGHT= 'zenburn'

	Specify the configuration file with --config (the extension doesn't matter, and INI headers are ignored. Don't worry)

	-------------------------

	extensions enabled by default (pandoc): 

		headerid -> auto_identifiers; 
		Attribute Lists -> (only headers) header_attributes; 
		fenced_code_blocks (~~~~ & ```) and attributes (#mycode .haskell .numberLines startFrom="100")  or ```haskell; 
		definition_lists; 
		tables: simple_tables, multiline_tables, grid_tables, pipe_tables (like pymd); 
		meta: pandoc_title_block, yaml_metadata_block; 
		smart strong -> intraword_underscores; 
		footnotes (no !DEF); 
		inline_notes; 
		citations

	markdown variants

		markdown_phpextra (PHP Markdown Extra)
		footnotes, pipe_tables, raw_html, markdown_attribute, fenced_code_blocks, definition_lists, intraword_underscores, header_attributes, abbreviations.

		markdown_github (Github-flavored Markdown)
		pipe_tables, raw_html, tex_math_single_backslash, fenced_code_blocks, fenced_code_attributes, auto_identifiers, ascii_identifiers, backtick_code_blocks, autolink_bare_uris, intraword_underscores, strikeout, hard_line_breaks

		markdown_mmd (MultiMarkdown)
		pipe_tables raw_html, markdown_attribute, link_attributes, raw_tex, tex_math_double_backslash, intraword_underscores, mmd_title_block, footnotes, definition_lists, all_symbols_escapable, implicit_header_references, auto_identifiers, mmd_header_identifiers

		markdown_strict (Markdown.pl)
		raw_html
"""

from __future__ import print_function, unicode_literals
import subprocess
import argparse
import sys
import os
import codecs
import re

# ==============================
# ==== Remove if publishing ====
# ==============================

# Cool stuff to include someday:
# Enable/disble extensions from cli
# custom css/js: --include-in-header

MY_CONFIGS = {
	'PANDOC_DATA_DIR' : "C:\\Program Files\\Pandoc",
	'TEMPLATE': 'github_sidebartitles.html',
	'HIGHLIGHT': 'zenburn',
}


# ==============================
# ==== info & pandoc config ====
# ==============================

__version__ = "1.8.2"
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

_PY_VER = sys.version_info[0]

# pandoc's formats. Filtered to remove some that will never be used (by me)
# Includes some synonyms
_FORMATS_BOTHWAYS = [
	'docbook',
	'html',
	'json',
	'latex',
	'markdown', "md",
	'markdown_github', "md_github",
	'markdown_mmd', "md_mmd",
	'markdown_phpextra', "md_phpextra",
	'markdown_strict', "md_strict",
	'mediawiki', "mw",
	'opml',
	'rst',
	'textile',
	]
_FORMATS_OUTPUT   = [
	'asciidoc',
	'beamer',
	'docx', 'doc',
	'epub',
	'epub3',
	'fb2',
	'html5',
	'odt',
	'opendocument', 'opendoc',
	'pdf', #[*for pdf output, use latex or beamer and -o FILENAME.pdf] 
	'plain',
	'rtf',
	"slides", "slide", #options slides in another list
	]

_HIGHLIGHT_OPTIONS = ['pygments', 'kate', 'monochrome', 'espresso', 'zenburn', 
                     'haddock', 'tango']
_SLIDES_OPTIONS    = ['dzslides', 'slidy', 'reveal', 'slideous', 's5']

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
	'NAV_TITLE': False,  #For book, use title navigation
	'NAV_SIDEBAR': False,  #For book, sidebar with titles

	'EMAIL_HIDE': False, # e-mail obfuscation (default none, true = references)
	'BIBLIOGRAPHY': '',
	'HTML_VER': 'html5', # Output html5 instead of html4 (html)
	'TOC_TAG': '[TOCME]',
	}


class Pandy(object):
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


		onlyExts = tuple()
		if self.format_from == "html":
			onlyExts = (".html", ".htm")
		
		
		self.files = files_list(self.input, only_exts=onlyExts)

		self.format_from, self.format_to = check_synonyms(self.format_from, self.format_to)

		# make base pandoc command. 
		self.command.append(self.settings['PANDOC'])
		self.command.append('--standalone')  # complete html --standalone

		# Exclude: do not treat right now or already done
		exclude = ("FORMAT_TO", "FORMAT_FROM", "SOURCE", "OUTPUT_PATH", 
			"OUTPUT_FLAT", "MERGE", "SLIDES", "BOOK", "HTML_VER", "PANDOC" )

		# Add the options 
		for key, val in self.settings.items():
			if key in exclude:
				continue
			self.command += translate_argsPandoc(key, val)

		self.command += self._cmdFromToOut('f', self.format_from)

		# and run! 
		self.run()

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
			if len(self.files) < 3:
				print ("  Sorry, not available with that few files. ")
				exit()

			# merge
			if merge:
				print ("  Parsing files and merging ... \n")
				self._parseMerge()
			else:
				# book

				# First of all, check if there is an output path, if not use
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
						"The wiki links weren't parsed")

				print ("  Parsing files and making book ... \n")
				self._parseBook()

	def _getOutputPath(self, filepath):
		"""Get output path"""

		if not self.output:
			return path_delExtension(filepath)
	
		if self.settings['OUTPUT_FLAT'] or (not self.settings['OUTPUT_FLAT'] and filepath == self.input):
			return os.path.join(self.output, path_delExtension(path_getFilename(filepath)))
		else:
			return os.path.join(self.output, path_delExtension(filepath)[len(self.input) + 1:])

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

	def _singleFileProperties(self, filepath, cmd=None, specials=False):
		"""for book. Instead of object use this which returns a dictionary with:
		output path, input path, title and text. Does the file processing and gets the title and html

		cmd: the command as starting point 
		specials: check for abbreviations, admonitions, toc 
		"""

		#sketch
		properties = {
		          'path_output' : '',
		          'path_input' : '',
		          'title' : '',
		          'text' : '',
		          }

		if filepath:
			properties['path_input']  = filepath
			properties['path_output'] = self._getOutputPath(filepath) + ".html"

		properties['title'] = path_delExtension(path_getFilename(properties['path_output']))

		if not cmd:
			return properties

		# Magic begins! (Get title and (parsed) body)
		cmd = list(cmd) # make copy because list is mutable u_u

		# remove the --template, this way can extract title easily
		for index, item in enumerate(cmd):
			if not item.startswith("--template"):
				continue
			else:
				del cmd[index]
				break 
		
		# special treatment for specials 
		if specials:
			cmd_text, toc = if_special_elements(properties['path_input'], self.settings['TOC_TAG'])

			if toc and not "--toc" in cmd:
				cmd.append('--toc')
		else:
			cmd_text = None # just to have save one if-else. Old stdin = False 
			cmd.append(properties['path_input'])

		# add missing args:
		cmd += ['-t', 'html']

		minimum = run_subprocess(cmd, True, cmd_text)
		minimum = minimum.decode('utf-8')

		# get the body (this is to also have the metadata; otherwise, 
		# with --standalone it gets the body but not header-block)
		_, body, _ = minimum.split("body>")
		properties['text'] = body[0:len(body) - 2 ] # remove the </ part of tag	

		# get <title> content
		_, title, _ = minimum.split("title>")
		title = title[0:len(title) - 2 ] # remove the </ part of tag

		# check if has, otherwise find it!
		if title: 
			properties['title'] = title
		else: 
			tryme = findH1(properties['text'])
			
			if tryme:
				properties['title'] = tryme

		return properties

	def _bookNavigation(self, current_path, prev_path, prev_title, next_path, next_title):
		""" Makes the navigation links """

		navPre  = ""
		navNext = ""
		
		use_titles = self.settings['NAV_TITLE']

		if prev_path:
			prev_path = path_relative_to(prev_path, current_path)

			navLink = prev_title if use_titles else 'prev'			
			navPre  = '<a href="' + prev_path + '">&lt; '+ navLink + '</a>'

		if next_path:
			next_path = path_relative_to(next_path, current_path)

			navLink = next_title if use_titles else 'next'
			navNext = '<a href="' + next_path + '">' + navLink + ' &gt;</a>'

		index_url = path_relative_to(os.path.join(self.output, 'index.html'),
							current_path)

		return '<div class="nav">' + navPre + ' <a href="'+index_url+'">index</a> '\
				 + navNext + '</div>'

	def _wikiLinks(self, text):
		""" Process "wiki" links: [](file|file.md) to [file title](newpath.html).
		It must be a markdown file, opened before (string)
		"""

		def futureTitle(filepath):
			tmp = self._singleFileProperties(filepath, 
				[self.settings['PANDOC'], '-f', self.format_from, '--standalone'])

			return tmp['title']

		textNew = list()
		
		for line in text:
			if "](file|" in line:
				if line.find("[](file|") > -1: 
					linkedFileName = line[line.find("[](file|") + 8 : line.find(")")]

					if os.path.exists(linkedFileName):
						title = futureTitle(linkedFileName)
						if title: 
							line = line.replace("[](file|", "[" + title + "](")
					else:
						line = line.replace("[](file|", "[" + linkedFileName + "](")

				else:
					# has custom title. Delete file| and find output path
					linkedFileName = line[line.find("](file|") + 7 : line.find(")")]
					line = line.replace("](file|", "](")

				# finds the output link and replaces
				outputPath = self._getOutputPath(linkedFileName) + ".html"
				line       = line.replace(linkedFileName, outputPath)
			
			elif "[](" in line:
				# if it has nothing but there's no file| tag and it's an existing file, 
				# put the filename as title link
				linked_path = line.split("[](")[1]
				if os.path.exists(linked_path):
					linked_path = path_getFilename(linked_path.split(")")[0])
					line = line.replace("[](", "[" + linked_path + "](")

			textNew.append(line)

		return textNew

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

				if not stdin:
					newcommand += is_from + cmd_to + cmd_out
					run_subprocess(newcommand)
				else:
					newcommand += cmd_to + cmd_out
					run_subprocess(newcommand, True, is_from)
				
	def _parseMerge(self):
		"""  pandoc already has a merge command when specified multiple files. 
		Special treatment for HTML output """

		if not self.output:
			self.output = os.getcwd()

		name = path_lastDir(self.input)
		path = os.path.join(self.output, name)
		
		for ext in self.format_to:
			command_base = list(self.command)

			cmd_to  = self._cmdFromToOut('t', ext)
			cmd_out = self._cmdFromToOut('o', ext, path) 

			if not ext == "html":
				command_base += [self.files] + cmd_to + cmd_out + ['--metadata=title:' + name]
				run_subprocess(command_base)
			else:

				# remove template to have less clutter
				template = ""
				for index in range(len(command_base)):
					if command_base[index].startswith("--template"):
						template = command_base[index]
						del command_base[index]
						break 

				if "--standalone" in command_base:
					wasStandalone = True 
				else:
					wasStandalone = False 

				# activate default template to have TOC
				if "--toc" in command_base:
					wasTOC = True 
					command_base.append("--template=default.html")
				else:
					wasTOC = False
					#remove everything to make it a fragment
					if wasStandalone:
						command_base.remove("--standalone")

				# now process
				merged_files = ""
				all_bodies   = ""
				all_tocs     = ""

				for thisFile in self.files:
					newcommand = list(command_base)
					new_text, toc = if_special_elements(thisFile, self.settings['TOC_TAG'])				
					newcommand += cmd_to

					new_text = run_subprocess(newcommand, True, new_text)

					if wasTOC:
						text = new_text.split("<body>")[1]					
						text = text.split("</body>")[0]
						text = text.split('<div id="TOC">')[1]
						text_parts = text.split('</div>')
						toc = text_parts[0]
						body = text_parts[1]
						toc = toc.splitlines()
						toc = [line for line in toc if line]			
						toc = toc[1:-1] # remove first <ul> and last </ul>
						toc = "".join(toc)

						all_tocs   += toc 
						all_bodies += body 
					else:
						merged_files += new_text

				# go back to full HTML
				if wasTOC:
					command_base.remove("--template=default.html")
					all_tocs = '<div id="TOC">\n' + all_tocs + '\n</div>'
					merged_files = all_tocs + all_bodies
				
				if wasStandalone:
					command_base.append("--standalone")

				if template:
					command_base.append(template)

				# finally save
				newcommand = command_base + cmd_to + cmd_out + ['--metadata=title:' + name]
				run_subprocess(newcommand, True, merged_files)

	def listTitles(self):
		"""Get a titles list (html) of all the files. 
		For Sidebar title list
		"""

		filesTotal = len(self.files)
		bookIndex = ""

		i = 0
		while i < filesTotal:
			newcommand = list(self.command)
			file_current = self._singleFileProperties(self.files[i], newcommand, specials=True)

			relative = path_relative_to(file_current['path_output'], self.output, True)
			bookIndex += '<li><a href="' + relative + '">' + \
							file_current['title'] + '</a></li>'
			i += 1

		self.listTitles = "<ul>" + bookIndex + "</ul>"


	def _parseBook(self):
		"""Make a book with navigation between files """

		filesTotal = len(self.files)
		self.listTitles()

		i = 0
		while i < filesTotal:
			newcommand = list(self.command)

			if self.settings['NAV_SIDEBAR']:
				newcommand.append('--variable=book_navigation:'+str(self.listTitles))
			
			# prepare prev, current and next files
			if i == 0:
				file_previous = self._singleFileProperties("")

			print (" Converting: " + path_getFilename(self.files[i]))
			file_current = self._singleFileProperties(self.files[i], newcommand, specials=True)
			
			if (i + 1) < filesTotal:
				file_next = self._singleFileProperties(self.files[i + 1], newcommand, specials=True) 
		
			# book navigation
			navigation = self._bookNavigation(file_current['path_output'], 
				                          file_previous['path_output'], file_previous['title'], 
				                          file_next['path_output'], file_next['title'] )
			#build new text
			text_new = navigation + file_current['text'] + navigation

			newcommand += ['-t', 'html', '-o', file_current['path_output']]
			
			# "hack" to have the file or title in the title (but using --title-prefix instead 
			# of --metadata=title:) so it doesnt print in body (and you won't notice 
			# the - at the end, shut up)
			newcommand.append('--title-prefix=' + file_current['title'])

			path_mkdir(path_get(file_current['path_output']))
			file_current['text'] = run_subprocess(newcommand, True, text_new)
		
			file_previous = file_current
			file_current  = file_next
			file_next     = self._singleFileProperties("")

			i += 1

		# Process index
		index_ouput = os.path.join(self.output, "index.html")
		index_file = self.settings['FILE_INDEX']


		if index_file and os.path.exists(index_file):
			index_text = cmd_open_file(index_file)
			index_text = index_text.split("\n")
			index_text = self._wikiLinks(index_text)

			index_text = os.linesep.join(n for n in index_text)
			newcommand = list(self.command)
		else:
			#build index
			index_text = self.listTitles
		
		newcommand += ['-o', index_ouput, '--metadata=title:Index']
		run_subprocess(newcommand, True, index_text)

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



# =========================
# == methods: prettify ====
# =========================

def insert_newlines(string, every=64):
    lines = []
    for i in range(0, len(string), every):
        lines.append(string[i:i + every])

    return '\n'.join(lines)

def help_replaceStringFormats(string, placeholders):
	"""Replaces placeholders in string, with _FORMATS_BOTHWAYS and _FORMATS_OUTPUT
	
	string      : complete string 
	placeholders: list of placeholders; what to replace -> converts to list to join

	returns processed string 
	"""

	tmp = ""

	for placeholder in placeholders:
		the_choosen_one = placeholder[3:len(placeholder) - 3] # get the list name

		if the_choosen_one == "_FORMATS_OUTPUT":
			the_list = _FORMATS_OUTPUT
		
		if the_choosen_one == "_FORMATS_BOTHWAYS":
			the_list = _FORMATS_BOTHWAYS

		is_synom = False
		
		for f in the_list:

			if the_choosen_one == "_FORMATS_OUTPUT":
				is_synom = True if f in ["doc", "opendoc", "slide"] else False 

			if the_choosen_one == "_FORMATS_BOTHWAYS":
				if f.startswith("md"):
					continue 

				is_synom = True if f == 'md' else False 

			if is_synom:
				tmp += " (or " + f + ")"
			else:
				tmp += ", " + f

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
		#raise 
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

def files_get(path, only_exts=()):
	""" Get a list of files in dir. Returns list 
	:param:only_exts tuple to include only selected extensions (mainly for html pages saved
		locally (which has folders > images ) )
	""" 

	theFiles = list()

	if os.path.isfile(path):
		if os.path.exists(path):
			theFiles.append(path)
	else:
		for root, subFolders, files in os.walk(path):
			for filename in files:
				filePath = os.path.join(root, filename)

				if os.path.exists(filePath) and filePath.endswith(only_exts):
					theFiles.append(filePath)

	return theFiles	

def files_list(path, only_exts=None):
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
	
	return files_get(path, only_exts)

def cmd_open_write(path, mode):
	""" Create the open/write command according to python version 
	mode is: 'r' for read and 'w' for write
	"""

	if _PY_VER == 3:
		return open(path, mode, encoding='utf-8-sig')
	else:
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
				if value.lower() in ["true", "false"]:
					value = bool(value)
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
		answer = raw_input(msg + " Continue? (y/n) ")

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

def if_special_elements(file_path, toc_tag):
	"""open file (file_path) and process trough specials (admonitions, abbreviations, TOC tag)
	returns: text (regardless if changed or not ) and hasTOC (bool)
	"""
	
	with cmd_open_write(file_path, 'r') as input_file:
		text_list = input_file.readlines()

		hasTOC, text = find_TOCinFile(text_list, toc_tag)
		text = parse_admonitions(text)
		text = parse_abbreviations(text)

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

def parse_admonitions_taghtml(text):
	""" (old, keep for legacy) Find and parse my admonitions. 
	Input text: as list (just after open)
	returns parsed text as list

	Syntax:
	<admon "class/type" "optional title">
	  * markdown
	  * super
	  * content
	</admon>

	would be translated as div:
	<div class="admonition class/type">
	<p class="admonition-title"> Optional title </p>
	  * markdown
	  * super
	  * content
	</div>
	"""

	new_test = list()

	for line in text:
		if line.startswith("<admon ") or line.startswith("<admon>"):
			admon_info = line.split('"')
			new_str = '<div class="admonition'

			try:
				admon_info[1]
			except IndexError:
				pass 
			else:
				new_str += ' ' + admon_info[1]

			new_str += '">'  #close admon
			new_test.append(new_str)

			try:
				admon_info[3]
			except IndexError:
				pass
			else:
				new_test.append('\t<p class="admonition-title">' + admon_info[3] + '</p>')
			
		elif line.startswith("</admon>"):
			line = line.replace("</admon>", "</div>")
			new_test.append(line)

		else:
			new_test.append(line)

	return new_test

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
	placeholder with another string. Returns text (as list)
	"""

	hasTOC = False

	for index in range(len(text)):
		if text[index].startswith(placeholder):
			text[index] = text[index].replace(placeholder, replace_with)
			hasTOC = True 

	return hasTOC, text 


# =============================
# == methods: help parsing ====
# =============================

def findH1(text):
	"""Find first h1 in html """

	slices = text.split("<h1 ")

	if len(slices) <= 1:
		return None

	title = slices[1].split("</h1>")[0]
	if "<a href=" in title:
		#TOC inserts links in headers. gets id="adverbios"><a href="#adverbios">Adverbios</a>
		title = title.split(">")[2] 
		title = title[0:len(title) - 3] #remove </a
	else:
		title = title.split(">")[1] 

	return title

# =============================
# == methods: Args/options ====
# =============================

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
	option_file.add_argument("--index", help="Custom index file for book. Can use wiki links ", metavar="FILE")
	option_file.add_argument("--html4", help="Use html4 output instead of html5", action="store_true")
	help = "Slides format. Options: " + ", ".join(_SLIDES_OPTIONS) + ". Default: %(default)s"
	help = insert_newlines(help, 63)
	option_file.add_argument("--slides", help=help, choices=_SLIDES_OPTIONS, default=_DEFAULT_CONFIG['SLIDES'], metavar="")
	option_file.add_argument("--bib", help="Use bibliography file", metavar="FILE")

	exclusive = option_file.add_mutually_exclusive_group()
	exclusive.add_argument("--merge", "-m", action="store_true", help="Merge files.")
	exclusive.add_argument("--book", "-b", action="store_true", help="Make a book with navigation (next/prev) and index")

	style = parser.add_argument_group(' styling')
	style.add_argument("--css", help="External CSS", metavar="FILE")

	help = "Highlight style. Options: " + ", ".join(_HIGHLIGHT_OPTIONS) + ". Default: %(default)s"
	help = insert_newlines(help, 73)
	style.add_argument("--highlight", choices=_HIGHLIGHT_OPTIONS, default=_DEFAULT_CONFIG['HIGHLIGHT'], help=help, metavar="")
	style.add_argument("--highlight-no", help="No highlight", action='store_true')
	style.add_argument("--tpl", help="Template file. Can enter 'default' for pandoc's default.", metavar="FILE")

	other = parser.add_argument_group(' other')
	other.add_argument("--toc", "-t", help="include TOC", action='store_true')
	other.add_argument("--depth", help="TOC depth. Choices: 1, 2, 3, 4, 5, 6. Default: %(default)s", type=int, choices=[1, 2, 3, 4, 5, 6], default=_DEFAULT_CONFIG['TOC_DEPTH'], metavar="")
	other.add_argument("--hide", action='store_true', help="e-mail obfuscation (default none, true = references)")
	other.add_argument("--sections", action='store_true', help="Wrap sections in <sections>, attach identifiers instead of titles")

	other.add_argument("--nav", "-n", help="(For book) use titles in navigation", action="store_true")
	other.add_argument("--navside", help="(For book) Make a sidebar with titles", action="store_true")
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
		'nav': 'NAV_TITLE',
		'data_dir': 'PANDOC_DATA_DIR',
		'html4': 'HTML_VER',
		'header': 'FILE_HEADER',
		'footer': 'FILE_FOOTER',
		'index': 'FILE_INDEX',
		'depth' : 'TOC_DEPTH',
		'navside' : 'NAV_SIDEBAR',
		}

	#just convert to uppercase
	options_noNameChange = ('pandoc', 'highlight', 'slides', 'source', 'sections',
		             'format_from', 'format_to', 'toc', 'merge', 'book', 'highlight_no') 
	options_exclude = ('config')

	settings_args = dict()

	# transfer & translate
	for key, val in arg_dict.items():
		if key in options_noNameChange:
			settings_args[key.upper()] = val 
		else:
			if key in options_exclude:
				continue
			if not key == "html4":
				settings_args[argsToSettings[key]] = val 
			else:
				settings_args[argsToSettings[key]] = 'html'

	# re add config
	tmp = arg_dict['config']
	settings_args['config'] = tmp

	return settings_args
	
def prepare_args(arg_dict):
	""" Prepares the args to a nice config dictionary. Also reads the --config file """
	
	# complete missing options. (Args take over default)
	settings_final = dict(_DEFAULT_CONFIG)
	settings_final.update(arg_dict)

	if settings_final['config'] and os.path.exists(settings_final['config']):
		settings_file = get_ini(settings_final['config'])

		#join/update configs args with file. Config take precedence
		settings_final.update(settings_file)

	#remove config option (just because)
	del settings_final['config']

	# Check option belonging, replace special keys, etc 
	if settings_final['NAV_TITLE'] and not settings_final['BOOK']:
		print("  --nav only works with book. Skipping that option")
		settings_final['NAV_TITLE'] = False

	if settings_final['FILE_INDEX'] and not settings_final['BOOK']:
		print("  --index only works with book. Skipping that option")
		settings_final['FILE_INDEX'] = ""

	if settings_final['TEMPLATE'] == "NONE":
		settings_final['TEMPLATE'] = ""

	if not settings_final['TOC']:
		settings_final['TOC_DEPTH'] = False

	if settings_final['SOURCE'].endswith(".list"):
		print("  Keeping folder structure with .list not supported. Skipping option")
		settings_final['OUTPUT_FLAT'] = True 


	# if pdf, warn that needs latex 
	if "pdf" in settings_final['FORMAT_TO']:
		answer = msg_cli_yesno("  To convert to PDF needs LaTeX installed (and in PATH).")
		if not answer:
			exit()

	return settings_final



if __name__ == '__main__':

	args = get_args()

	print ("\n  ------------------ STARTING ------------------------------")
	CONFIG = prepare_args(args)

	if MY_CONFIGS and isinstance(MY_CONFIGS, dict):
		CONFIG.update(MY_CONFIGS)

	# steady, ready, go!
	Pandy(CONFIG)
	
	print ("\n  ------------------ DONE! :) ------------------------------")


# History (File Last Updated on $Date$ )

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
