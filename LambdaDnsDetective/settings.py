
INSTANCE_STATE_CHANGE = {
	"ValidDomains": ["cjgamer"],
	"StartInstances": {
		"Conditions": {
			"Previous": ["stopped"],
			"DNSTag": "DNSName"
		},
		"AddDNS": True,
		"Levels": [3]
	},
	"StopInstances": {
		"Conditions": {
			"Previous": ["running"],
			"DNSTag": "DNSName"
		},
		"RemoveDNS": True,
		"Levels": [3]
	}
}