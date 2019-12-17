import os

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.tree import Tree

from .stanfordcorenlp.corenlpwrapper import CoreNLPWrapper

class NLPUtils:

    PUNCTUATION = ['.', ',', ':', ';']

    @staticmethod
    def adjust_tokens(contents, remove_punctuation=False):
        # This seems like a major overhead, maybe there is a better way...
        nlp = CoreNLPWrapper()
        annotated = nlp.annotate(contents,  properties={'annotators': 'tokenize, ssplit, pos'})

        resolved = ''
        for sentence in annotated['sentences']:
            for token in sentence['tokens']:
                if remove_punctuation and (token['pos'] in NLPUtils.PUNCTUATION or (token['index'] == 1 and token['pos'] == 'DT')):
                    continue

                if token['pos'] in NLPUtils.PUNCTUATION or token['pos'] == 'POS':
                    resolved = resolved.strip()

                resolved += token['word'] + ' '

            resolved = resolved.strip()
            resolved += '\n'

        return resolved.strip()

    @staticmethod
    def remove_stopwords(sentence):
        stop_words = set(stopwords.words('english'))
        word_tokens = word_tokenize(sentence)

        filtered_sentence = [w for w in word_tokens if not w.lower() in stop_words]

        return ' '.join(filtered_sentence)

    @staticmethod
    def dependency_parse(contents, verbose=False):
        nlp = CoreNLPWrapper()
        annotated = nlp.annotate(contents, properties={'annotators': 'tokenize, ssplit, pos, lemma, ner, depparse'})

        dependencies = list()
        for sentence in annotated['sentences']:
            for dependency in sentence['basicDependencies']:
                dep_tuple = (dependency['governorGloss'], dependency['dep'], dependency['dependentGloss'])
                if verbose:
                    print('{} --{}--> {}'.format(dep_tuple[0], dep_tuple[1], dep_tuple[2]))

                dependencies.append(dep_tuple)

        return dependencies

    @staticmethod
    def extract_np_and_verbs(contents):
        print('Determining the noun-phrases (possible entities) and verbs (possible predicates). \n Please wait, as it may take a while ...')
        nlp = CoreNLPWrapper()
        annotated = nlp.annotate(contents, properties={'annotators': 'tokenize, ssplit, pos, lemma, ner, parse'})

        verb_set = set()
        entity_set = set()
        for sentence in annotated['sentences']:
            for token in sentence['tokens']:
                if token['pos'].startswith('VB'):
                    verb_set.add(token['word'])

            parsed_sentence = sentence['parse'].replace('\n', '')
            parse_tree = Tree.fromstring(parsed_sentence)
            for sub_tree in parse_tree.subtrees():
                if sub_tree.label() == 'NP':
                    np_entity = NLPUtils.adjust_tokens(' '.join(sub_tree.leaves()), remove_punctuation=True)
                    if np_entity: # not empty
                        if np_entity.endswith('.'):
                            np_entity = np_entity.replace('.', '') # needed due to a tokenizer bug
                        entity_set.add(np_entity)

        return entity_set, verb_set

    @staticmethod
    def generate_tsv_file(self, contents, linked, input_filename):
        nlp = CoreNLPWrapper()
        annotated = nlp.annotate(contents, properties={'annotators': 'tokenize, ssplit, pos, lemma, ner'})

        tsv_filename = os.path.splitext(input_filename)[0] + '_ner.tsv'
        open(tsv_filename, 'w').close() # Clean the file in case it exists

        with open(tsv_filename, 'a') as tsv_file:
            for sentence in annotated['sentences']:
                for token in sentence['tokens']:
                   tk = token['ner']
                   if tk == 'O' and token['word'].upper() in linked:
                       tk = 'MISC'
                   tsv_file.write(token['word'] + '\t' + tk + '\n')
        tsv_file.close()
        print('TSV file has been stored at {}'.format(tsv_filename))

        return tsv_filename

