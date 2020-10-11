import settings
from tools import check_ready_for_create_dns, add_dns_name_to_instance, remove_dns_name_from_route53


def handle_stop_instance(event_detail, messages):
	instances = event_detail['responseElements']['instancesSet']['items']
	configurations = {'Instances': []}
	failure = False

	for instance in instances:
		configuration = settings.INSTANCE_STATE_CHANGE
		try:
			ready = check_ready_for_create_dns(
				valid_previous_states=configuration['StopInstances']['Conditions']['Previous'],
				dns_tag=configuration['StopInstances']['Conditions']['DNSTag'],
				valid_names=configuration['ValidDomains'],
				configuration=configuration,
				instance=instance,
				messages=messages
			)

			if ready and configuration['StopInstances']['RemoveDNS']:
				success = remove_dns_name_from_route53(
					dns_name=configuration["DNSName"],
					configuration=configuration,
					messages=messages
				)
				configuration['success'] = success
				configurations['Instances'].append(configuration)
				if not success:
					failure = True

		except Exception as ex:
			messages.append("Instance stop failed: {}".format(ex))
			failure = True
			configuration['success'] = False
			configurations['Instances'].append(configuration)

	configurations['success'] = not failure
	return configurations


def handle_start_instance(event_detail, messages):

	instances = event_detail['responseElements']['instancesSet']['items']
	failure = False
	configurations = {'Instances': []}

	for instance in instances:
		configuration = settings.INSTANCE_STATE_CHANGE
		try:
			ready = check_ready_for_create_dns(
				valid_previous_states=configuration['StartInstances']['Conditions']['Previous'],
				dns_tag=configuration['StartInstances']['Conditions']['DNSTag'],
				valid_names=configuration['ValidDomains'],
				configuration=configuration,
				instance=instance,
				messages=messages
			)

			if ready and configuration['StartInstances']['AddDNS']:
				success = add_dns_name_to_instance(
					dns_name=configuration["DNSName"],
					ip_address=configuration['IpAddress'],
					configuration=configuration,
					messages=messages
				)
				configuration['success'] = success
				configurations['Instances'].append(configuration)
				if not success:
					failure = True
				continue

			configuration['success'] = False
			failure = True
			configurations['Instances'].append(configuration)

		except Exception as ex:
			messages.append("Adding DNS failed for {}: {}".format(instance['instanceId'], ex))
			configuration['success'] = False
			failure = True
			configurations['Instances'].append(configuration)

	configurations['success'] = not failure
	return configurations

