# Bastion on-demand prototype
## Overview
This project creates the AWS resources necessary to deliver a bastion on-demand service offering from an AWS account.
For situations when it is not optimal to establish a persistent VPN or Direct Connect tunnel into a customer AWS environment,
this on-demand bastion-service facilitates secure remote access to a specific workload.  Additionally, Systems Manager
Run Command is used to provision a local account (linux or windows) on the target workload that you need to connect to.

## Disclaimer
All assets contained in this project should be considered beta.
Although some level of testing has been performed, additional error handling and logging should be implemented to meet customer/operational requirements.
Note, for beta testing, output values generated in the CloudFormation stacks (artifacts 2 and 3) may be considered sensitive.
Ensure access to your CloudFormation stacks is secured appropriately.
Any AWS region or OS specific limitations have been noted below.

## AWS Services
CloudTrail, CloudWatch, IAM Role, Lambda, Systems Manager-Run Command, EC2, S3, and Security Groups

## Use Case
The use case for prototype is to provide a publicly accessible, on-demand bastion instance (either linux or windows), that will terminate
after a specified expiration interval (e.g., 60 minutes) and perform all necessary cleanup as follows:

1. provision platform-based bastion instance (see artifacts 2 and 3) in public subnet, with security group open for remote access (ssh, rdp)
2. create local account on bastion instance using random generated username and random generated password
3. create local account on target managed instance (i.e., private instance you need a remote connection to)
4. scheduled cleanup with terminate bastion stacks that are expired and delete local account that was created on managed instance

* All actions will be fully logged in CloudTrail
* All managed instances must have the SSM agent installed, have Internet access, and be launched with an IAM Instance role with SSM access

## Artifacts
### CloudFormation
1. bastion_ondemand_core.yaml
Template establishes the core services (IAM role for lambda execution and 3 lambda function) for bastion on-demand.
2. create_linux_bastion.yaml
Template can be used to spin up a Linux bastion on-demand. Depends on bastion_ondemand_core.yaml being run first.
3. create_win_bastion.yaml
Template can be used to spin up a Windows bastion on-demand. Depends on bastion_ondemand_core.yaml being run first.

### Lambdas
1. BastionRandomUserAndPwd.py
Function called by create_linux_bastion.yaml or reate_win_bastion.yaml as custom resource to get a random username, random pwd, and expire time
2. BastionCreateLocalAcct.py
Function calls Systems Manager-Run Command to create a local account on the target managed instance
3. BastionTermExpired.py
Function scheduled via CloudWatch rule to routinely check for and terminate expired bastion stacks and cleanup local account

## Setup Instructions
1. Create S3 bucket to upload Lambda function code as zip files. This is used in bastion_ondemand_core.yaml
2. Create S3 bucket to store sshd_config or any other configs used to bootstrap and harden bastion instances
3. Execute bastion_ondemand_core.yaml to create IAM role and Lambda functions
4. Execute either create_linux_bastion.yaml or create_win_bastion.yaml to create an on-demand bastion stacks
5. Manually create CloudWatch rule and associate to BastionTermExpired function as schedule trigger at desired interval

* Step 5 is critical for automated cleanup; however, you may want to adjust intervals and test adhoc

## Other Prerequisites
1. Workloads must be configured to use Systems Manager agent
see https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/sysman-install-ssm-agent.html
2. Workloads must be launched with IAM role to allow Systems Manager access
see https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/systems-manager-access.html
3. You should already have your Security Group created for your bastion instances. This is specific to your security needs.
4. You should already have Security Groups configured for workloads to allow inbound from Bastion Security group above.
