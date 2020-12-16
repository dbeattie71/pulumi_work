import * as pulumi from "@pulumi/pulumi";
import { Input, Output } from "@pulumi/pulumi"
import * as insights from "@pulumi/azure-nextgen/insights/latest";

// These are the input properties supported by the custom resource.
// Can be anything that makes sense. Supporting location and tags in this example.
// - resourceGroupName: resource group in which to launch these resources
// - location: location for these resources. 
interface SharedElementsArgs {
    resourceGroupName: Input<string>;
    location: Input<string>;
};

export class SharedElements extends pulumi.ComponentResource {
  // The output properties for the custom resource.
  // Can be anything that makes sense. 
  // In this case, the endpoint URL is returned.
  public readonly instrumentationKey: Output<string>;
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

    const beAppInsights = new insights.Component(`${name}-app-insights`, {
        applicationType: "web",
        flowType: "Bluefield",
        kind: "web",
        location: location,
        requestSource: "rest",
        resourceGroupName: resourceGroupName,
        resourceName: `${name}-app-insights`
    }, {parent: this});

    this.registerOutputs({});

    this.instrumentationKey = beAppInsights.instrumentationKey 
  }
}
