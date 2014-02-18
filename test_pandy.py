#! python3
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
		self.init_func(self.test_internallinks)
		self.init_func(self.test_wikilinks)
		self.init_func(self.test_findTitleMd)
		
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
		drumroll = compare('string', str_result, str_shouldbe)
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

		str_result_bak = list(str_result)
		str_result = "\n".join(str_result)

		self.tests_total += 1
		drumroll = compare('string', str_result, str_shouldbe)
		self.print_result("Parsing admonitions", drumroll)

		if not drumroll:
			str_shouldbe = str_shouldbe.split('\n')
			diff = difflib.ndiff(str_shouldbe, str_result_bak)

			for d in diff:
				print (d)

	def test_internallinks(self):
		""" Internal links (old wikilinks)"""

		md_from = list()
		md_from.append('  * [:nocionesbasicas][]')
		md_from.append('  * [Greetings](greetings.md)')
		md_from.append('  * [El verbo ser](desu.md)')
		md_from.append('  * [Tiempo](tiempo.md)')
		md_from.append('  * [](yup.md)')
		
		md_to = list()
		md_to.append('  * [:nocionesbasicas][]')
		md_to.append('  * [Greetings](greetings.html)')
		md_to.append('  * [El verbo ser](desu.html)')
		md_to.append('  * [Tiempo](tiempo.html)')
		md_to.append('  * [](yup.html)')

		result = pandy.parse_internalLinks(md_from)

		self.tests_total += 1
		drumroll = compare('list', result, md_to)
		self.print_result("Parsing internal links", drumroll)

		if not drumroll:
			diff = difflib.ndiff(md_to, result)

			for d in diff:
				print (d)

	def test_wikilinks(self):
		"""Parsing wikilinks """

		md_from = ['Un poco de [:nocionesbasicas.md][], despues [:greetings][saludamos]. Un [:invalid][] y otro [:invalid.md][invalid link]']
		md_to = ['Un poco de [Nociones Basicas][nocionesbasicas.md], despues [saludamos][greetings]. Un [:invalid][] y otro [:invalid.md][invalid link]']

		md_to_references_list = [
  		    '[nocionesbasicas.md]: nocionesbasicas.html',
  		    '[greetings]: greetings.html',
  		    ]

		tmp_refs = {
			'nocionesbasicas|nocionesbasicas.md': {
				'output' : 'nocionesbasicas.html', 'title': 'Nociones Basicas'
			},
			'greetings': {
				'output' : 'greetings.html', 'title': 'Greetings'
			}
		}

		result_text, result_refs = pandy.parse_wikilinks(md_from, this_references=tmp_refs)
		self.tests_total += 1

		drumroll = compare('list', result_text, md_to)
		self.print_result("Parsing wikilinks", drumroll)
		if not drumroll:
			diff = difflib.ndiff(md_to, result_text)

			for d in diff:
				print (d)

		self.tests_total += 1
		drumroll = compare('list', result_refs, md_to_references_list)
		self.print_result("Comparing references", drumroll)
		if not drumroll:
			diff = difflib.ndiff(md_to_references_list, result_refs)

			for d in diff:
				print (d)	

	def test_findTitleMd(self):
		"""Find title in md"""

		shouldbe = "Tiempo"


		# pandoc block
		md_from = [
		'% Tiempo',
		'% author ',
		'',
		'Hora',
		'------',
		'',
		'La hora se construye con [contadores](contadores.md): ji para las horas y bun para los minutos. Se usa la [particula ni](particulas_ni.md) para hacer tiempo (como "at" en ingles).']

		result = pandy.findTitleMd(text_lines=md_from)
		self.tests_total += 1

		drumroll = compare('string', result, shouldbe)
		self.print_result("Finding title, pandoc block", drumroll)
		if not drumroll:
			print ("It should be: " + shouldbe)
			print ("But got: " + result)

		# YAML block 
		md_from = [
		'---',
		'title: Tiempo',
		'--- ',
		'',
		'Hora',
		'------',
		'',
		'La hora se construye con [contadores](contadores.md): ji para las horas y bun para los minutos. Se usa la [particula ni](particulas_ni.md) para hacer tiempo (como "at" en ingles).']

		result = pandy.findTitleMd(text_lines=md_from)
		self.tests_total += 1

		drumroll = compare('string', result, shouldbe)
		self.print_result("Finding title, YAML block", drumroll)
		if not drumroll:
			print (" It should be: " + shouldbe)
			print ("But got " + result)


		# markdown ATX headers 
		md_from = [
		'',
		'# Tiempo',
		'some text',
		'## Hora',
		'',
		'La hora se construye con [contadores](contadores.md): ji para las horas y bun para los minutos. Se usa la [particula ni](particulas_ni.md) para hacer tiempo (como "at" en ingles).']

		result = pandy.findTitleMd(text_lines=md_from)
		self.tests_total += 1

		drumroll = compare('string', result, shouldbe)
		self.print_result("Finding title, Atx headers", drumroll)
		if not drumroll:
			print (" It should be: " + shouldbe)
			print ("But got " + result)

		# markdown Setext headers
		md_from = [
		'',
		'Tiempo',
		'========= ',
		'sometext',
		'Hora',
		'------',
		'',
		'La hora se construye con [contadores](contadores.md): ji para las horas y bun para los minutos. Se usa la [particula ni](particulas_ni.md) para hacer tiempo (como "at" en ingles).']

		result = pandy.findTitleMd(text_lines=md_from)
		self.tests_total += 1

		drumroll = compare('string', result, shouldbe)
		self.print_result("Finding title, Setext headers", drumroll)
		if not drumroll:
			print (" It should be: " + shouldbe)
			print ("But got " + result)



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

def compare(what, compare1, compare2):
	""" what: 'string' or 'list'
	returns boolean
	"""

	if what in ("string", "str"):
		return (compare1 == compare2)

	if what == "list":
		if not len(compare1) == len(compare2):
			return False 

		total_items = len(compare1)
		for i in range(total_items):
			if not compare1[i] == compare2[i]:
				return False 
		return True 



if __name__ == '__main__':
	TestMe()