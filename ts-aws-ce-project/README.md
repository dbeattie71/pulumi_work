# Best Practices Project

This folder contains a Pulumi project to show various Pulumi concepts and practices, including but not limited to:

- Custom Resources
- Modules
- Helper Functions
- Transformations
- Data sources and .get() functions
- Unit and integration testing

# Project Architecture

(WIP)

- Load balancer to a
- instance scaling group that presents a web site and sends data to a
- API Gateway to a
- Lambda to
- MKS
- Fargate instance reads from MKS
- Fargate write to DynamoDB?

## Components

- Base VPC (maybe as a stack?)
- Web Frontend = LB and Instances
- API frontend = API GW and Lambda
- MKS queue
- Backend = Fargate plus DynamoDB
