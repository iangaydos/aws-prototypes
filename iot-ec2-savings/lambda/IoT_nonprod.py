import boto3

# update environment list values to match your convention for non-production
environment_list = ['Test', 'QA']
client = boto3.client('ec2')

def stop_instance(resource_id):
    # stops instance based on ResourceId
    response = client.stop_instances(
    InstanceIds=[resource_id]
    )
    status = 'IoT Shutdown: ' \
    + 'InstanceId_' + resource_id + ' PreviousState: ' \
    + response['StoppingInstances'][0]['PreviousState']['Name']
    return(status)

def start_instance(resource_id):
    # starts instance based on ResourceId
    response = client.start_instances(
    InstanceIds=[resource_id]
    )
    status = 'IoT StartUp: ' \
    + 'InstanceId_' + resource_id + ' starting from IoT DOUBLE press.'
    return(status)

def IoT_nonprod_handler(event, context):
    # IoT button payload sample
    # {
    # "serialNumber": "GXXXXXXXXXXXXXXXXX",
    # "batteryVoltage": "xxmV",
    # "clickType": "SINGLE" | "DOUBLE" | "LONG"
    # }
    # loop through list of ec2 instances based on a tag named "Environment"
    paginator = client.get_paginator('describe_tags')
    response_iterator = paginator.paginate(
        Filters=[
            {
                'Name': 'key',
                'Values': ['Environment']
            }
        ]
        )
    for i in response_iterator:
        for tag in i['Tags']:
            # check if Environment tag is in the target environment_list
            if tag['Value'] in environment_list:
                if event['clickType'] == 'SINGLE': # indicates stop event
                    response = stop_instance(tag['ResourceId'])
                    print response
                elif event['clickType'] == 'DOUBLE': # indicates start event
                    response = start_instance(tag['ResourceId'])
                    print response
