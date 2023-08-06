'''
Usage: Pass in the filenames of documents as script arguments, e.g.
   python preprocess.py docs/*

'''

import sys, os, re, lxml.html, cPickle, functools, urllib

from collections import Counter
from lxml.html.clean import clean_html
from pprint import pprint
from operator import itemgetter

import server_config

all_postings = {}
document_names = []

'''
This function is the entry point to the query logic.  Simply returns
the submitted terms or a simple message if non provided at the moment
'''
def runQuery(query_terms):
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

        
        if None not in query_posting_lists: # If all query terms were found in at least one document

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
                fileName = document_names[file_index].split('/')[-1]
                urlSafeName = urllib.quote(fileName)
                urlName = "<a href='docs/%s'>%s</a>" % (urlSafeName, fileName) 
                result_string += "%s (score: %d) <br>" % (urlName, score) 

        return result_string

    else:
        return "No Query Entered"



def parseDocs(file_path):

    token_pattern = re.compile("([\w]+)")

    onlyfiles = [ os.path.join(file_path,f) for f in os.listdir(file_path) if os.path.isfile(os.path.join(file_path,f)) ]


    for filename in onlyfiles:

        if os.path.isfile(filename):
            print "Input file: %s" % filename
            document_names.append(filename)
            
            # Suppose filename is	'docs/Acadia_National_Park.htm'
            # filename_nodir:		'Acadia_National_Park.htm'
            # filename_noext:		'Acadia_National_Park'
            filename_nodir = os.path.basename(filename)
            filename_noext = os.path.splitext(filename_nodir)[0]
            
            
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
            word_counter.update(tokens) # This is what actually puts the words from this
            # document into the Counter object. It accummulates the word counts but does
            # not retain information about positions within the document, etc.
            
            for term, term_frequency in word_counter.items():
                posting = Counter({document_names.index(filename): term_frequency})
                if all_postings.get(term) == None:
                    all_postings.update({term: posting})
                else:
                    all_postings[term] += posting
            
            # We're now done building this document's word_counter.

            # We don't need to output the following statistics every time we reparse
            # the documents. This is just for our own evaluation of the dataset if/when
            # the document collection changes.
            # print "Unique terms: %d" % len(word_counter.values())
            # print "Total tokens: %d\n" % sum(word_counter.values())


    print "\nDone processing %d documents.\n" % (len(document_names))
    
    # Use cPickle to store a reference copy of the collection-wide all_postings dictionary.
    # This may be used in the future to compare the results of different versions of parsing
    # and querying functions. Also, because we are pickling the data structure, it can be
    # directly read into a usable Python object.
    
    if not os.path.isfile(os.path.join(os.getcwd(), "serialized_postings.txt")):
        # Don't bother to regenerate the file if it already exists.
        with open(os.path.join(os.getcwd(), "serialized_postings.txt"), 'w') as output_file:
            cPickle.dump(all_postings, output_file)

    return

# doc_totals = parseDocs(server_config.document_path)

print "Initial Parsing Complete - Server Coming Up..."


