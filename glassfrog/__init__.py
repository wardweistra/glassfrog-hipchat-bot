#!/usr/bin/env python3
from flask import Flask, json, request, render_template, flash
import requests

app = Flask(__name__)
app.secret_key = 'not_so_secret'

myserver = "http://5.157.82.115:45277"
app.hipchatToken = ''
app.glassfrogToken = ''
app.hipchatApiUrl = ''
app.roomId = ''


@app.route('/')
def hello_world():
    return '<a target="_blank" href="https://www.hipchat.com/addons/install?url='+myserver+"/capabilities.json"+'">Install Glassfrog HipChat Integration</a>'


@app.route('/capabilities.json')
def capabilities():
    capabilities_dict = \
        {
            "name": "Glassfrog Hipchat Bot",
            "description": "A Hipchat bot for accessing Glassfrog",
            "key": "glassfrog-hipchat-bot",
            "links": {
                "homepage": myserver,
                "self": myserver+"/capabilities.json"
            },
            "vendor": {
                "name": "The Hyve",
                "url": "https://www.thehyve.nl/"
            },
            "capabilities": {
                "hipchatApiConsumer": {
                    "fromName": "Glassfrog Hipchat Bot",
                    "scopes": [
                        "send_notification",
                        "view_room",
                        "view_group"
                    ]
                },
                "installable": {
                    "allowGlobal": False,
                    "allowRoom": True,
                    "callbackUrl": myserver+"/installed"
                },
                "webhook": [
                    {
                        "event": "room_message",
                        "pattern": "\\A\\/hola\\b",
                        "url": myserver+"/hola",
                        "name": "Holacracy webhook",
                        "authentication": "jwt"
                    }
                ],
                "configurable": {
                    "url": myserver+"/configure.html"
                }
            }
        }
    return json.jsonify(capabilities_dict)


@app.route('/installed', methods=['GET', 'POST'])
def installed():
    if request.method == 'POST':
        installdata = json.loads(request.get_data())
        # b'{"oauthId": "f3100c47-9936-40e8-a8aa-798b1e8da8f0", "capabilitiesUrl": "https://api.hipchat.com/v2/capabilities", "roomId": 2589171, "groupId": 46617, "oauthSecret": "Jgtf1Baj5KrSpXHZ7LbB0H3Krwr6cotrkQgkJm9C"}'
        print(installdata)
        CLIENT_ID = installdata['oauthId']
        CLIENT_SECRET = installdata['oauthSecret']
        app.roomId = installdata['roomId']

        capabilitiesdata = json.loads(requests.get(installdata['capabilitiesUrl']).text)
        tokenUrl = capabilitiesdata['capabilities']['oauth2Provider']['tokenUrl']
        print(tokenUrl)

        client_auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
        post_data = {"grant_type": "client_credentials",
                     "scope": "send_notification"}
        tokendata = json.loads(requests.post(tokenUrl,
                                             auth=client_auth,
                                             data=post_data).text)
        print(tokendata)
        # {'expires_in': 431999999, 'group_name': 'tranSMART', 'access_token': 'qjVBeM4ckCYzrc2prQMwuRZnHB3xUVsBwZISP0TF', 'group_id': 46617, 'scope': 'send_notification', 'token_type': 'bearer'}
        app.hipchatToken = tokendata['access_token']
        app.hipchatApiUrl = capabilitiesdata['capabilities']['hipchatApiProvider']['url']

        sendMessage('green', "Installed successfully. Please set Glassfrog Token in the Hipchat Integration Configure page.")
    return ('', 200)


@app.route('/installed/<oauthId>', methods=['GET', 'POST', 'DELETE'])
def uninstall(oauthId):
    # TODO Delete entries related to this installation (oauthID) from database.
    return ('', 200)


def getCircles():
    headers = {'X-Auth-Token': app.glassfrogToken}
    circlesUrl = 'https://glassfrog.holacracy.org/api/v3/circles'
    circlesresponse = requests.get(circlesUrl, headers=headers)
    print(circlesresponse)
    code = circlesresponse.status_code
    print(code)
    circles = json.loads(circlesresponse.text)
    print(circles)
    return code, circles


def createMessageDict(color, message):
    message_dict = {
        "color": color,
        "message": message,
        "notify": False,
        "message_format": "text"
        }
    return message_dict


def sendMessage(color, message):
    messageUrl = app.hipchatApiUrl+'/room/{}/notification'.format(app.roomId)
    token_header = {"Authorization": "Bearer "+app.hipchatToken}
    data = createMessageDict(color, message)
    messageresponse = requests.post(messageUrl,
                                    headers=token_header,
                                    data=data)


@app.route('/hola', methods=['GET', 'POST'])
def hola():
    print(request.get_data())
    # b'{"event": "room_message", "item": {"message": {"date": "2016-05-26T15:32:43.700609+00:00", "from": {"id": 351107, "links": {"self": "https://api.hipchat.com/v2/user/351107"}, "mention_name": "WardWeistra", "name": "Ward Weistra", "version": "00000000"}, "id": "715f101f-1baa-4a5c-958a-9c6c7efaaa1f", "mentions": [], "message": "/test", "type": "message"}, "room": {"id": 2589171, "is_archived": false, "links": {"members": "https://api.hipchat.com/v2/room/2589171/member", "participants": "https://api.hipchat.com/v2/room/2589171/participant", "self": "https://api.hipchat.com/v2/room/2589171", "webhooks": "https://api.hipchat.com/v2/room/2589171/webhook"}, "name": "The Hyve - Holacracy", "privacy": "private", "version": "0XLIKALD"}}, "oauth_client_id": "ed8bb9f0-02d8-426b-9226-0d50fdcd47ea", "webhook_id": 4965523}'
    if app.glassfrogToken != '':
        code, message = getCircles()
        print(message)
        message_dict = createMessageDict('green', message)
    else:
        message_dict = createMessageDict('red', "Please set the Glassfrog token first in the plugin configuration")
    return json.jsonify(message_dict)


@app.route('/configure.html', methods=['GET', 'POST'])
def configure():
    if request.method == 'POST':
        app.glassfrogToken = request.form['glassfrogtoken']
        code, message = getCircles()
        if code == 200:
            flashmessage = 'Valid Glassfrog Token stored'
            sendMessage('green', "Configured successfully. Type /hola to get started!")
        else:
            flashmessage = 'Encountered Error '+str(code)+' when testing the Glassfrog Token.'
            if 'message' in message:
                flashmessage = flashmessage + ' Message given: \''+message['message']+'\'.'
        flash(flashmessage)
    return render_template('configure.html', glassfrogtoken=app.glassfrogToken)

if __name__ == '__main__':
    app.run()
