import * as pulumi from "@pulumi/pulumi";
import * as azure from "@pulumi/azure";
import * as azure_nextgen from "@pulumi/azure-nextgen";
import * as network from "@pulumi/azure-nextgen/network/latest";
import * as random from "@pulumi/random";
import { BaseNet } from "./base-net";
import { FrontEnd } from "./front-end";
import { BackEnd } from "./back-end";


//// Use config to store a base name for resources 
//// Added nameBase to the vault and storage account to avoid global naming conflicts.
//// This is also used for the custom resource.
const config = new pulumi.Config();
const nameBase = config.get("nameBase") || "mitchhrd"

//// Create the base networking environment that is used as a foundation for the other resources.
const baseNet = new BaseNet(nameBase, {
    location: "uksouth",
    vnetCidr: "10.4.1.0/24",
    spaCidr: "10.4.1.0/27", 
    beCidr: "10.4.1.32/27", 
    crmCidr: "10.4.1.64/27",
});
const resourceGroup = baseNet.resourceGroup

// Create the frontend components:
const frontEnd = new FrontEnd(nameBase, {
    resourceGroupName: resourceGroup.name,
    location: resourceGroup.location,
})

// Create the backend API components
const backEnd = new Backend(nameBase, {
    resourceGroupName: resourceGroup.name,
    location: resourceGroup.location,
    subnetId: baseNet.beSubnet.id,
})

export const endpointUrl = frontEnd.endpointUrl

// const appinsights = new azure_nextgen.insights.latest.Component("appinsights", {
//   resourceName: "appi-puluminextgetn01",
//   location: resourceGroup.location,
//   applicationType: "web",
//   kind: "web",
//   resourceGroupName: resourceGroup.name,
// });

// export const instrumentationKey = appinsights.instrumentationKey;

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


// const webapp02 = new azure_nextgen.web.v20200601.WebApp("webappcrm", {
//     resourceGroupName: resourceGroup.name,
//     location: resourceGroup.location,
//     name: "app-apicrmpulumi02",
//     enabled: true,
//     serverFarmId: appServicePlan.id,
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

