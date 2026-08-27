from __future__ import absolute_import, unicode_literals
from flittpayments import utils
from .tests_helper import TestCase


class UtilTest(TestCase):
    def setUp(self):
        self.data = self.get_dummy_data()

    def test_to_form(self):
        form = utils.to_form(self.data['checkout_data'])
        self.assertEqual(form, 'amount=100&currency=GEL')

    def test_from_from(self):
        form = utils.to_form(self.data['checkout_data'])
        json = utils.from_form(form)
        self.assertEqual(json, self.data['checkout_data'])

    def test_join_url(self):
        joined_url = utils.join_url("checkout", "order")
        self.assertEqual(joined_url, "checkout/order")
        joined_url = utils.join_url("order", "/3ds")
        self.assertEqual(joined_url, "order/3ds")
