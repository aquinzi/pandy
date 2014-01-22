import difflib # for testing
import pandy
import re

class TestMe(object):
	""" Do basic testing """

	tests_total  = 0
	tests_failed = 0

	def __init__(self):
		print ("Let's test! ")

		self.init_func(self.test_parsingAbbr)
		self.init_func(self.test_parsingAdmonition)
		self.init_func(self.test_findh1)
		
		self.finishing()

	def test_parsingAbbr(self):
		"""Parsing abbreviations """


		str_from = '''Some text with an ABBR and a REF. Ignore REFERENCE and ref.

			*[ABBR]: Abbreviation
			*[REF]: Abbreviation Reference
		'''
		str_from = str_from.replace('\t', '') # so can collapse string above
		str_shouldbe = 'Some text with an <abbr title="Abbreviation">ABBR</abbr> and a <abbr title="Abbreviation Reference">REF</abbr>. Ignore REFERENCE and ref.'

		str_from = str_from.split('\n')
		str_result = pandy.parse_abbreviations(str_from)
		str_result_bak = list(str_result)
		str_result = "".join(str_result)

		self.tests_total += 1
		drumroll = (str_result == str_shouldbe)
		self.print_result("Parsing abbreviations", drumroll)

		if not drumroll:
			str_shouldbe = str_shouldbe.split('\n')
			diff = difflib.ndiff(str_shouldbe, str_result_bak )

			for d in diff:
				print (d)

	def test_parsingAdmonition(self):
		""" Parsing admonitions """

		str_from = '''
			[info:Optional title]
				* markdown
				* super
				* content

			Content outside admon
		'''

		# so can collapse string above
		str_from = re.sub(r'^\t{0,3}(.+)', '\\1', str_from, flags=re.MULTILINE)

		str_shouldbe = '''
			<div class="admonition info">
			<p class="admonition-title">Optional title</p>
			* markdown
			* super
			* content
			</div>

			Content outside admon
		'''
		# so can collapse string above
		str_shouldbe = re.sub(r'^\t{0,3}(.+)', '\\1', str_shouldbe, flags=re.MULTILINE)

		str_from = str_from.split('\n')
		str_result = pandy.parse_admonitions(str_from)

		# so could collapse above
		"""
		for index in range(len(str_result)):
			if '"admonition-title">' in str_result[index]:
				str_result[index] = str_result[index].replace('\t<p class="admonition-title">', '<p class="admonition-title">')	
		"""	

		str_result_bak = list(str_result)
		str_result = "\n".join(str_result)

		self.tests_total += 1
		drumroll = (str_result == str_shouldbe)
		self.print_result("Parsing admonitions", drumroll)

		if not drumroll:
			str_shouldbe = str_shouldbe.split('\n')
			diff = difflib.ndiff(str_shouldbe, str_result_bak )

			for d in diff:
				print (d)

	def test_findh1(self):
		str_from_notoc = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
			<html xmlns="http://www.w3.org/1999/xhtml">
			<head>
			  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
			  <meta http-equiv="Content-Style-Type" content="text/css" />
			  <meta name="generator" content="pandoc" />
			  <title></title>
			  <style type="text/css">
			    html, body {
			        color: black;
			    }
			  </style>
			</head>
			<body class="normal">
			<div id="wrapper">
			<h1 id="adverbios">Adverbios</h1>
			<p>Los adverbios suelen estar delante del verbo o adjetivo que modifican. Segun el tipo de adjetivo las reglas de formacion de adverbios cambian:</p>

			<p>Otras formas para formar adverbios:</p>

			<h2 id="adverbios-intraducibles">Adverbios intraducibles</h2>
			<p>Algunas veces, se pueden encontrar adverbios con matices especiales o con adverbios que no tienen una traduccion clara. Los mas representativos:</p>

			</div>
			</body></html>"""

		str_from_toc = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
			<html xmlns="http://www.w3.org/1999/xhtml">
			<head>
			  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
			  <meta http-equiv="Content-Style-Type" content="text/css" />
			  <meta name="generator" content="pandoc" />
			  <title></title>
			  <style type="text/css">
			    html, body {
			        color: black;
			    }
			  </style>
			</head>
			<body class="normal">
			<div id="wrapper">
			<div id="TOC">
			<ul>
			<li><a href="#adverbios">Adverbios</a><ul>
			<li><a href="#adverbios-intraducibles">Adverbios intraducibles</a></li>
			</ul></li>
			</ul>
			</div>
			<h1 id="adverbios"><a href="#adverbios">Adverbios</a></h1>
			<p>Los adverbios suelen estar delante del verbo o adjetivo que modifican. Segun el tipo de adjetivo las reglas de formacion de adverbios cambian:</p>

			<p>Otras formas para formar adverbios:</p>

			<h2 id="adverbios-intraducibles"><a href="#adverbios-intraducibles">Adverbios intraducibles</a></h2>
			<p>Algunas veces, se pueden encontrar adverbios con matices especiales o con adverbios que no tienen una traduccion clara. Los mas representativos:</p>

			</div>
			</body></html>"""

		str_shouldbe = "Adverbios"

		toc_no = pandy.findH1(str_from_notoc)
		toc_yes = pandy.findH1(str_from_toc)

		self.tests_total += 1
		drumroll = (toc_no == str_shouldbe)
		self.print_result("Finding H1, no TOC", drumroll)

		if not drumroll:
			print (" It should be: " + str_shouldbe)
			print ("But got " + toc_no)

		self.tests_total += 1
		drumroll = (toc_yes == str_shouldbe)
		self.print_result("Finding H1, with TOC", drumroll)

		if not drumroll:
			print (" It should be: " + str_shouldbe)
			print ("But got " + toc_yes)		

	def finishing(self):
		print ("\n\n------------------------------- ")
		print ("Total tests: {} Failed: {}".format(self.tests_total, self.tests_failed))
		print ("\nThank you :) ")
		exit()

	def print_function_name(self, func):

		print ("\n" + func.__name__ )

	def print_result(self, msg, result):

		if result:
			result = " ok "
		else:
			result = " error "
			self.tests_failed += 1

		print (msg , " ............. " + result)

	def init_func(self, func):
		self.print_function_name(func)
		func()

if __name__ == '__main__':
	TestMe()