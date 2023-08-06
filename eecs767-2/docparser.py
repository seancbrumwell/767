'''
Usage: Pass in the filenames of documents as script arguments, e.g.
python preprocess.py docs/*

'''

import sys, os, re, lxml.html, functools, urllib, math, cProfile, pstats, numpy

from collections import Counter
from lxml.html.clean import clean_html
from pprint import pprint
from operator import itemgetter

import server_config

all_postings = {}
idf_dict = {}
totals = {'sorted_terms': [], 'document_names': []}


def prettyFloat(f):
	return "%3.4f" % f


def runQuery(query_terms):
	''' This is where to put the query function.
		query_terms is already split into individual terms.'''

	if query_terms:
		# using cProfile module to collect more detailed profiling statistics
		# to turn off, remove lines with:
		#       profiler.enable()
		#       profiler.disable()
		#       ps = pstats.Stats(profiler).strip_dirs().sort_stats('cumulative', 'module')
		#       ps.print_stats()

		profiler = cProfile.Profile()
		profiler.enable()

		query_terms = set(query_terms)  # Take the unique terms in the query
		query_terms = sorted(query_terms)  # Sort the unique terms alphabetically
		query_terms = [t for t in query_terms if t in totals['sorted_terms']]  # Ignore query terms that match no documents at all

		print "\n> runQuery: %s" % " ".join(query_terms)

		result_string = ""
		query_postings_dict = {}
		candidate_docs = set([])

		for query_term in query_terms:
			print "query term '%s'" % query_term
			post = all_postings.get(query_term)
			if post is not None:
				query_postings_dict[query_term] = post
				candidate_docs.update(post.keys())

		candidate_vectors = dict.fromkeys(candidate_docs)

		for doc_index in sorted(candidate_docs):
			# for each term t's posting list in query_postings_dict, all_postings[t][doc_index]
			# is the term frequency for term t in the document at doc_index.  if term t
			# doesn't occur in the document at doc_index, posting_list[doc_index] will be 0.

			# idf_dict[t] was already computed and stored as part of parseDocs()

			doc_vector = [all_postings[t][doc_index] * idf_dict[t] for t in totals['sorted_terms']]

			candidate_vectors[doc_index] = doc_vector

		#print "\ncandidate documents:"
		#for index, doc_vector in candidate_vectors.items():
			#if len(doc_vector) < 15:
				#print index, map(lambda x: "%3.4f" % x, doc_vector)

		query_vector = []
		for t in totals['sorted_terms']:
			# We're not going to acknowledge multiple occurrences of a term in a query,
			# so the "term frequency" will be 1*idf(term) or 0.
			if t in query_terms:
				query_vector.append(idf_dict[t])
			else:
				query_vector.append(0)

		query_results = []
		qvec = numpy.array(query_vector)
		for doc_index, vec in candidate_vectors.items():
			sim = computeSimilarity(numpy.array(vec), qvec)
			query_results.append((doc_index, sim))

		query_results_sorted = sorted(query_results, key=itemgetter(1), reverse=True)

		result_string += "<br>Documents matching query:<br><br>"

		for (file_index, score) in query_results_sorted:
			fileName = totals['document_names'][file_index].split('/')[-1]
			urlSafeName = urllib.quote(fileName)
			urlName = "<a href='docs/%s'>%s</a>" % (urlSafeName, fileName)
			result_string += "%s (score: %3.4f) <br>" % (urlName, score)
			print "%s (score: %3.4f)" % (fileName, score)

		profiler.disable()
		ps = pstats.Stats(profiler).strip_dirs().sort_stats('cumulative', 'module')
		ps.print_stats()
		return result_string

	else:
		return "No Query Entered"


def computeSimilarity(a1, a2):
	""" Similarity normalized for the magnitude of the document and query vectors.
	If a query term appears a number of times in a very long document, the contribution
	to the similarity measure is not as great as if the term appeared the same number of
	times in only a short document. """

	if a1.size != a2.size:
		# The dimensionality of the two vectors should be the same
		return None

	norm_product = numpy.linalg.norm(a1) * numpy.linalg.norm(a2)
	if norm_product > 0:
		return a1.dot(a2) / norm_product
	else:
		return 0

