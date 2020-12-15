import * as pulumi from "@pulumi/pulumi";
import * as cache from "@pulumi/azure-nextgen/cache/latest";
import { BaseNet } from "./base-net";
import { FrontEnd } from "./front-end";
import { BackEnd } from "./back-end";


//// Use config to store a base name for resources 
//// Added nameBase to the vault and storage account to avoid global naming conflicts.
//// This is also used for the custom resource.
const config = new pulumi.Config();
const nameBase = config.get("nameBase") || "mitchhrd"

const vnetCidr = "10.4.1.0/24"
const spaCidr = "10.4.1.0/27"
const beCidr = "10.4.1.32/27" 
const crmCidr =  "10.4.1.64/27"

//// Create the base networking environment that is used as a foundation for the other resources.
const baseNet = new BaseNet(nameBase, {
    location: "uksouth",
    vnetCidr: vnetCidr,
    spaCidr: spaCidr,
    beCidr: beCidr, 
    crmCidr: crmCidr,
});
const resourceGroup = baseNet.resourceGroup

// Create the frontend components:
const frontEnd = new FrontEnd(nameBase, {
    resourceGroupName: resourceGroup.name,
    location: resourceGroup.location,
})

// Create the backend API components
const beapi = new BackEnd(`${nameBase}-be`, {
    resourceGroupName: resourceGroup.name,
    location: resourceGroup.location,
    allowedAccess: spaCidr, 
})

// Create the CRM API components 
const crm = new BackEnd(`${nameBase}-crm`, {
    resourceGroupName: resourceGroup.name,
    location: resourceGroup.location,
    allowedAccess: beCidr, 
})

// Create the Redis Cache
const redis = new cache.Redis(`${nameBase}-redis`, {
    name: `${nameBase}-redis`,
    resourceGroupName: resourceGroup.name,
    location: resourceGroup.location,
    sku: {
        capacity: 1,
        family: "C",
        name: "Basic",
    },
});


export const frontendUrl = frontEnd.url
export const backendApiUrl = beapi.url
export const crmApiUrl = crm.url

// const stcards = new azure_nextgen.storage.latest.StorageAccount("stcards", {
//     resourceGroupName: resourceGroup.name,
//     accountName: `${nameBase}`+"stpuluminextgen01",
//     location: resourceGroup.location,
//     sku: {
//         name: "Standard_LRS",
//     },
//     kind: "StorageV2", 
//     /*tags: {
//       Environment: "Dev",
//       CostCenter: "VSE",
//     }*/
// });
// const blobContainer = new azure_nextgen.storage.latest.BlobContainer("blobContainer", {
//     resourceGroupName: resourceGroup.name,
//     accountName: stcards.name,
//     containerName: "$web",
// });


// const vault = new azure_nextgen.keyvault.latest.Vault("vault01", {
//     location: resourceGroup.location,
//     properties: {
//         accessPolicies: [{
//             objectId: "00000000-0000-0000-0000-000000000000",
//             permissions: {
//                 certificates: [
//                     "get",
//                     "list",
//                     "delete",
//                     "create",
//                     "import",
//                     "update",
//                     "managecontacts",
//                     "getissuers",
//                     "listissuers",
//                     "setissuers",
//                     "deleteissuers",
//                     "manageissuers",
//                     "recover",
//                     "purge",
//                 ],
//                 keys: [
//                     "encrypt",
//                     "decrypt",
//                     "wrapKey",
//                     "unwrapKey",
//                     "sign",
//                     "verify",
//                     "get",
//                     "list",
//                     "create",
//                     "update",
//                     "import",
//                     "delete",
//                     "backup",
//                     "restore",
//                     "recover",
//                     "purge",
//                 ],
//                 secrets: [
//                     "get",
//                     "list",
//                     "set",
//                     "delete",
//                     "backup",
//                     "restore",
//                     "recover",
//                     "purge",
//                 ],
//             },
//             tenantId: "701766e0-5785-4e08-969d-87bbce0d356b",
//         }],
//         enabledForDeployment: true,
//         enabledForDiskEncryption: true,
//         enabledForTemplateDeployment: true,
//         sku: {
//             family: "A",
//             name: "standard",
//         },
//         tenantId: "701766e0-5785-4e08-969d-87bbce0d356b",
//     },
//     resourceGroupName: resourceGroup.name,
//     vaultName: `${nameBase}-`+"vault-task01", 
// });

