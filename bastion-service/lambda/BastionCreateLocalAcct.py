import boto3
import uuid
import httplib
import urlparse
import json

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

def is_linux_target(event, response):
    try:
        # extract username, pwd, and expiration date/time from event
        random_username = event['ResourceProperties']['random_username']
        random_pwd = event['ResourceProperties']['random_pwd']
        request_user = event['ResourceProperties']['request_user']
        expire_time = event['ResourceProperties']['expire_time']
        instance_id = event['ResourceProperties']['instance_id']
        # build shell script to execute
        cmd_str = 'useradd -m -s /bin/bash ' \
        + random_username + '\n' \
        + 'echo ' + random_username + ':' \
        + random_pwd + ' | chpasswd \n' \
        + 'echo random_user: ' + random_username \
        + ' created at request of: ' + request_user + ' \n'
        print cmd_str
        # establish boto3 client to Systems Manager
        ssm = boto3.client('ssm')
        ssm_response = ssm.send_command (
            InstanceIds = [instance_id],
            DocumentName = 'AWS-RunShellScript',
            Comment='create local account for remote access from bastion',
            Parameters={
                'commands' : [
                    cmd_str
                ]
            })
        print ssm_response['Command']['Status']
        print 'Bastion on-demand, local acct created by RunCommandId: ' \
        + ssm_response['Command']['CommandId']
        response['Data'] = {
            'random_pwd': random_pwd,
            'random_username': random_username,
            'request_user': request_user,
            'expire_time': expire_time,
            'instance_id': instance_id
        }
        response['Reason'] = 'Success'
    except Exception as E:
        response['Status'] = 'FAILED'
        response['Reason'] = 'Lambda Call failed : CreateBastLocalAcct_linuxTarget'
    return send_response(event, response)

def is_window_target(event, response):
    try:
        # extract username, pwd, and expiration date/time from event
        random_username = event['ResourceProperties']['random_username']
        random_pwd = event['ResourceProperties']['random_pwd']
        request_user = event['ResourceProperties']['request_user']
        expire_time = event['ResourceProperties']['expire_time']
        instance_id = event['ResourceProperties']['instance_id']
        # build shell script to execute
        cmd_str = "$User = \"" + random_username + "\" \n" \
        + "$Computer = $env:COMPUTERNAME \n" \
        + "$GroupName = 'Administrators' \n" \
        + "$ADSI = [ADSI](\"WinNT://$Computer\") \n" \
        + "$HelpDesk=$ADSI.Create(\"User\",$User) \n" \
        + "$HelpDesk.SetPassword(\"" + random_pwd + "\") \n" \
        + "$HelpDesk.SetInfo() \n" \
        + "$HelpDesk.Put(\"Description\"," \
        + "\"Bastion-Service Local Account\") \n" \
        + "$HelpDesk.SetInfo() \n" \
        + "$Group = $ADSI.Children.Find($GroupName, \"group\") \n" \
        + "$Group.Add((\"WinNT://$computer/$user\")) \n"
        print cmd_str
        # establish boto3 client to Systems Manager
        ssm = boto3.client('ssm')
        ssm_response = ssm.send_command (
            InstanceIds = [instance_id],
            DocumentName = 'AWS-RunPowerShellScript',
            Comment='create local account for remote access from bastion',
            Parameters={
                'commands' : [
                    cmd_str
                ]
            })
        print ssm_response['Command']['CommandId']
        print 'Bastion on-demand, local acct created by RunCommandId: ' \
        + ssm_response['Command']['CommandId']
        response['Data'] = {
            'random_pwd': random_pwd,
            'random_username': random_username,
            'request_user': request_user,
            'expire_time': expire_time,
            'instance_id': instance_id
        }
        response['Reason'] = 'Success'
    except Exception as E:
        response['Status'] = 'FAILED'
        response['Reason'] = 'Lambda Call failed : CreateBastLocalAcct_windowsTarget'
    return send_response(event, response)

def CreateBastLocalAcct_handler(event, context):
        response = {
            'StackId': event['StackId'],
            'RequestId': event['RequestId'],
            'LogicalResourceId': event['LogicalResourceId'],
            'Status': 'SUCCESS'
        }
        try:
            # PhysicalResourceId is meaningless here, but CloudFormation requires it
            if 'PhysicalResourceId' in event:
                response['PhysicalResourceId'] = event['PhysicalResourceId']
            else:
                response['PhysicalResourceId'] = str(uuid.uuid4())
            # There is nothing to do for a delete request
            if event['RequestType'] == 'Delete':
                return send_response(event, response)
            if event['ResourceProperties']['platform'] == 'linux':
                return is_linux_target(event, response)
            else:
                return is_window_target(event, response)
        except Exception as E:
            response['Status'] = 'FAILED'
            response['Reason'] = 'Lambda Call failed : CreateBastLocalAcct'
        return send_response(event, response)
