#!/usr/bin/env python3
import os
import unittest
from unittest import mock
# import tempfile
from flask import url_for, request, json, jsonify

import glassfrog
from glassfrog.functions import apiCalls
from glassfrog.functions.messageFunctions import createMessageDict
from glassfrog import strings

import test_values


class GlassfrogTestCase(unittest.TestCase):

    def setUp(self):
        # self.db_fd, glassfrog.app.config['DATABASE'] = tempfile.mkstemp()
        glassfrog.app.config['TESTING'] = True
        self.app = glassfrog.app.test_client()
        # with glassfrog.app.app_context():
        #     glassfrog.init_db()

    def tearDown(self):
        # os.close(self.db_fd)
        # os.unlink(glassfrog.app.config['DATABASE'])
        pass

    def test_home(self):
        rv = self.app.get('/', follow_redirects=True)
        assert b'Install Glassfrog HipChat Integration' in rv.data

    def test_capabilities(self):
        mock_myserver = 'http://localhost:45277'
        mock_capabilitiesDict = apiCalls.getCapabilitiesDict(mock_myserver)

        glassfrog.myserver = mock_myserver
        rv = self.app.get('/capabilities.json', follow_redirects=True)
        return_capabilitiesDict = json.loads(rv.get_data())
        assert return_capabilitiesDict == mock_capabilitiesDict

    @mock.patch('glassfrog.apiCalls.HipchatApiHandler')
    def test_installed(self, mock_HipchatApiHandler):
        mock_HipchatApiHandler.return_value.getCapabilitiesData.return_value = test_values.mock_capabilitiesData
        mock_HipchatApiHandler.return_value.getTokenData.return_value = test_values.mock_tokenData
        mock_jsoninstalldata = json.dumps(test_values.mock_installdata)

        rv = self.app.post('/installed', follow_redirects=True, data=mock_jsoninstalldata)

        mock_hipchatApiSettings = apiCalls.HipchatApiSettings(
                                    hipchatToken=test_values.mock_tokenData['access_token'],
                                    hipchatApiUrl=test_values.mock_capabilitiesData['capabilities']['hipchatApiProvider']['url'],
                                    hipchatRoomId=test_values.mock_installdata['roomId'])
        mock_HipchatApiHandler.return_value.sendMessage.assert_called_with(
            color=strings.succes_color,
            message=strings.installed_successfully,
            hipchatApiSettings=mock_hipchatApiSettings)

    @mock.patch('glassfrog.apiCalls.requests')
    def test_sendMessage(self, mock_requests):
        mock_hipchatToken = 'TtqnpP9GREMNHIOSIYaXqM64hZ3YfQjEelxpLDeT'
        mock_hipchatApiUrl = 'https://api.hipchat.com/v2/'
        mock_hipchatRoomId = 2589171
        mock_color = strings.succes_color
        mock_message = 'Test!'

        hipchatApiHandler = apiCalls.HipchatApiHandler()
        mock_hipchatApiSettings = apiCalls.HipchatApiSettings(
                                    hipchatToken=mock_hipchatToken,
                                    hipchatApiUrl=mock_hipchatApiUrl,
                                    hipchatRoomId=mock_hipchatRoomId)
        hipchatApiHandler.sendMessage(
            color=mock_color,
            message=mock_message,
            hipchatApiSettings=mock_hipchatApiSettings)
        mock_messageUrl = '{}/room/{}/notification'.format(mock_hipchatApiUrl, mock_hipchatRoomId)
        mock_token_header = {"Authorization": "Bearer "+mock_hipchatToken}
        mock_data = createMessageDict(mock_color, mock_message)

        mock_requests.post.assert_called_with(mock_messageUrl,
                                              headers=mock_token_header,
                                              data=mock_data)

    def test_configure(self):
        # Set right glassfrogtoken
        # Set wrong glassfrogtoken
        pass

    def test_hola_no_glassfrog_token(self):
        mock_messagedata = json.dumps(test_values.mock_messagedata)
        mock_color = strings.error_color
        mock_message = strings.set_token_first
        mock_messageDict = createMessageDict(mock_color, mock_message)

        glassfrog.app.glassfrogApiSettings = None
        rv = self.app.post('/hola', follow_redirects=True, data=mock_messagedata)
        return_messageDict = json.loads(rv.get_data())
        assert return_messageDict == mock_messageDict

    def test_hola(self):
        mock_messagedata = json.dumps(test_values.mock_messagedata)
        mock_color = strings.succes_color
        mock_message = strings.help_information
        mock_messageDict = createMessageDict(mock_color, mock_message)

        mock_glassfrogToken = 'myglassfrogtoken'
        glassfrog.app.glassfrogApiSettings = apiCalls.GlassfrogApiSettings(mock_glassfrogToken)
        rv = self.app.post('/hola', follow_redirects=True, data=mock_messagedata)
        return_messageDict = json.loads(rv.get_data())
        assert return_messageDict == mock_messageDict

    def test_hola_circles(self):
        # Send '/hola circles' message
        # Intercept circles call to glassfrog
        # Assert circles data
        pass

    def test_uninstalled(self):
        # Send uninstall call
        # Test removed related data
        pass

if __name__ == '__main__':
    unittest.main()
