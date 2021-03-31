import unittest
import engine


class TestAPI(unittest.TestCase):
    def test_katakanize(self):
        text = 'こんにちは'
        self.assertEqual('コンニチハ', engine.text_service.katakanize(text, False))

    def test_morphs(self):
        text = 'こんにちは世界'
        self.assertEqual(['コンニチハ', 'セカイ'], engine.text_service.morphs(text))

    def test_cleaned(self):
        text = '!@#$%^^&*()，。/-_=+;:こんにちはwww'
        self.assertEqual('こんにちは', engine.text_service.cleaned(text))

    def test_count_char_matches(self):
        self.assertEqual(
            0, engine.text_service.count_char_matches('ABC', 'BCA'))
        self.assertEqual(
            1, engine.text_service.count_char_matches('ABC', 'ACB'))
        self.assertEqual(
            2, engine.text_service.count_char_matches('ABC', 'ABB'))
        self.assertEqual(
            3, engine.text_service.count_char_matches('ABC', 'ABC'))

    def test_n_gram(self):
        self.assertEqual(['こんに', 'んにち', 'にちは'],
                         engine.text_service.n_gram('こんにちは', 3))

    def test_nomalize(self):
        self.assertEqual('カキクケコ', engine.text_service.normalize('ガギグゲゴ'))
        self.assertEqual('アイイ', engine.text_service.normalize('アアアイイ'))

    def test_convert_vector(self):
        self.assertEqual([12371, 12435, 12395, 12385, 12399],
                         engine.text_service.conv_vector('こんにちは'))

    @unittest.skipIf(not engine.text_service.token_valid, 'TESTSKIP')
    def test_katakanize_withapi(self):
        texts = [
            ['コンニチハ', 'こんにちは'],
            ['チョオマエ', 'ちょwお前www'],
            ['エービーシーディー', 'ABCD'],
            ['', 'abcd'],
        ]
        for text in texts:
            self.assertEqual(
                text[0],
                engine.text_service.katakanize(text[1])
            )

    @unittest.skipIf(not engine.text_service.token_valid, 'TESTSKIP')
    def test_sensitive_check_withapi(self):
        text = '殺人，麻薬'
        self.assertEqual(
            ['傷害', '恐喝', '殺人', '脅迫', '薬物', '覚せい剤', '麻薬'],
            engine.text_service.sensitive_check(text))
