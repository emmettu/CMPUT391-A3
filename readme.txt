Emmett Underhill
John Maxwell Douglas

Running question 8:

python q8.py <turtle file> <db file name>


Running question 9:

python q9.py <db file> <query file>

When the query is returned, the prefixes are substituted out
becuase the parser does not resubstitute prefixes in the query
results.

Results are separated by "|", the first line is the name of the
variables for each column being printed.

Edmonton.txt was the main test graph used.

Assumptions made during query parsing:

A numeric filter is in the form "FILTER (variable operation number)"
ie: FILTER (?population > 200)

