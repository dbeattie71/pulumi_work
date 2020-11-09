 // Contrived example around using:
 // - StackReference outputs as inputs to a
 // - GET function 
 // - and then using the results of that GET function as inputs to another resource creation.


import * as pulumi from "@pulumi/pulumi";
import * as gcp from "@pulumi/gcp";
import { getBucketObject } from "@pulumi/gcp/storage";

// get stack output
const config = new pulumi.Config()
const stackName = config.require("stackName")
const baseStack = new pulumi.StackReference(stackName)
export const bucketName = baseStack.getOutput("bucketName")
export const bucketObjectName = baseStack.getOutput("bucketObjectName")

const bktObject = pulumi.all([bucketName, bucketObjectName]).apply(([name, id]) => {
  return getBucketObject({
    bucket:  name,
    name: id,
  });
});

const anotherBucketObject = new gcp.storage.BucketObject("another-mitch-object", {
  bucket: pulumi.interpolate`${bktObject.bucket}`,
  content: "This is Mitch's other bucket object"
});