def computeIDF(docs, term, posting_list):
	# document frequency (how many documents contained the term)
	df = float(len(posting_list))

	# n_docs is the total number of documents
	n_docs = len(docs)

	# idf(t) = log10( n_docs / df(t) )
	idf = math.log(n_docs / df, 10)
	return idf


def runBooleanQuery(query_terms):
	''' This is where to put the query function.
		query_terms is already split into individual terms.'''

	if query_terms:

		result_string = ""

		query_posting_lists = [all_postings.get(query_term) for query_term in query_terms]
		for query_term_index, term in enumerate(query_terms):
			# Get the posting list for this query term
			posting_list = query_posting_lists[query_term_index]

			# Display document frequency (how many documents contained the term), and term frequency
			# (how many times in each document). Nothing new actually getting computed here;
			# it is just being displayed for informational purposes.
			if posting_list is not None:
				result_string += "<br>\"%s\" found in %d documents<br>" % (term, len(posting_list))
			else:
				result_string += "No documents matched \"%s\"<br>" % term

		if None not in query_posting_lists:  # If all query terms were found in at least one document

			# This is where we combine the posting lists for each individual
			# query term, by takikng the intersection of Counter objects to see which (if any)
			# documents contained *all* our query terms.

			# The lambda function used in the following reduce is using the intersection (A & B)
			# method of the Counter class. This takes all the elements that are in both Counters
			# and records as a count: (the smaller count number in either Counter)
			query_results = functools.reduce(lambda v1,v2: v1 & v2, query_posting_lists)

			# Sort the (document, score) pairs in descending order by score, so the highest scored
			# pairs come first.
			query_results_sorted = sorted(query_results.items(), key=itemgetter(1), reverse=True)

			result_string += "<br>Documents matching entire query:<br><br>"

			for (file_index, score) in query_results_sorted:
				fileName = totals['document_names'][file_index].split('/')[-1]
				urlSafeName = urllib.quote(fileName)
				urlName = "<a href='docs/%s'>%s</a>" % (urlSafeName, fileName)
				result_string += "%s (score: %d) <br>" % (urlName, score)

		return result_string

	else:
		return "No Query Entered"


def parseDocs(file_path):
	token_pattern = re.compile("([\w]+)")

	onlyfiles = [os.path.join(file_path, f) for f in os.listdir(file_path) if os.path.isfile(os.path.join(file_path, f))]
	onlyfiles = sorted(onlyfiles)

	for filename in onlyfiles:
		if os.path.isfile(filename) and filename not in totals['document_names']:
			print "Input file: %s" % filename
			totals['document_names'].append(filename)

			input_file = open(filename, 'r')
			contents = input_file.read()
			input_file.close()

			contents = clean_html(contents)
			parsed_contents = lxml.html.document_fromstring(contents).body

			text = parsed_contents.text_content().lower()
			tokens = re.findall(token_pattern, text)

			'''A Counter is a dict subclass for counting hashable objects.
			It is an unordered collection where elements are stored as dictionary
			keys and their counts are stored as dictionary values'''

			word_counter = Counter()
			# This is what actually puts the words from this document into the Counter object.
			# It accummulates the word counts but does not retain information about positions
			# within the document, etc.
			word_counter.update(tokens)

			for term, term_frequency in word_counter.items():
				posting = Counter({totals['document_names'].index(filename): term_frequency})
				if all_postings.get(term) is None:
					all_postings.update({term: posting})
				else:
					all_postings[term] += posting

			# We're now done building this document's word_counter.

	totals['sorted_terms'] = sorted(all_postings.keys())

	# Compute and store IDF values (only happens once, not once per document)
	for term in totals['sorted_terms']:
		posting_list = all_postings[term]
		idf_dict[term] = computeIDF(totals['document_names'], term, posting_list)

	print "\nDone processing %d documents." % (len(totals['document_names']))

	return


print "Initial Parsing Complete - Server Coming Up..."
