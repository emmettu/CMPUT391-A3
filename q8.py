import sys
import re
import sqlite3


class RdfParser():

    def __init__(self, file_name):
        self.triplets = []
        self.prefix_map = {}
        self.raw = self.read_rdf(file_name)
        self.tokens = self.tokenize(self.raw)
        self.token_number = -1
        self.get_triples()

    def read_rdf(self, file_name):
        with open(file_name, "r") as f:
            return f.read()

    def tokenize(self, raw_rdf):
        raw_rdf = re.sub("\s#.*$", "", raw_rdf)
        raw_rdf = re.sub("\s+", " ", raw_rdf)
        return raw_rdf.split(" ")

    def get_triples(self):
        while self.token_number < len(self.tokens) - 1:
            token = self.consume_token()
            #print(token)
            if (token == "@prefix"):
                self.prefix()
            else:
                self.dbr(token)

    def prefix(self):
        prefix_name = self.consume_token()
        prefix_value = self.consume_token().replace("<", "").replace(">", "")
        self.consume_token()
        self.prefix_map[prefix_name] = prefix_value

    def dbr(self, subject):
        if subject == "":
            return
        subject = self.sub_prefix(subject)
        token = subject
        while True:
            if token == ".":
                break
            predicate = self.get_predicate()
            self.triplets.extend(self.make_triples(subject, predicate))
            token = self.peek_token()
        self.consume_token()

    def get_predicate(self):
        doubles = []
        predicate = self.get_next(self.consume_token())
        predicate = self.sub_prefix(predicate)
        objects = self.get_objects(self.consume_token())
        for o in objects:
            doubles.append((predicate, o))
        return doubles

    def get_objects(self, token):
        token = self.sub_prefix(token)
        token = self.get_next(token)
        objects = [token]
        next_token = token
        while (next_token != ";"):
            if (self.peek_token() == "."):
                break
            next_token = self.consume_token()
            if (next_token == ""):
                continue
            if (next_token == ","):
                next_token = self.sub_prefix(self.consume_token())
                objects.append(self.get_next(next_token))
        return objects

    def make_triples(self, subject, predicate_list):
        triples = []
        for p, o in predicate_list:
            triples.append((subject, p, o))
        return triples

    def sub_prefix(self, name):
        prefix = None
        if (":" in name and name.split(":")[0] + ":" in self.prefix_map):
            prefix = name.split(":")[0] + ":"
        if (prefix):
            name = name.replace(prefix, self.prefix_map[prefix], 1)
        return name

    def get_next(self, token):
        if token.startswith("\""):
            return self.rebuild_string(token)
        return token

    def rebuild_string(self, token):
        string_list = [token]
        while(not self.string_end(string_list[-1])):
            string_list.append(self.consume_token())
        return " ".join(string_list)

    def string_end(self, string):
        if "@" in string:
            string = string.split("@")[0]
        if "^^" in string:
            string = string.split("^^")[0]
        if string[-1] == "\"":
            return True
        return False

    def consume_token(self):
        self.token_number += 1
        token = self.tokens[self.token_number]
        return token

    def peek_token(self):
        token = self.tokens[self.token_number + 1]
        return token

if __name__ == "__main__":
    parser = RdfParser(sys.argv[1])
    #print(parser.triplets)
    conn = sqlite3.connect(sys.argv[2])
    cur = conn.cursor()
    conn.text_factory = str
    cur.execute(
        '''CREATE TABLE triples
          (subject text, predicate text, object text)''')

    cur.executemany(
        'INSERT into triples \
        (subject, predicate, object) \
        values (?, ?, ?)', parser.triplets)
    conn.commit()
    conn.close()
