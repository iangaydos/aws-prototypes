import boto3
from datetime import datetime
from datetime import timedelta

client = boto3.client('cloudformation')

def evaluate_stack(stack_name, response):
    # paginate through stack all details to evaluate to determine
    # if a stack is bastion related and is expired and ready to terminate
    paginator = client.get_paginator('describe_stacks')
    iterator = paginator.paginate(StackName = stack_name)
    # iterate through stack paginator checking if Outputs key exist
    for i in iterator:
        for stack in i['Stacks']:
            if 'Outputs' not in stack.keys():
                response['Status'] = 'SUCCESS'
                response['Reason'] = 'No outputs'
                response['StackName'] = stack_name
            else:
                stack_data = {}
                for item in stack['Outputs']:
                    stack_data[item['OutputKey']] = item['OutputValue']
                # check Output key to see if stack is a Bastion stack
                if 'BastionFlag' not in stack_data.keys():
                    response['Status'] = 'SUCCESS'
                    response['Reason'] = 'No bastion_flag, nothing to do'
                    response['StackName'] = stack_name
                    return (response)
                else:
                    # is bastion stack so check ExpireTime
                    try:
                        if stack_data['ExpireTime'] < str(datetime.now()):
                            print 'Automated cleanup, terminating stack: ' \
                            + stack_name + ' expired: ' \
                            + stack_data['ExpireTime']
                            # delete expired stack
                            client.delete_stack(StackName=stack_name)
                            # cleanup local account based on platform
                            if stack_data['BastionPlatform'] == 'windows':
                                response = is_windows_target \
                                (stack_data['RandomUsername'], \
                                stack_data['TargetInstanceId'], \
                                stack_data['ExpireTime'], response)
                            else:
                                response = is_linux_target \
                                (stack_data['RandomUsername'], \
                                stack_data['TargetInstanceId'], \
                                stack_data['ExpireTime'], response)
                        else:
                            response['Status'] = 'SUCCESS'
                            response['Reason'] = 'expire time not yet expired'
                            response['StackName'] = stack_name
                            return (response)
                    except Exception as E:
                        response['StackName'] = stack_name
                        response['Status'] = 'FAILED'
                        response['Reason'] = 'Call failed - evaluate_stack'
                        response['Exception'] = E
    return(response)

def is_windows_target(random_username, instance_id, expire_time, response):
    # delete local account that was created on a managed instance
    # as part of provisioning bastion on-demand access
    try:
        # build shell script to execute
        cmd_str = "$User = \"" + random_username + "\" \n" \
        + "$Computername = $env:COMPUTERNAME \n" \
        + "$ADSIComp = [adsi]\"WinNT://$Computername\" \n" \
        + "$ADSIComp.Delete(\"User\",$User) \n"
        print cmd_str
        # establish boto3 client to Systems Manager
        ssm = boto3.client('ssm')
        ssm_response = ssm.send_command (
            InstanceIds = [instance_id],
            DocumentName = 'AWS-RunPowerShellScript',
            Comment='delete local account from expired bastion stack',
            Parameters={
                'commands' : [
                    cmd_str
                ]
            })
        print ssm_response['Command']['Status']
        print ssm_response['Command']['CommandId']
        response['Status'] = ssm_response['Command']['Status']
        response['Reason'] = 'SUCCESS'
    except Exception as E:
        response['Status'] = 'FAILED'
        response['Reason'] = 'Call failed - is_windows_target'
        response['Exception'] = E
    return (response)

def is_linux_target(random_username, instance_id, expire_time, response):
    # delete local account that was created on a managed instance
    # as part of provisioning bastion on-demand access
    try:
        # build shell script to execute
        cmd_str = "userdel -r " + random_username + " \n" \
        "echo " + random_username + " expired baston account has been deleted"
        print cmd_str
        # establish boto3 client to Systems Manager
        ssm = boto3.client('ssm')
        ssm_response = ssm.send_command (
            InstanceIds = [instance_id],
            DocumentName = 'AWS-RunShellScript',
            Comment='delete local account from expired bastion stack',
            Parameters={
                'commands' : [
                    cmd_str
                ]
            })
        print ssm_response['Command']['Status']
        print ssm_response['Command']['CommandId']
        response['Status'] = ssm_response['Command']['Status']
        response['Reason'] = 'SUCCESS'
    except Exception as E:
        response['Status'] = 'FAILED'
        response['Reason'] = 'Call failed - is_linux_target'
        response['Exception'] = E
    return (response)

def expired_bastion_handler(event, context):
    # generate list of all completed stacks running in Region
    list_of_stacks = client.list_stacks(
        StackStatusFilter=['CREATE_COMPLETE'])
    response = {
        'Status' : 'SUCCESS',
        'Reason' : 'Nothing to do'
    }
    #loop through list of stacks checking for expired bastion stacks
    for s in list_of_stacks['StackSummaries']:
        response = evaluate_stack(s['StackName'], response)
        print 'Status: ' + response['Status'] +  ' : Reason: ' \
        + response['Reason'] + ' : StackName: ' + s['StackName']
        return 'expired bastions have been terminated, local account cleaned'
