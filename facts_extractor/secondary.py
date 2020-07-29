from sys import path

path.insert(0, '../')
from common.nlputils import NLPUtils
from common.triple import Triple

class SecondaryFactsExtractor:

    def extract(self, input_filename, output_filename, verbose=False):
        return self.__dep_parse(input_filename, output_filename, verbose)

    def __dep_parse(self, input_filename, output_filename, verbose=False):
        if verbose:
            print('Attempting to extract secondary facts using dependency parsing...')

        out_contents = ''
        with open(input_filename, 'r') as input_file:
            sentence_number = 0
            for line in input_file.readlines():
                if len(line) < 1:
                    continue

                dependency_list = NLPUtils.dependency_parse(line, deps_key='enhancedPlusPlusDependencies', verbose)

                previous_term = ''
                previous_compound = ''
                dict_basic_to_most_specific = {}
                connective_dependencies = []
                while len(dependency_list) > 0:
                    elem = dependency_list.pop()

                    if elem[1] in ['ROOT', 'punct', 'det'] or 'subj' in elem[1] or 'obj' in elem[1]:
                        continue

                    if elem[1] in ['compound', 'nmod:poss', 'aux', 'neg'] or elem[1].endswith('mod'):
                        if previous_term == elem[0]:
                            updated_term = '{} {}'.format(elem[2], previous_compound)
                        else:
                            updated_term = '{} {}'.format(elem[2], elem[0])
                            previous_compound = elem[0]
                        dict_basic_to_most_specific[elem[0]] = updated_term

                        triple = Triple(sentence_number, updated_term, 'rdfs:subClassOf', previous_compound)

                        previous_compound = updated_term
                        previous_term = elem[0]

                        if verbose:
                            print(triple.to_string())

                        out_contents += triple.to_string() + '\n'

                    elif elem[1] in ['acl', 'appos'] or elem[1].startswith('nmod:'):
                        connective_dependencies.append(elem)

                while len(connective_dependencies) > 0:
                    elem = connective_dependencies.pop()

                    if elem[1] == 'nmod:poss':
                        continue

                    if elem[1].find(':') > 0: # e.g. 'nmod:of'
                        connector = elem[1][elem[1].find(':')+1:]
                    elif elem[1] in ['acl', 'appos']:
                        connector = ''
                    else:
                        connector = elem[1]

                    first = elem[0]
                    if first in dict_basic_to_most_specific.keys():
                        first = dict_basic_to_most_specific[first]

                    second = elem[2]
                    if second in dict_basic_to_most_specific.keys():
                        second = dict_basic_to_most_specific[second]

                    if connector == '':
                        full = '{} {}'.format(first, second)
                    else:
                        full = '{} {} {}'.format(first, connector, second)
                    
                    triple = Triple(sentence_number, full, 'local:{}_{}'.format(connector, second.replace(' ', '')), first)
                    if verbose:
                        print(triple.to_string())
                    out_contents += triple.to_string() + '\n'

                    triple = Triple(sentence_number, full, 'local:{}_{}'.format(first.replace(' ', ''), connector), second)
                    if verbose:
                        print(triple.to_string())
                    out_contents += triple.to_string() + '\n'

                    dict_basic_to_most_specific[elem[0]] = full

                sentence_number += 1

            input_file.close()

        with open(output_filename, 'a') as output_file:
            output_file.write(out_contents)
            output_file.close()

        return output_filename
