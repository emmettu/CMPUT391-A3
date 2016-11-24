import sys
import re


class RdfParser():

    def __init__(self, file_name):
        self.triplets = []
        self.prefix_list = []
        self.raw = self.read_rdf(file_name)
        self.tokens = self.tokenize(self.raw)

    def read_rdf(self, file_name):
        with open(file_name, "r") as f:
            return f.read()

    def tokenize(self, raw_rdf):
        raw_rdf = re.sub("\s+", " ", raw_rdf)
        return raw_rdf.split(" ")

    def get_triples(self):
        pass


if __name__ == "__main__":
    parser = RdfParser(sys.argv[1])
    print(parser.tokens)
