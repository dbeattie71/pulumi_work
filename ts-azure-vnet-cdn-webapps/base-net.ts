import * as pulumi from "@pulumi/pulumi";
import { Input } from "@pulumi/pulumi"
import * as network from "@pulumi/azure-nextgen/network/latest";
import * as resources from "@pulumi/azure-nextgen/resources/latest";

// These are the input properties supported by the custom resource.
// Can be anything that makes sense. Supporting location and tags in this example.
// - location: azure location in which to create the resources
// - cidrBlock: main block for the network.
// - subnetCidrBlocks: an array of subnet CIDR blocks within the main block.
// - tags: optional tags to add to resources
interface BaseNetArgs {
    location: Input<string>;
    cidrBlock: Input<string>;
    subnetCidrBlocks: Input<string>[];
    tags?: pulumi.Input <{
        [key: string]: pulumi.Input<string>;
    }>;
};

export class BaseNet extends pulumi.ComponentResource {
    // The output properties for the custom resource.
    // Can be anything that makes sense. 
    // In this case, the resourceGroup is needed in the calling program.
    // The network and subnets are just included for examples but not used in the calling program at this time.
    public readonly resourceGroup: resources.ResourceGroup;
    public readonly network: network.VirtualNetwork;
    public readonly subnets: network.Subnet[];

    // Standard constructor declaration 
    // - name: this is standard resource declaration name. In the case of this custom resource, it is also used as a basis for the resource names.
    // - args: the input properties for the custom resource as declared in the Interface above.
    // - opts: supports standard Pulumi resource options (e.g. the protect flag or the dependsOn flag).
    constructor(name: string, args: BaseNetArgs, opts?: pulumi.ComponentResourceOptions) {
        // MUST HAVE this super() call to register the custom resource.
        // You'll see this string in the pulumi up
        super("custom:x:BaseNet", name, args, opts);

        // Deploy the resource group.
        this.resourceGroup = new resources.ResourceGroup(`${name}-rg`, {
            resourceGroupName: pulumi.interpolate`${name}-rg`,
            location: args.location,
        }, {parent: this, });

        // Creates a Virtual Network
        this.network = new network.VirtualNetwork(`${name}-vnet`, {
            resourceGroupName: this.resourceGroup.name,
            location: args.location,
            virtualNetworkName:`${name}-vnet`,
            addressSpace: { addressPrefixes: [args.cidrBlock]},
        }, {parent: this, ignoreChanges:["tags"] }); // This is because we hit this error: Custom diff for VirtualNetwork https://github.com/pulumi/pulumi-azure-nextgen-provider/issues/74

        // Create subnets
        this.subnets = [];
        for (let i = 0; i < (args.subnetCidrBlocks?.length ?? 0); i++) {
            const subnet = new network.Subnet(`${name}-subnet-${i}`, {
                resourceGroupName: this.resourceGroup.name,
                virtualNetworkName: this.network.name,
                subnetName: `${name}-subnet-${i}`,
                addressPrefix: args.subnetCidrBlocks[i],
            }, { parent: this.network, });
             this.subnets.push(subnet);
        }

        // This tells pulumi that resource creation is complete and so will register with the stack
        this.registerOutputs({});
    }
}
