# Networking bits

- DONE: Virtual network
- DONE: FE, BE, CRM Subnets and Security Groups
  - Also enabled network services for FE (storage) and BE (cosmos)

# Frontend Bits

- DONE: WAF
  - Using example rules
- DONE: CDN and Endpoint
- DONE: SPA Storage

# Backend Bits

- DONE: BE API Webapp
- WTG TEMPLATE DUMP: BE CosmosDB ()
  - Can you provide a template dump from one you have set up?
- WTG TEMPLATE DUMP: BE Function API ()
  - Can you provide a template dump from one you have set up?

# CRM Bits

- DONE: CRM API Webapp

# Redis Cache

- DONE: Common Redis Cache

# AppInsights Registrations

I think I have this set up correctly.

- DONE: BE WebApp
- DONE: CRM WebApp
- NOT DONE: Function API (WTG TO DO FUNCTION API - see above)

# Log Analytics Registrations

- NOT DONE: CDNs ()
  - Can you show me what you are referring to in UI

# General

- NOT DONE: Address subnet creation race condition that occasionally stops a subnet from being created the first time - maybe dependsOn vnet or something?
  error: autorest/azure: Service returned an error. Status=<nil> Code="AnotherOperationInProgress" Message="Another operation on this or dependent resource is in progress. To retrieve status of the operation use uri: https://management.azure.com/subscriptions/32b9cb2e-69be-4040-80a6-02cd6b2cc5ec/providers/Microsoft.Network/locations/uksouth/operations/3484c84f-0320-4c7a-9f63-d9e2449a9fea?api-version=2020-07-01." Details=[]
