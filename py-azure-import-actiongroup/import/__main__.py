"""An Azure Python Pulumi program"""

import pulumi
import pulumi_azure as azure

rgname='mitch-rg'
agname='mitch-ag'
name = "mitchimp"
import_resource_group = azure.core.ResourceGroup(name+"ResourceGroup", location="East US",
  name=rgname,
  opts=pulumi.ResourceOptions(import_='/subscriptions/32b9cb2e-69be-4040-80a6-02cd6b2cc5ec/resourceGroups/'+rgname)
)


## SDKs: pulumi-azure: v3.15.0; pulumi: v2.5.0
import_action_group = azure.monitoring.ActionGroup(name+"ActionGroup",
    name=agname,
    resource_group_name=import_resource_group.name,
    short_name="p0action",
    webhook_receivers=[{ 
        "name": "callmyapiaswell",
        "service_uri": "http://example.com/alert",
        "use_common_alert_schema": False,
    }],
    opts=pulumi.ResourceOptions(import_='/subscriptions/32b9cb2e-69be-4040-80a6-02cd6b2cc5ec/resourceGroups/'+rgname+'/providers/microsoft.insights/actionGroups/'+agname)
)

## Current SDK 
# import_action_group = azure.monitoring.ActionGroup(name+"ActionGroup",
#     name=agname,
#     resource_group_name=import_resource_group.name,
#     short_name="p0action",
#     webhook_receivers=[azure.monitoring.ActionGroupWebhookReceiverArgs(
#         name="callmyapiaswell",
#         service_uri="http://example.com/alert",
#         use_common_alert_schema=False,
#     )],

#     opts=pulumi.ResourceOptions(import_='/subscriptions/32b9cb2e-69be-4040-80a6-02cd6b2cc5ec/resourceGroups/'+rgname+'/providers/microsoft.insights/actionGroups/'+agname)
# )

