# AWS (API Gateway) -> Lambda -> Event Bridge -> Lambda -> DynamoDB

- something about the event rule
  - If you make the cycle below where things ar eworking and then totally remove event rule from code and add back in you are back to it not working.
  - So adding the target manually sets something for the event rule that is not set when programmed
- test to prove:
  - stack up
  - Test it doesn't write to dynamodb
  - manually add another target - set retentio to 1 hour to distinguish
  - Test - should see two writes to dynamodb
  - Remove manual target
  - Test - should still see writes
  - Remove target from code and up and add it back in in code and up and test and see it works.

#####

The goal is to stand up an infrastructure that demonstrates the following use-case:

- There is a pre-existing API Gateway.
- I want to stand up a couple of lambda functions and event bridge bus and a DynamoDB.
- I want to connect lambda #1 to the API GW.
- Lambda #1 receieves requests from the API GW and forwards it to the EventBridge
- Lambda #2 is triggered by EventBridge and writes data to the DynamoDB.

# Folder Contents

- existing-resources: this is a Pulumi project to create existing resources resources to be used as pre-existing resoruces for the main lambda-eventbridge-lambda-dynamodb project. This project is not directly referenced by the min project.
- lambda-eventbridge-dynamodb: this is the main project that stands up the system using the "existing" VPC and API GW.
