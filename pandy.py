# "Wrapper" for Pandoc (python 2.7)
# pandy [from] [to] [file] [other options]

import argparse
import sys
import os
import subprocess

# =====================
# ==== config vars ====
# =====================

pandocPath = 'pandoc'
template   = 'github.html'
highlight  = 'zenburn' # options: pygments (the default), kate, monochrome, espresso, zenburn, haddock, tango
slides     = 'dzslides' # dzslides (html5),  slidy
dataDir    = "C:\Program Files\Pandoc" # empty for default

print "\n----------------------------------------------\n"

FormatsFrom = ["md","html"]
FormatsTo = ["md","html","doc","epub","odt","slides","slide","mediawiki","mw"]

# ===================
# ==== functions ====
# ===================

def exit():
	sys.exit()

def args():
	parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description='''

 [from] 
   md, html 
   
 [to]
   md 
 	html, docx (as doc), slides (or slide), epub, mediawiki (or mw), odt
   html
 	markdown (as md), docx (as doc), epub, odt
 
 [file] file with extension or folder
 
 [other options] (below)''', usage='pandy [from] [to] [file] [other options]')
	parser.add_argument("ffrom", help=argparse.SUPPRESS)
	parser.add_argument("to", help=argparse.SUPPRESS, nargs='+')
	parser.add_argument("file", help=argparse.SUPPRESS)
	parser.add_argument("-nohigh", help="no highlight", action='store_true')
	parser.add_argument("-toc", help="include TOC", action='store_true')
	parser.add_argument("-self", help="self contained file", action='store_true')
	parser.add_argument("-hide", help="e-mail obfuscation (default none, true = references)", action='store_true')
	parser.add_argument("-css", help="External CSS")
	parser.add_argument("-merge", help="Merge files in folder into one. Gets the name of the specified folder", action='store_true')
	
	return vars(parser.parse_args()) # to dict
	
def checkFormats(formatFrom, formatTo):	
	if not formatFrom in FormatsFrom: 
		print "FROM format not recognised. Exiting"
		exit()
	for item in formatTo:
		if not item in FormatsTo: 
			print "TO format not recognised. Exiting"
			exit()


def isFrom(format, file):
	toReturn  = list()

	if format == "md":
		toReturn = ["-f", "markdown+mmd_title_block+link_attributes"]
	if format == "html":
		toReturn = ["-f", "html"]

	if file is not False:
		toReturn.append(file)

	return toReturn

def goTo(format, file, path):
	completePath = os.path.join(path,file)
	
	if format == "html":
		return ["-t", "html", "-o", completePath + ".html", "--template="+template]
	if format == "doc":
		return ["-t", "docx", "-o", completePath + ".docx"]
	if format == "epub":
		return ["-t", "epub", "-o", completePath + ".epub"]
	if format == "odt":
		return ["-t", "odt", "-o", completePath + ".odt"]	
	if format in ["slides", "slide"]:
		return ["-t", slides, "-o", completePath + ".html"]
	if format in ["mediawiki","mw"]:
		return ["-t", "mediawiki", "-o", completePath + ".mw"]
	if format == "md":
		return ["-t", "markdown+mmd_title_block+link_attributes", "-o", completePath + ".md"]
	
# get file without extension
def getFilename(file):
	tmp = os.path.basename(file)
	tmp = tmp.rpartition(".")
	
	return tmp[0]

def getPath(file):
	return os.path.dirname(file)

def getLastDir(path):
	return os.path.split(path)[1]

def cycleTrough (elements):
	theFiles=list()
	
	if os.path.isfile(elements):
		theFiles.append(elements)
	else:
		for root, subFolders, files in os.walk(elements):
			for filename in files:
				filePath = os.path.join(root, filename)
				theFiles.append(filePath)
	return theFiles	
	
# Do the Pandoc
def pandoc(command):
	return subprocess.check_call(command)

def doThePandoc(elements, fileFrom, fileTo, command):
	global mergeFiles

	files = cycleTrough(elements)
	newcommand = command
	
	if mergeFiles:	
		name = getLastDir(elements)
		path = getPath(elements)

		newcommand = newcommand + isFrom(fileFrom, False)
		newcommand = newcommand + files 

		for item in fileTo:
			newcommand = newcommand + goTo(item, name, path)

			pandoc(newcommand)

	else:
		for file in files:	
			fileNoExt = getFilename(file)
			path = getPath(file)

			newcommand = newcommand + isFrom(fileFrom, file)
		
			for item in fileTo:
				newcommand = newcommand + goTo(item, fileNoExt, path)
		    	
		    	pandoc(newcommand)
			newcommand = command

# ===============================
# ==== Finally, the program ====
# ==============================

args = args()

fileFrom   = args["ffrom"]
fileTo     = args["to"]
fileThe    = args["file"]
mergeFiles = args['merge']

# check if fileThe is a directory, if it's -> allow mergeFiles
if not os.path.isdir(fileThe) and mergeFiles is True:
	mergeFiles = False

# check input
checkFormats(fileFrom, fileTo)

otherOptions = list()

if args["nohigh"]:
	otherOptions.append("--no-highlight")
if args["toc"]:
	otherOptions.append("--toc")
if args["self"]:
	otherOptions.append("--self-contained")
if args["hide"]:
	otherOptions.append("--email-obfuscation=references")
if args["css"]:
	otherOptions.append("--css="+args.css)

if dataDir:
	dataDir = "--data-dir=" + dataDir
	
basicOptions = [pandocPath, "-s", dataDir, "--highlight-style=" + highlight]

command = basicOptions # Command holder
command += otherOptions

doThePandoc(fileThe, fileFrom, fileTo, command)

print "               And we're done :) "
print "\n----------------------------------------------"
