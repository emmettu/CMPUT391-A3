'''
Question 9: Assignment #3

I have been using test.txt, q1.txt, and q2.txt to test.txt.

test.txt has a '>' sign in it because I wanted to make sure I was grabbing it properly.
Its not actually a runnable query.
'''

import sys
import re


class SparqlQueryParser():

    def __init__(self, file_name):
        # Mappings
        self.prefix_map = {}
        self.variable_map = {}
        # These are the variables to output at the end
        self.output_variables = []
        # If False then we print the variables in output_variables, if True then we print *
        self.outputFLAG = False

        ### Open the file ###
        f = open(file_name, "r")
        self.lines = f.readlines()

        ### Parse the query ###
        self.splitlines = self.split_lines(self.lines)
        reduce_by = self.get_prefixes(self.splitlines)
        self.splitlines = self.splitlines[reduce_by:]
        self.determine_output(self.splitlines[0])
        self.splitlines = self.splitlines[1:]
        self.triples, filter_query = self.replace_and_add(self.splitlines)
        if filter_query:
            self.filter = self.parse_filter(filter_query)

         # I think these are all of the objects that are needed to actually run the query
            print self.filter # (filter-by, var1, var2) where 1 and 2 are the order in which they appear in the query

        print self.prefix_map
        print self.output_variables
        print self.outputFLAG
        print self.variable_map
        print self.triples

    def parse_filter(self, filter):
        # Reconstruct our Filter query
        filter_string = ''
        for i in filter:
            filter_string = filter_string + i
        # Remove 'FILTER' from front of line
        filter_string = filter_string[6:]

        # Deal with regex case
        if 'regex' in filter_string:
            count = 0
            for i in filter_string:
                if i == '(':
                    filter_string = filter_string[count:]
                else:
                    count += 1
            filter_string = filter_string.replace("(","").replace(")","")
            filter_params = filter_string.split(',')
            filter = ['regex', filter_params[0], filter_params[1]]

        # Deal with numeric constraint case
        else:
            count = 0
            for i in filter_string:
                if i == '(':
                    filter_string = filter_string[count:]
                else:
                    count += 1
            filter_string = filter_string.replace("(", "").replace(")", "")
            # I think these are all of the operations we might need to do...
            reg = '(\<=|>=|<|>|==|=)'
            filter_params = re.split(reg, filter_string)
            filter = [filter_params[1],filter_params[0],filter_params[2]]
        return filter

    def split_lines(self, lines):
        s = []
        for line in lines:
            new = line.split()
            # Only take non-empty lines
            if new:
                s.append(new)
        return s

    def get_prefixes(self,file_lines):
        i = 0
        while file_lines[i][0] == 'PREFIX':
            self.prefix_map[file_lines[i][1]] = file_lines[i][2]
            i+=1
        return i

    def determine_output(self, line):
        # Get just the variables or the '*"
        # Not terribly robust but I am not sure we need to be...
        line = line[1:]
        ###
        for i in line:
            if i == '*':
                self.outputFLAG = True
            elif i[0] == '?':
                self.output_variables.append(i)
            else:
                continue

    def replace_and_add(self, query):
        triples = []
        filter_query = []
        threes, count = 0, 0

        for i in query:
            # Get the filter portion
            if i[0] == 'FILTER':
                filter_query = i
            # Don't need to keep around any 'WHERE's or trailing parentheses on new lines
            elif len(i) < 3:
                continue
            # Collect all the triples
            else:
                triples.append(i)
                threes += 1
        # Replace the triple prefixes with urls
        query = []
        for i in triples:
            q = []
            for j in i:
                if j[0] == '?':
                    self.variable_map[j] = []
                    q.append(j)
                    count+=1
                else:
                    q.append(self.sub_prefix(j))
                    count+=1
            query.append(q[:3])

        return query, filter_query

    def sub_prefix(self, name):
        prefix = None
        if (":" in name and name.split(":")[0] + ":" in self.prefix_map):
            prefix = name.split(":")[0] + ":"
        if (prefix):
            name = name.replace(prefix, self.prefix_map[prefix], 1)
        return name


if __name__ == "__main__":
    parser = SparqlQueryParser(sys.argv[1])
    #print(parser.prefix_map)