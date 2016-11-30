'''
Question 9: Assignment #3

I have been using test.txt, q1.txt, and q2.txt to test.txt.

test.txt has a '>' sign in it because I wanted to make sure I was grabbing it properly.
Its not actually a runnable query.
'''

import sys
import sqlite3


class SparqlQueryParser():

    def __init__(self, file_name):
        with open(file_name, "r") as f:
            raw_query = f.read()
        self.parse(raw_query)

    def parse(self, query_text):
        query_text = query_text.strip()
        self.print_all = False
        self.variable_map = {}
        self.triples = []
        self.columns = ["subject", "predicate", "object"]
        self.filter_struct = None

        lines = query_text.split("\n")
        lines = [i.strip() for i in lines]
        lines = [i for i in lines if i != ""]
        prefixes, rest = self.divide_at_prefixes(lines)

        self.get_prefixes(prefixes)
        self.parse_rest(rest[:-1])

    def divide_at_prefixes(self, lines):
        prefix_index = 0
        for index, line in enumerate(lines):
            if not line.strip().startswith("PREFIX"):
                prefix_index = index
                break
        return lines[:prefix_index], lines[prefix_index:]

    def get_prefixes(self, prefixes):
        self.prefix_map = {}
        for prefix in prefixes:
            self.eval_prefix(prefix)

    def eval_prefix(self, prefix):
        prefix = prefix.split(" ")
        prefix = [i.strip() for i in prefix]
        key = prefix[1][:-1]
        value = prefix[2]
        self.prefix_map[key] = value.replace("<", "").replace(">", "")

    def parse_rest(self, rest):
        variables, rest = rest[0], rest[1:]
        self.parse_vars(variables)
        for line in rest:
            self.parse_filter_or_triple(line.strip())

    def parse_vars(self, variables):
        variables = variables.replace("SELECT", "")
        variables = variables.replace("WHERE", "")
        variables = variables.replace("{", "")
        variables = variables.strip()

        if "*" in variables:
            self.print_all = True
            return

        variables = variables.split(" ")
        self.output_vars = [i.strip() for i in variables]

    def parse_filter_or_triple(self, line):
        if line.startswith("FILTER") and "(" in line:
            self.parse_filter(line)
        else:
            self.parse_triple(line)

    def parse_filter(self, line):
        line = line.replace("FILTER", "").strip()
        line = line.strip("(").strip(")")
        if line.startswith("regex"):
            self.parse_regex(line)
        else:
            self.parse_numeric(line)

    def parse_regex(self, line):
        line = line.replace("regex(", "")
        var, query = line.split(",")
        self.filter_struct = (str.__contains__, var.strip(), query.strip().strip("\""))

    def parse_numeric(self, line):
        func_map = {
            ">": lambda x, y: self.to_num(x) > y,
            "<": lambda x, y: self.to_num(x) > y,
            ">=": lambda x, y: self.to_num(x) > y,
            "<=": lambda x, y: self.to_num(x) > y,
            "!=": lambda x, y: self.to_num(x) > y,
            "==": lambda x, y: self.to_num(x) > y
        }
        line = line.strip()
        items = [i.strip() for i in line.split(" ")]

        var = items[0]
        op = items[1]
        pred = self.to_num(items[2])

        self.filter_struct = (func_map[op], var, pred)

    def to_num(self, string):
        try:
            return int(string)
        except:
            return float(string)

    def parse_triple(self, line):
        triples = line.split(" ")
        triples = [i.strip() for i in triples]
        triples = [i.strip("\"") for i in triples]
        sub, pred, obj = [self.sub_prefix(i) for i in triples[0:3]]
        self.triples.append([sub, pred, obj])

    def sub_prefix(self, item):
        if ":" in item and item.split(":")[0] in self.prefix_map:
            key, val = item.split(":")
            return self.prefix_map[key] + val
        return item

    def execute(self, db):
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        for triple in self.triples:
            self.run_triple(triple, cur)
        conn.close()
        self.print_result()

    def run_triple(self, triple, cur):
        sub = triple[0]
        pred = triple[1]
        obj = triple[2]

        subs = self.get_vars(sub)
        preds = self.get_vars(pred)
        objs = self.get_vars(obj)

        all_items = filter(lambda x: x != "", subs + preds + objs)
        only_vars = filter(self.is_var, [sub, pred, obj])

        select = self.make_select(sub, pred, obj)
        where = self.make_where(subs, preds, objs)
        query_result = cur.execute(select + " " + where, all_items)
        self.fill_variables(only_vars, query_result)

    def get_vars(self, string):
        if self.is_new_var(string):
            return []
        elif self.is_var(string):
            return self.variable_map[string]
        return [string]

    def make_select(self, sub, pred, obj):
        columns = [self.columns[i] for i in range(3) if self.is_var([sub, pred, obj][i])]

        return "SELECT " + ", ".join(columns) + " FROM triples"

    def make_where(self, sub, pred, obj):
        subs = self.or_conditions("subject", sub)
        preds = self.or_conditions("predicate", pred)
        objs = self.or_conditions("object", obj)
        nop_condition = "1 = 1"
        return "WHERE " + " AND ".join(filter(lambda x: x != "()", [subs, preds, objs, nop_condition]))

    def or_conditions(self, type_str, lst):
        return "(" + " OR ".join([type_str + " = ? " for i in lst if i != ""]) + ")"

    def is_var(self, string):
        return string.startswith("?")

    def is_new_var(self, string):
        return self.is_var(string) and string not in self.variable_map

    def fill_variables(self, var_list, query_result):
        for var in var_list:
            self.variable_map[var] = []

        for row in query_result:
            for index, var in enumerate(var_list):
                self.variable_map[var].append(row[index])

    def apply_filter(self):
        func, variable, pred = self.filter_struct
        var_list = self.variable_map[variable]
        self.variable_map[variable] = filter(lambda x: func(x.encode("ascii", "ignore"), pred), var_list)

    def print_result(self):
        output_list = self.variable_map.keys() if self.print_all else self.output_vars
        length = len(self.variable_map[output_list[0]])
        out = []
        for i in output_list:
            out.append(i)
        print "|".join(out)

        for i in range(length):
            out = []
            for x, variable in enumerate(output_list):
                variable_list = self.variable_map[variable]
                if len(variable_list) < i + 1:
                    return
                if self.skip(variable, variable_list[i]):
                    break
                out.append(variable_list[i])
            print "|".join(out)
        print


    def skip(self, var, item):
        if not self.filter_struct:
            return False
        if var != self.filter_struct[1]:
            return False
        func, variable, pred = self.filter_struct
        return not func(item.encode("ascii", "ignore"), pred)

if __name__ == "__main__":
    parser = SparqlQueryParser(sys.argv[2])
    parser.execute(sys.argv[1])
    #print(parser.prefix_map)
