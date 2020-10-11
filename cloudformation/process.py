import json
import os


def process():
    print("Processing")
    build_number = os.environ['BUILD_NUMBER']

    # Open cf_template
    content = json.loads(open('cf_template.json', 'r').read())

    # Modify
    for key in content["Resources"]:
        if key.startswith("Lambda"):
            s3_key = "lambda/{}-{}.zip".format(key, build_number)
            print("Found: {} (key = {})".format(key, s3_key))
            content["Resources"][key]['Properties']['Code']['S3Key'] = s3_key

    # Save cf_template
    f = open("cf_template.json", 'w')
    f.write(json.dumps(content, indent=3))
    f.close()

    print("Processing complete")


if __name__ == "__main__":
    process()