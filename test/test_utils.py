# -*- encoding: utf-8 -*-
# pylint: skip-file
from __future__ import absolute_import

import unittest
import esipy.utils as utils


class TestUtils(unittest.TestCase):

    def test_code_verifier(self):
        with self.assertRaises(ValueError):
            utils.generate_code_verifier(30)

        with self.assertRaises(ValueError):
            utils.generate_code_verifier(98)

        code_verifier = utils.generate_code_verifier()
        self.assertGreater(len(code_verifier), 0)

    def test_code_challenge(self):
        # example from RFC 7636
        CODE_VERIFIER = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        EXP_CODE_CHALLENGE = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"

        code_challenge = utils.generate_code_challenge(CODE_VERIFIER)
        self.assertEqual(code_challenge, EXP_CODE_CHALLENGE)
