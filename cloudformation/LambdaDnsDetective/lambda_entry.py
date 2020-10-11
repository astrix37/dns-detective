import boto3
import os
import json
from handle_actions import handle_start_instance, handle_stop_instance


def lambda_handler(event, context):
    # Setup
    sns = boto3.client('sns', region_name='ap-southeast-2')
    event_detail = event['detail']
    event_name = event_detail['eventName']
    messages = []

    # Execution
    print(event_detail)
    target_actions = {
        'StartInstances': handle_start_instance,
        'StopInstances': handle_stop_instance
    }
    config = {}

    try:
        config = target_actions[event_name](event_detail, messages)
        messages.append("Execution has completed")
    except Exception as ex:
        messages.append("Execution has failed: {}".format(ex))
        config['success'] = False

    message = "\n".join(messages)
    message += "\n\n" + ("Succeeded".upper() if config['success'] else "Failed".upper())
    message += "\n\n\n" + "Configuration: {}".format(json.dumps(config, indent=2))

    snsresult = sns.publish(
        TargetArn=os.environ['AlertSNS'],
        Subject="Event Action {} ({})".format(
            "Succeeded" if config['success'] else "Failed",
            event_name
        ),
        Message=message
    )
    print(snsresult)
