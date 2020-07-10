# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path('__file__').resolve().parent))
# --------------------------------------------------------------------------------------
import os
import re
from janome.tokenizer import Tokenizer
from kanjize import int2kanji
import jaconv
import pyboin
from engine import engine
# --------------------------------------------------------------------------------------


class JudgeEngine(engine.Engine):
    def __init__(self):
        self.tokenize = Tokenizer()
        self.force_pass_pattern = open('config/force_judge_pattern.txt').read().split('\n')
        self.force_pass_pattern.remove('')

    def is_dajare(self, dajare, use_api=True):
        # force pass as dajare
        for pattern in self.force_pass_pattern:
            if re.match(pattern, dajare) is not None:
                return True

        # not pass symmetry(xxx|xxx) pattern
        # ex. テストテスト -> not dajare
        pivot = len(dajare) // 2
        if dajare[:pivot] == dajare[pivot:]:
            return False

        # convert dajare to reading & morphes
        reading, morphes = self.to_reading_and_morphes(dajare, use_api)

        # pre judge
        tri_gram = self.n_gram(reading, 3)
        if len(set(tri_gram)) != len(tri_gram):
            return True

        # preprocessing
        reading, morphes = self.preprocessing(reading, morphes)

        # exclude 'ッ'
        reading_excluded_tu = reading.replace('ッ', '')
        morphes_excluded_tu = [m.replace('ッ', '') for m in morphes]

        if self.judge(reading, morphes):
            return True
        if self.judge(reading_excluded_tu, morphes_excluded_tu):
            return True

        return False

    def judge(self, reading, morphes):
        # whether morphe is included multiple
        for m in morphes:
            if reading.count(m) >= 2:
                return True

        # whether judgment rules holds
        tri_char = self.n_gram(reading, 3)

        for i, tri1 in enumerate(tri_char):
            for tri2 in tri_char[(i+1):]:
                # all match
                if tri1 == tri2:
                    return True

                # 2 chars match && all vowels match
                if self.count_str_match(tri1, tri2) == 2:
                    if pyboin.text2boin(tri1) == pyboin.text2boin(tri2):
                        return True

        if 'ー' in reading:
            # exclude 'ー'
            if self.judge(reading.replace('ー', ''), []):
                return True

            # convert 'ー' to last vowel
            # ex. 'カー' -> 'カア'
            hyphen_to_vowel_reading = ''
            patterns = re.findall(r'.ー', reading)
            for ch in patterns:
                hyphen_to_vowel_reading = reading.replace(
                    ch,
                    ch[0] + pyboin.text2boin(ch[0])
                )
            if self.judge(hyphen_to_vowel_reading, []):
                return True

        # convert char to next lower's vowel
        # ex. 'シュン' -> 'ウン'
        matches = re.findall(r'.[ァィゥェォャュョヮ]', reading)
        if matches != []:
            lower_to_vowel_reading = reading
            for ch in matches:
                lower_to_vowel_reading = lower_to_vowel_reading.replace(
                    ch,
                    pyboin.text2boin(ch[1])
                )
            if self.judge(lower_to_vowel_reading, []):
                return True

        return False

    def to_reading_and_morphes(self, dajare, use_api=True):
        reading = ''

        # use docomo api
        if use_api:
            reading = self.to_reading(dajare)

        # not use api || cannot use api
        if reading == '':
            for ch in re.findall('\d+', dajare):
                dajare = dajare.replace(ch, int2kanji(int(ch)))

            # morphological analysis
            for token in self.tokenize.tokenize(dajare):
                reading = token.reading

                if reading == '*':
                    # token with unknown word's reading
                    reading += jaconv.hira2kata(token.surface)
                else:
                    # token with known word's reading
                    reading += reading

        # extract morphes (len >= 2)
        morphes = []
        for token in self.tokenize.tokenize(dajare):
            if len(token.reading) >= 2:
                morphes.append(token.reading)

        # force convert reading
        reading = jaconv.hira2kata(reading)

        # exclude noises
        reading = ''.join(re.findall('[ァ-ヴー]+', reading))

        return reading, morphes

    def preprocessing(self, reading, morphes):
        # nomalize text
        nomalize_pair = [
            'ヂガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ',
            'ジカキクケコサシスセソタチツテトハヒフヘホハヒフヘホ'
        ]
        for i in range(len(nomalize_pair[0])):
            reading = reading.replace(
                nomalize_pair[0][i],
                nomalize_pair[1][i],
            )
            morphes = [m.replace(
                nomalize_pair[0][i],
                nomalize_pair[1][i]) for m in morphes]

        # convert looped vowel text to '-'
        for ci in range(len(reading) - 1):
            if reading[ci+1] not in 'アイウエオ':
                continue

            if pyboin.text2boin(reading[ci]) == \
                    pyboin.text2boin(reading[ci+1]):
                reading = reading[:ci+1] + 'ー' + reading[ci+2:]

        # convert vowel text to pronunciation
        vowel_pattern = [
            ['オウ', 'オー'],
            ['エイ', 'エー'],
        ]
        for bi_char in self.n_gram(reading, 2):
            for sub in vowel_pattern:
                if pyboin.text2boin(bi_char) == sub[0]:
                    reading = reading.replace(bi_char, sub[1])

        return reading, morphes

    def n_gram(self, dajare, n):
        return [dajare[idx:idx + n] for idx in range(len(dajare) - n + 1)]

    def count_str_match(self, s1, s2):
        count = 0
        for i in range(len(s1)):
            if s1[i] == s2[i%len(s2)]:
                count += 1

        return count

