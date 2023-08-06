'''
Usage: Pass in the filenames of documents as script arguments, e.g.
   python preprocess.py docs/*

'''

import sys, os, re, lxml.html

from collections import Counter
from lxml.html.clean import clean_html

word_pattern = re.compile("([\w]+)")

document_words = []

for filename in sys.argv[1:]:
	if os.path.isfile(filename):
		print "\nInput file: %s" % filename
		
		input_file = open(filename, 'r')
		contents = input_file.read()
		input_file.close()
		
		contents = clean_html(contents)
		parsed_contents = lxml.html.document_fromstring(contents).body

		text = parsed_contents.text_content().lower()
		words = re.findall(word_pattern, text)
		
		'''A Counter is a dict subclass for counting hashable objects.
		It is an unordered collection where elements are stored as dictionary
		keys and their counts are stored as dictionary values'''
		word_counter = Counter()
		word_counter.update(words)
		document_words.append( (filename, word_counter) )
		
		print "Unique words: %d" % len(word_counter.values())
		print "Total words: %d" % sum(word_counter.values())
		
		# sanity check: print 10 most common words in each document
		print "Most common words:"
		for word, count in word_counter.most_common(10):
			print "\t%s : %d" % (word, count)
		
		# sanity check: print 10 least common words in each document
		print "Least common words:"
		for word, count in word_counter.most_common()[:-11:-1]:
			print "\t%s : %d" % (word, count)

print "\n\nWord counts calculated for %d documents." % (len(document_words))
