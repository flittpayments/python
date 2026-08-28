import os
import json

from unittest import TestCase
from flittpayments import Api, Pcidss, helpers


class TestCase(TestCase):
    def get_api(self):
        self.data = self.get_dummy_data()
        return Api(merchant_id=self.data['merchant']['id'],
                   secret_key=self.data['merchant']['secret'])

    def get_dummy_data(self):
        dummy_data = os.path.join(os.path.dirname(__file__),
                                  'data',
                                  'test_data.json')
        with open(dummy_data) as f:
            self.data = json.load(f)
        return self.data

    def create_order(self):
        pcidss = Pcidss(api=self.get_api())
        params = {
            "preauth": "Y",
            "required_rectoken": "Y"
        }
        params.update(self.data['payment_pcidss_non3ds'])
        return pcidss.step_one(params)

    def test_validate_order(self):
        payment = self.create_order()
        is_valid = helpers.is_valid(data=payment,
                                    secret_key=self.data['merchant']['secret'],
                                    protocol='1.0')
        self.assertEqual(payment.get('response_status'), 'success')
        self.assertEqual(is_valid, True)

    def test_is_approved(self):
        payment = self.create_order()
        self.assertEqual(payment.get('order_status'), 'approved')
        is_approved = helpers.is_approved(data=payment,
                                          secret_key=self.data['merchant']['secret'],
                                          protocol='1.0')
        self.assertEqual(is_approved, True)

    def test_is_approved_missing_order_status(self):
        # secret_key/protocol are irrelevant here - is_approved must raise
        # before ever looking at the signature, so this needs no self.data.
        with self.assertRaises(ValueError):
            helpers.is_approved(data={'signature': 'x'},
                                secret_key='test',
                                protocol='1.0')
