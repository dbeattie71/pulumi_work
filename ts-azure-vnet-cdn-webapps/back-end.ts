import * as pulumi from "@pulumi/pulumi";
import { Input, Output } from "@pulumi/pulumi"
import * as web from "@pulumi/azure-nextgen/web/latest";

// These are the input properties supported by the custom resource.
// Can be anything that makes sense. Supporting location and tags in this example.
// - resourceGroupName: resource group in which to launch these resources
// - location: location for these resources. 
interface BackEndArgs {
    resourceGroupName: Input<string>;
    location: Input<string>;
};

export class BackEndArgs extends pulumi.ComponentResource {
    // The output properties for the custom resource.
    // Can be anything that makes sense. 
    // In this case, the endpoint URL is returned.
    public readonly webappUrl: Output<string>;
    //private readonly sa: storage.Account;


    // Standard constructor declaration 
    // - name: this is standard resource declaration name. In the case of this custom resource, it is also used as a basis for the resource names.
    // - args: the input properties for the custom resource as declared in the Interface above.
    // - opts: supports standard Pulumi resource options (e.g. the protect flag or the dependsOn flag).
    constructor(name: string, args: BackEndArgs, opts?: pulumi.ComponentResourceOptions) {
        // MUST HAVE this super() call to register the custom resource.
        // You'll see this string in the pulumi up
        super("custom:x:BackEnd", name, args, opts);

        const resourceGroupName = args.resourceGroupName
        const location = args.location

        const beAppServicePlan = new web.AppServicePlan(`${name}-be-svcplan`, {
            resourceGroupName: resourceGroupName,
            location: location,
            name: `${name}-be-svcplan`,
            kind: "app",
            sku: {
                capacity: 1,
                family: "D",
                name: "D1",
                size: "D1",
                tier: "Shared"
            }
        }, {parent: this})

        const beWebApp = new web.WebApp(`${name}-be-webapp`, {
            resourceGroupName: resourceGroupName,
            location: location,
            name: `${name}-be-webapp`,
            enabled: true,
            serverFarmId: appServicePlan.id,
            siteConfig: {
                cors: {
                    allowedOrigins: [
                             "https://pulumitask.example.com",
                            "https://stspapulumi001.z33.web.core.windows.net/",
                            
                    ]},
            },
        });

        // This tells pulumi that resource creation is complete and so will register with the stack
        this.registerOutputs({});


    }
}
