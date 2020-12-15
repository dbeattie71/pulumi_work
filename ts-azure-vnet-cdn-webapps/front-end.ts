import * as pulumi from "@pulumi/pulumi";
import { Input, Output } from "@pulumi/pulumi"
import * as storage from "@pulumi/azure/storage";
import * as cdn from "@pulumi/azure-nextgen/cdn/latest";

// These are the input properties supported by the custom resource.
// Can be anything that makes sense. Supporting location and tags in this example.
// - resourceGroupName: resource group in which to launch these resources
// - location: location for these resources. 
interface FrontEndArgs {
    resourceGroupName: Input<string>;
    location: Input<string>;
};

export class FrontEnd extends pulumi.ComponentResource {
    // The output properties for the custom resource.
    // Can be anything that makes sense. 
    // In this case, the endpoint URL is returned.
    public readonly url: Output<string>;
    //private readonly sa: storage.Account;


    // Standard constructor declaration 
    // - name: this is standard resource declaration name. In the case of this custom resource, it is also used as a basis for the resource names.
    // - args: the input properties for the custom resource as declared in the Interface above.
    // - opts: supports standard Pulumi resource options (e.g. the protect flag or the dependsOn flag).
    constructor(name: string, args: FrontEndArgs, opts?: pulumi.ComponentResourceOptions) {
        // MUST HAVE this super() call to register the custom resource.
        // You'll see this string in the pulumi up
        super("custom:x:FrontEnd", name, args, opts);

        // SPA storage account
        const sa = new storage.Account(`${name}spasa`, {
            resourceGroupName: args.resourceGroupName,
            location: args.location,
            accountTier: "Standard",
            accountReplicationType: "GRS",
            staticWebsite: {
                indexDocument: "index.html",
                error404Document: "index.html",
            },
            /*tags: {
                environment: "Dev",
            },*/
        }, {parent: this })

        //// FOR TESTING PURPOSES ////
        // Putting a file up in Blob for the "SPA" so there is something to test with and validate WAF/CDN/ENDPOINT stuff is working.
        const fakeSpa = new storage.Blob("index.html", {
            name: "index.html",
            storageAccountName: sa.name,
            storageContainerName: "$web", 
            type: "Block",
            sourceContent: "This is a place holder for a Single Page App",
            contentType: "text/html"
        }, {parent: this })

        // CDN, WAF, and Endpoint
        const cdnProfile = new cdn.Profile(`${name}-spa-cdn-profile`, {
            resourceGroupName: args.resourceGroupName,
            location: "global",
            profileName: `${name}-spa-cdn-profile`,
            sku: {
                name: "Standard_Microsoft",
            },
        }, {parent: this });

        // Example WAF Setup - should be customized accordingly
        const cdnWafRules = new cdn.Policy(`${name}spawafrules`, {
            policyName: `${name}spawafrules`,
            // example using managed rules
            managedRules: {
                managedRuleSets: [{
                    ruleSetType: "DefaultRuleSet",
                    ruleSetVersion: "1.0",
                }],
            },
            // example using custom rules
            customRules: {
                rules: [
                    {
                        action: "Block",
                        enabledState: "Enabled",
                        matchConditions: [{
                            matchValue: [
                                "US",
                                "MX",
                                "CA",
                            ],
                            matchVariable: "RemoteAddr",
                            negateCondition: true,
                            operator: "GeoMatch",
                        }],
                        name: "BlockOutsideNorthAmerica",
                        priority: 10,
                    },
                    {
                        action: "Allow",
                        enabledState: "Enabled",
                        matchConditions: [{
                            matchValue: ["/login"],
                            matchVariable: "RequestUri",
                            negateCondition: false,
                            operator: "Contains",
                        }],
                        name: "AllowUnauthenticatedLogin",
                        priority: 30,
                    },
                ],
            },
            location: cdnProfile.location,
            resourceGroupName: args.resourceGroupName,
            sku: cdnProfile.sku
        }, {parent: this});

        // Endpoint
        const endpoint = new cdn.Endpoint(`${name}-spa-endpoint`, {
            resourceGroupName: args.resourceGroupName,
            location: cdnProfile.location,
            profileName: cdnProfile.name,
            webApplicationFirewallPolicyLink: { id: cdnWafRules.id},
            endpointName: `${name}-spa-endpoint`,
            isHttpAllowed: false,
            isHttpsAllowed: true,
            originHostHeader: sa.primaryWebHost,
            origins: [{
                name: "blobstorage",
                hostName: sa.primaryWebHost,
            }],
            contentTypesToCompress: ['text/html', 'application/octet-stream'],
            deliveryPolicy: {
                rules: [
                    {
                        actions: [
                            {
                                name: "ModifyResponseHeader",
                                parameters: {
                                    odataType:  "#Microsoft.Azure.Cdn.Models.DeliveryRuleHeaderActionParameters",
                                    headerAction: "Append",
                                    headerName: "X-Frame-Options",
                                    value: "DENY",
                                },
                            },
                            {
                                name: "ModifyResponseHeader",
                                parameters: {
                                    odataType:  "#Microsoft.Azure.Cdn.Models.DeliveryRuleHeaderActionParameters",
                                    headerAction: "Append",
                                    headerName: "cache-control",
                                    value: "no-store",
                                },
                            },
                            {
                                name: "ModifyResponseHeader",
                                parameters: {
                                    odataType:  "#Microsoft.Azure.Cdn.Models.DeliveryRuleHeaderActionParameters",
                                    headerAction: "Append",
                                    headerName: "Content-Security-Policy",
                                    value: "frame-ancestors 'none'",
                                },
                            },
                        ],
                        conditions: [],
                        name: "Global",
                        order: 0,
                    },
                    {
                        actions: [{
                            name: "UrlRewrite",
                            parameters: {
                                odataType:  "#Microsoft.Azure.Cdn.Models.DeliveryRuleUrlRewriteActionParameters",
                                destination: "/index.html",
                                preserveUnmatchedPath: false,
                                sourcePattern: "/",
                            },
                        }],
                        conditions: [{
                            name: "UrlFileExtension",
                            parameters: {
                                odataType:  "#Microsoft.Azure.Cdn.Models.DeliveryRuleUrlFileExtensionMatchConditionParameters",
                                matchValues: ["0"],
                                negateCondition: false,
                                operator: "LessThanOrEqual",
                                //transforms: [],
                            },
                        }],
                        name: "ToIndex",
                        order: 1,
                    },
                    {
                        actions: [
                            {
                                name: "CacheExpiration",
                                parameters: {
                                    odataType:  "#Microsoft.Azure.Cdn.Models.DeliveryRuleCacheExpirationActionParameters",
                                    cacheBehavior: "BypassCache",
                                    cacheType: "All",
                                },
                            },
                            {
                                name: "ModifyResponseHeader",
                                parameters: {
                                    odataType:  "#Microsoft.Azure.Cdn.Models.DeliveryRuleHeaderActionParameters",
                                    headerAction: "Overwrite",
                                    headerName: "Strict-Transport-Security",
                                    value: "max-age=31536000; includeSubDomains; preload",
                                },
                            },
                            {
                                name: "ModifyResponseHeader",
                                parameters: {
                                    odataType:  "#Microsoft.Azure.Cdn.Models.DeliveryRuleHeaderActionParameters",
                                    headerAction: "Overwrite",
                                    headerName: "X-XSS-Protection",
                                    value: "�1; mode=block�",
                                },
                            },
                        ],
                        conditions: [{
                            name: "UrlPath",
                            parameters: {
                                odataType:  "#Microsoft.Azure.Cdn.Models.DeliveryRuleUrlPathMatchConditionParameters",
                                //matchValues: [],
                                negateCondition: false,
                                operator: "Any",
                                //transforms: [],
                            },
                        }],
                        name: "bypasscache",
                        order: 2,
                    },
                    {
                        actions: [{
                            name: "UrlRedirect",
                            parameters: {
                                odataType:  "#Microsoft.Azure.Cdn.Models.DeliveryRuleUrlRedirectActionParameters",
                                destinationProtocol: "Https",
                                redirectType: "Found",
                            },
                        }],
                        conditions: [{
                            name: "RequestScheme",
                            parameters: {
                                odataType:  "#Microsoft.Azure.Cdn.Models.DeliveryRuleRequestSchemeConditionParameters",
                                matchValues: ["HTTP"],
                                negateCondition: false,
                                operator: "Equal",
                            },
                        }],
                        name: "EnforceHTTPS",
                        order: 3,
                    },
                    {
                        actions: [{
                            name: "ModifyResponseHeader",
                            parameters: {
                                odataType:  "#Microsoft.Azure.Cdn.Models.DeliveryRuleHeaderActionParameters",
                                headerAction: "Overwrite",
                                headerName: "X-Content-Type-Options",
                                value: "nosniff",
                            },
                        }],
                        conditions: [{
                            name: "RequestScheme",
                            parameters: {
                                odataType:  "#Microsoft.Azure.Cdn.Models.DeliveryRuleRequestSchemeConditionParameters",
                                matchValues: ["HTTPS"],
                                negateCondition: false,
                                operator: "Equal",
                            },
                        }],
                        name: "HeaderModifications",
                        order: 4,
                    },
                ],
            },
        }, {parent: this });

        // This tells pulumi that resource creation is complete and so will register with the stack
        this.registerOutputs({});

        this.url= pulumi.interpolate`https://${endpoint.hostName}/`;

    }
}
