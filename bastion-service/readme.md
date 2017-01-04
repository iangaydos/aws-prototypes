# Bastion on-demand prototype
## Overview
This project creates the AWS resources necessary to deliver a bastion
on-demand service offering from an AWS account.

## Disclaimer
All assets contained in this project should be considered beta.
Although some level of testing has been performed, additional error handling and logging should be implemented to meet customer/operational requirements.
Any AWS region or OS specific limitations have been noted below.

## AWS Services
CloudTrail, CloudWatch, IAM Role, Lambda, Systems Manager-Run Command, EC2, S3, and Security Groups

## Assumptions and Use Case
The use case for prototype is to provide a publicly accessible, on-demand bastion instance (either linux or windows), that will terminate
after a specified expiration interval (e.g., 60 minutes) and perform all necessary cleanup according to the following flow:
1. provision platform based (linux or windows) bastion instance in public subnet, with security group open for remote access (ssh, rdp)
2. create local account on bastion instance using random generated username and random generated password
3. create local account on target managed instance (i.e., private instance you need a remote connection to)
4. scheduled cleanup with terminate bastion stacks that are expired and delete local account that was created on managed instance
* - all actions will be fully logged in CloudTrail
* - All managed instances must have the SSM agent installed, have Internet access, and be launched with an IAM Instance role with SSM access

## Artifacts
### CloudFormation
1. cft_bastion_ondemand_core.yaml
Template establishes the core services (IAM role for lambda execution and 3 lambda function) for bastion on-demand.
2. cft_create_linux_bastion.yaml
Template can be used to spin up a Linux bastion on-demand. Depends on cft_bastion_ondemand_core.yaml being run first.
3. cft_create_win_bastion.yaml
Template can be used to spin up a Windows bastion on-demand. Depends on cft_bastion_ondemand_core.yaml being run first.

### Lambda
1. BastionRandomUserAndPwd.py
Function called by cft_create_linux_bastion.yaml or cft_create_win_bastion.yaml as custom resource to get a random username, random pwd, and expire time
2. BastionCreateLocalAcct.py
Function calls Systems Manager-Run Command to create a local account on the target managed instance
3. BastionTermExpired.py
Function scheduled via CloudWatch rule to routinely check for and terminate expired bastion stacks and cleanup local account

## Setup Instructions
1. Create S3 bucket to upload Lambda function code as zip files. This is used in cft_bastion_ondemand_core.yaml
2. Create S3 bucket to store sshd_config or any other configs used to bootstrap and harden bastion instances
3. Execute cft_bastion_ondemand_core.yaml to create IAM role and Lambda functions
4. Execute either cft_create_linux_bastion.yaml or cft_create_win_bastion.yaml to create an on-demand bastion stacks
5. Create CloudWatch rule and associate to BastionTermExpired function as schedule trigger at desired interval
