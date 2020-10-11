import boto3

ec2 = boto3.client('ec2', region_name='ap-southeast-2')
route53 = boto3.client('route53', region_name='ap-southeast-2')


def check_ready_for_create_dns(valid_previous_states, dns_tag, valid_names, configuration, instance, messages):
	previous_state = instance['previousState']['name']
	configuration["DNSName"] = ""
	aws_id = instance['instanceId']
	configuration['InstanceId'] = instance['instanceId']

	if previous_state in valid_previous_states:
		instance_details = ec2.describe_instances(InstanceIds=[aws_id])
		tags = instance_details['Reservations'][0]['Instances'][0]['Tags']
		ip_address = instance_details['Reservations'][0]['Instances'][0]['PublicIpAddress']
		configuration['IpAddress'] = ip_address
		dns_tag_found = False
		dns_tag_value = ""
		core_dns_value = ""
		for tag in tags:
			if tag['Key'] == dns_tag:
				dns_tag_found = True
				dns_tag_value = tag['Value']
				core_dns_values = dns_tag_value.split('.')
				if len(core_dns_values) != 3:
					messages.append("Invalid DNS name: {}".format(dns_tag_value))
					return False
				core_dns_value = core_dns_values[1]

				if core_dns_value not in valid_names:
					messages.append("{} is not supported by available domains".format(core_dns_value))
					return False
				break

		if dns_tag_found:
			configuration["DNSName"] = dns_tag_value
			return True
		else:
			messages.append("{} was started, but there was no DNSName tag".format(aws_id))
			return False
	else:
		messages.append(
			"{} was started, but it was in an invalid state to set a DNS name (Previous state: {})".format(aws_id,
																										   previous_state))
		return False


def acquire_hosted_zone_id(dns_name, messages):
	zones = [{'Id': hz['Id'], 'Name': hz['Name']} for hz in route53.list_hosted_zones()['HostedZones']]
	target_id = ""
	dns_core = dns_name.split('.')[len(dns_name.split('.')) - 2]
	for zone in zones:
		if dns_core in zone['Name'].split("."):
			messages.append("Found matching hosted zone: {} ({})".format(
				zone['Name'],
				zone["Id"]
			))
			return zone["Id"]

	messages.append("Could not match DNS name to available hosted zone")
	return target_id


def remove_dns_name_from_route53(dns_name, configuration, messages):
	target_id = acquire_hosted_zone_id(dns_name, messages)

	if target_id:
		configuration['target_id'] = target_id

		try:
			records = route53.list_resource_record_sets(HostedZoneId=target_id)['ResourceRecordSets']
			target_record = {}
			for record in records:
				if record['Name'] == "{}.".format(dns_name):
					target_record = record

			route53.change_resource_record_sets(
				HostedZoneId=target_id,
				ChangeBatch={
					"Changes": [{"Action": 'DELETE', "ResourceRecordSet": target_record}]
				}
			)
			messages.append("DNS name: {} has been remove from Route53".format(dns_name))
			messages.append("Target record: {}".format(target_record))
			return True
		except Exception as ex:
			messages.append("Unable to remove record: {}".format(ex))
			print(ex)

	return False


def add_dns_name_to_instance(dns_name, ip_address, configuration, messages):
	target_id = acquire_hosted_zone_id(dns_name, messages)

	if target_id:
		configuration['target_id'] = target_id
		try:
			route53.change_resource_record_sets(
				HostedZoneId=target_id,
				ChangeBatch={
					"Comment": 'New record for starting instance',
					"Changes": [
						{
							"Action": 'CREATE',
							"ResourceRecordSet": {
								"Name": dns_name,
								"Type": 'A',
								"TTL": 300,
								'ResourceRecords': [{'Value': ip_address}]
							}
						}
					]
				}
			)
			messages.append("DNS name: {} has been attached to address: {}".format(dns_name, ip_address))
		except Exception as ex:
			error = ex.response['Error']
			exp_error = '[Tried to create resource record set [name=\'{}.\', type=\'A\'] but it already exists]'.format(dns_name)
			if error['Message'] == exp_error:
				messages.append("ERROR: This DNS name is already in use")
				return False
			else:
				messages.append("Unhandled exception: {}".format(ex))
				return False
		return True

	messages.append("Unable to match DNS name '{}' to an available hosted zone".format(dns_name))
	return False