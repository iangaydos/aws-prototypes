import random
import uuid
import httplib
import urlparse
import json
from datetime import datetime
from datetime import timedelta

def send_response(request, response, status=None, reason=None):
    """ Send our response to the pre-signed URL supplied by CloudFormation
    If no ResponseURL is found in the request, there is no place to send a
    response. This may be the case if the supplied event was for testing.
    """

    if status is not None:
        response['Status'] = status

    if reason is not None:
        response['Reason'] = reason

    if 'ResponseURL' in request and request['ResponseURL']:
        url = urlparse.urlparse(request['ResponseURL'])
        body = json.dumps(response)
        https = httplib.HTTPSConnection(url.hostname)
        https.request('PUT', url.path+'?'+url.query, body)

    return response

def RandomUserAndPwd_handler(event, context):
    # set expiration interval in minutes
    expire_interval = 10
    # build random bank of letters, characters for generating random pwd
    randNumbank = '0123456789'
    randCharbank = 'ABCDEFGHIJKLMNOPQRSTUVWYZ' + 'abcdefghijklmnopqrstuvwxyz'
    randSpecbank = '#!_'
    pwd = ''.join(random.choice(randCharbank) for i in range(4)) \
    + ''.join(random.choice(randSpecbank) for i in range(1)) \
    + ''.join(random.choice(randNumbank) for i in range(3)) \
    + ''.join(random.choice(randCharbank) for i in range(2))
    usertoken = ''.join(random.choice(randNumbank) for i in range(4))

    response = {
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Status': 'SUCCESS'
    }

    # PhysicalResourceId is meaningless here, but CloudFormation requires it
    if 'PhysicalResourceId' in event:
        response['PhysicalResourceId'] = event['PhysicalResourceId']
    else:
        response['PhysicalResourceId'] = str(uuid.uuid4())

    # There is nothing to do for a delete request
    if event['RequestType'] == 'Delete':
        return send_response(event, response)

    try:
        # check that Requestor supplied
        for key in ['Requestor']:
            if key not in event['ResourceProperties'] or not event['ResourceProperties'][key]:
                return send_response(
                    event, response, status='FAILED',
                    reason='The properties KeyId and PlainText must not be empty'
                )

        request_user = event['ResourceProperties']['Requestor']

        username = 'bastion_svc_' + usertoken
        print 'Bastion access requested by: ' + request_user + ' assigned generated username: ' + username
        # set expiration time
        expire_time = str(datetime.now() + timedelta(minutes=expire_interval))

        response['Data'] = {
            'random_pwd': pwd,
            'random_username': username,
            'request_user': request_user,
            'expire_time': expire_time
        }
        response['Reason'] = 'Success'

    except Exception as E:
        response['Status'] = 'FAILED'
        response['Reason'] = 'Lambda call failed: RandomUserAndPwd'

    return send_response(event, response)
