# vim: set ts=8 sw=4 sts=4 et ai tw=79:
"""
Test ini storage class to the Exact Online REST API Library.

This file is part of the Exact Online REST API Library in Python
(EORALP), licensed under the LGPLv3+.
Copyright (C) 2015-2021 Walter Doekes, OSSO B.V.
"""
from unittest import TestCase, main
from io import StringIO
from os import path, unlink

from . import MissingSetting
from .ini import IniStorage


class IniStorageTestCase(TestCase):
    def test_dont_die_if_config_doesnt_exist(self):
        try:
            config = IniStorage('storage-does-not-exist.ini')
            del config
            self.assertFalse(path.exists('storage-does-not-exist.ini'))
        finally:
            try:
                unlink('storage-does-not-exist.ini')
            except OSError:
                pass

    def test_missing_section_raises_nooption(self):
        config = IniStorage(StringIO())
        self.assertRaises(MissingSetting, config.get, 'bad_section',
                          'bad_value')

    def test_server_defaults(self):
        config = IniStorage(StringIO())
        self.assertEqual(config.get_auth_url(),
                         'https://start.exactonline.nl/api/oauth2/auth')
        self.assertEqual(config.get_rest_url(),
                         'https://start.exactonline.nl/api')
        self.assertEqual(config.get_token_url(),
                         'https://start.exactonline.nl/api/oauth2/token')

    def test_server_default_writes(self):
        try:
            self.assertFalse(path.exists('storage-gets-created.ini'))
            config = IniStorage('storage-gets-created.ini')
            auth_url = 'https://start.exactonline.nl/api/oauth2/auth'
            self.assertEqual(config.get_auth_url(), auth_url)
            with open('storage-gets-created.ini', 'r') as written:
                for line in written:
                    if auth_url in line:
                        break
                else:
                    self.assertFalse('URL %r not found in file' % (auth_url,))
        finally:
            try:
                unlink('storage-gets-created.ini')
            except OSError:
                pass

    def test_application_no_defaults(self):
        config = IniStorage(StringIO())
        self.assertRaises(MissingSetting, config.get_base_url)
        self.assertRaises(MissingSetting, config.get_response_url)  # same..
        self.assertRaises(MissingSetting, config.get_client_id)
        self.assertRaises(MissingSetting, config.get_client_secret)

    def test_transient_no_defaults(self):
        config = IniStorage(StringIO())
        # We do use a default of 0 for config.get_access_expiry.
        # #self.assertRaises(MissingSetting, config.get_access_expiry)
        self.assertRaises(MissingSetting, config.get_access_token)
        self.assertRaises(MissingSetting, config.get_code)
        self.assertRaises(MissingSetting, config.get_division)
        self.assertRaises(MissingSetting, config.get_refresh_token)

    def test_example_ini(self):
        config = IniStorage(
            path.join(path.dirname(__file__), 'ini_example.ini'))

        # [server]
        self.assertEqual(config.get_auth_url(),
                         'https://start.exactonline.co.uk/api/oauth2/auth')
        self.assertEqual(config.get_rest_url(),
                         'https://start.exactonline.co.uk/api')
        self.assertEqual(config.get_token_url(),
                         'https://start.exactonline.co.uk/api/oauth2/token')
        self.assertEqual(config.get_token_url(), config.get_refresh_url())

        # [application]
        self.assertEqual(config.get_base_url(), 'https://example.com')
        self.assertEqual(config.get_response_url(), 'https://example.com')
        self.assertEqual(config.get_client_id(),
                         '{12345678-abcd-1234-abcd-0123456789ab}')
        self.assertEqual(config.get_client_secret(), 'ZZZ999xxx000')

        # [transient]
        self.assertEqual(config.get_access_expiry(), 1426492503)
        self.assertEqual(
            config.get_access_token(),
            'dAfjGhB1k2tE2dkG12sd1Ff1A1fj2fH2Y1j1fKJl2f1sD1ON275zJNUy...')
        self.assertEqual(
            config.get_code(),
            'dAfj!hB1k2tE2dkG12sd1Ff1A1fj2fH2Y1j1fKJl2f1sD1ON275zJNUy...')
        self.assertEqual(config.get_division(), 123456)
        self.assertEqual(
            config.get_refresh_token(),
            'SDFu!12SAah-un-56su-1fj2fH2Y1j1fKJl2f1sDfKJl2f1sD11FfUn1...')

    def test_transient_writes(self):
        try:
            self.assertFalse(path.exists('storage-gets-created.ini'))
            config = IniStorage('storage-gets-created.ini')
            self.assertRaises(MissingSetting, config.get_division)
            config.set_division(987654321)
            self.assertEqual(config.get_division(), 987654321)
            config.set_division(11223344)

            # Re-open config, and check availability.
            config2 = IniStorage('storage-gets-created.ini')
            self.assertEqual(config2.get_division(), 11223344)
        finally:
            try:
                unlink('storage-gets-created.ini')
            except OSError:
                pass

    def test_get_and_set_must_be_string_types(self):
        # internals: we want str types inserted into set() and returned
        # from get(). Needed for clean py23 compatibility.
        try:
            self.assertFalse(path.exists('storage-gets-created.ini'))
            config = IniStorage('storage-gets-created.ini')

            # Test even when writing the inverse of a str, we still get a
            # native-str type back. For py23 compatibility.
            byte_string = 'abc'.encode('ascii')
            if hasattr(byte_string, 'encode'):
                non_native_string = byte_string.decode('ascii')
            else:
                non_native_string = byte_string

            # Store temp value.
            config.set_access_token(non_native_string)
            value = config.get_access_token()
            self.assertEqual(value, 'abc')
            self.assertEqual(type(value), str)

            # Reload file and check value some more.
            config = IniStorage('storage-gets-created.ini')
            value = config.get_access_token()
            self.assertEqual(value, 'abc')
            self.assertEqual(type(value), str)
        finally:
            try:
                unlink('storage-gets-created.ini')
            except OSError:
                pass

    def test_that_you_cannot_use_multiple_storages(self):
        "You can use multiple IniStorage()s, but not at the same time"
        try:
            self.assertFalse(path.exists('storage-gets-created.ini'))
            config = IniStorage('storage-gets-created.ini')
            config_opened_too_soon = IniStorage('storage-gets-created.ini')
            config.set_refresh_token('some-token')
            config_opened_after_write = IniStorage('storage-gets-created.ini')

            # Our storage has the right data (obviously).
            self.assertEqual(
                config.get_refresh_token(), 'some-token')
            # A new storage opened after updating the source file has
            # the right data.
            self.assertEqual(
                config_opened_after_write.get_refresh_token(), 'some-token')
            # A second storage opened before updating a different one,
            # does not get any updates. The INI file is read during
            # construction, after all.
            with self.assertRaises(MissingSetting):
                config_opened_too_soon.get_refresh_token()
        finally:
            try:
                unlink('storage-gets-created.ini')
            except OSError:
                pass


if __name__ == '__main__':
    main()
