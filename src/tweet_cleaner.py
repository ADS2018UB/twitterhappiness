import re
from nltk.tokenize import WordPunctTokenizer
from bs4 import BeautifulSoup


class TweetCleaner:
    def __init__(self):
        self.tok = WordPunctTokenizer()
        pat1 = r'@[A-Za-z0-9_]+'
        pat2 = r'https?://[^ ]+'
        self.combined_pat = r'|'.join((pat1, pat2))
        self.www_pat = r'www.[^ ]+'
        self.negations_dic = {"isn't": "is not", "aren't": "are not", "wasn't": "was not", "weren't": "were not",
                              "haven't": "have not", "hasn't": "has not", "hadn't": "had not", "won't": "will not",
                              "wouldn't": "would not", "don't": "do not", "doesn't": "does not", "didn't": "did not",
                              "can't": "can not", "couldn't": "could not", "shouldn't": "should not", "mightn't": "might not",
                              "mustn't": "must not"}
        self.neg_pattern = re.compile(
            r'\b(' + '|'.join(self.negations_dic.keys()) + r')\b')

    def clean(self, text):
        soup = BeautifulSoup(text, 'lxml')
        souped = soup.get_text()
        try:
            bom_removed = souped.decode("utf-8-sig").replace(u"\ufffd", "?")
        except:
            bom_removed = souped
        stripped = re.sub(self.combined_pat, '', bom_removed)
        stripped = re.sub(self.www_pat, '', stripped)
        lower_case = stripped.lower()
        neg_handled = self.neg_pattern.sub(
            lambda x: self.negations_dic[x.group()], lower_case)
        letters_only = re.sub("[^a-zA-Z]", " ", neg_handled)
        words = [x for x in self.tok.tokenize(letters_only) if len(x) > 1]
        return (" ".join(words)).strip()
