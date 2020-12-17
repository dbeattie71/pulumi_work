import * as pulumi from "@pulumi/pulumi";
import { Input, Output } from "@pulumi/pulumi"
import * as insights from "@pulumi/azure-nextgen/insights/latest";
import * as cache from "@pulumi/azure-nextgen/cache/latest";
import * as storage from "@pulumi/azure-nextgen/storage/latest";
import * as keyvault from "@pulumi/azure-nextgen/keyvault/latest";


// These are the input properties supported by the custom resource.
// Can be anything that makes sense. Supporting location and tags in this example.
// - resourceGroupName: resource group in which to launch these resources
// - location: location for these resources. 
interface SharedElementsArgs {
    resourceGroupName: Input<string>;
    location: Input<string>;
    tenantId: Input<string>;
    vaultObjectId: Input<string>;
};

export class SharedElements extends pulumi.ComponentResource {
  // The output properties for the custom resource.
  // Can be anything that makes sense. 
  // In this case, the endpoint URL is returned.
  public readonly instrumentationKey: Output<string>;
  public readonly webBackupStorageAccountUrl: Output<string>;
  //private readonly sa: storage.Account;


  // Standard constructor declaration 
  // - name: this is standard resource declaration name. In the case of this custom resource, it is also used as a basis for the resource names.
  // - args: the input properties for the custom resource as declared in the Interface above.
  // - opts: supports standard Pulumi resource options (e.g. the protect flag or the dependsOn flag).
  constructor(name: string, args: SharedElementsArgs, opts?: pulumi.ComponentResourceOptions) {
    // MUST HAVE this super() call to register the custom resource.
    // You'll see this string in the pulumi up
    super("custom:x:SharedElements", name, args, opts);

    const resourceGroupName = args.resourceGroupName
    const location = args.location
    const tenantId = args.tenantId
    const vaultObjectId = args.vaultObjectId

    const beAppInsights = new insights.Component(`${name}-app-insights`, {
        applicationType: "web",
        flowType: "Bluefield",
        kind: "web",
        location: location,
        requestSource: "rest",
        resourceGroupName: resourceGroupName,
        resourceName: `${name}-app-insights`
    }, {parent: this});


    // create the shared redis cache
    //// Azure takes FOREVER AND A DAY to create redis cache. So commenting out to speed up testing/demos for the time being.
    // const redis = new cache.Redis(`${name}-redis`, {
    //   name: `${name}-redis`,
    //   resourceGroupName: resourceGroupName,
    //   location: location,
    //   sku: {
    //       capacity: 1,
    //       family: "C",
    //       name: "Basic",
    //   },
    // }, {parent: this});
    
    // create the shared "stcards" storage account
    const stcards = new storage.StorageAccount(`${name}stcards`, {
      resourceGroupName: resourceGroupName,
      accountName: `${name}stcards`,
      location: location,
      sku: {
          name: "Standard_LRS",
      },
      kind: "StorageV2", 
      /*tags: {
        Environment: "Dev",
        CostCenter: "VSE",
      }*/
    }, {parent:this});

    const stcardsContainer = new storage.BlobContainer(`${name}stcardscont`, {
      resourceGroupName: resourceGroupName,
      accountName: stcards.name,
      containerName: `${name}stcardscont`
    }, {parent: this})

    const webBackups = new storage.StorageAccount(`${name}webbackups`, {
      resourceGroupName: resourceGroupName,
      accountName: `${name}webbackups`,
      location: location,
      sku: {
          name: "Standard_LRS",
      },
      kind: "StorageV2", 
      /*tags: {
        Environment: "Dev",
        CostCenter: "VSE",
      }*/
    }, {parent:this});

    const webBackupsContainer = new storage.BlobContainer(`${name}webbackupscontainer`, {
      resourceGroupName: resourceGroupName,
      accountName: stcards.name,
      containerName: `${name}webbackupscontainer`
    }, {parent: this})

    const vault = new keyvault.Vault(`${name}-vault`, {
      vaultName: `${name}-vault`,
      resourceGroupName: resourceGroupName,
      location: location,
      properties: {
          accessPolicies: [{
              objectId: vaultObjectId, // Info on how to find this value: https://docs.microsoft.com/en-us/azure/key-vault/general/assign-access-policy-cli#acquire-the-object-id
              permissions: {
                  certificates: [
                      "get",
                      "list",
                      "delete",
                      "create",
                      "import",
                      "update",
                      "managecontacts",
                      "getissuers",
                      "listissuers",
                      "setissuers",
                      "deleteissuers",
                      "manageissuers",
                      "recover",
                      "purge",
                  ],
                  keys: [
                      "encrypt",
                      "decrypt",
                      "wrapKey",
                      "unwrapKey",
                      "sign",
                      "verify",
                      "get",
                      "list",
                      "create",
                      "update",
                      "import",
                      "delete",
                      "backup",
                      "restore",
                      "recover",
                      "purge",
                  ],
                  secrets: [
                      "get",
                      "list",
                      "set",
                      "delete",
                      "backup",
                      "restore",
                      "recover",
                      "purge",
                  ],
              },
              tenantId: tenantId,
          }],
          enabledForDeployment: true,
          enabledForDiskEncryption: true,
          enabledForTemplateDeployment: true,
          sku: {
              family: "A",
              name: "standard",
          },
          tenantId: tenantId,
      },
 
    }, {parent: this});

    this.registerOutputs({});

    this.instrumentationKey = beAppInsights.instrumentationKey 
    this.webBackupStorageAccountUrl = pulumi.interpolate`${webBackups.primaryEndpoints.blob}${webBackupsContainer.name}`
  }
}
