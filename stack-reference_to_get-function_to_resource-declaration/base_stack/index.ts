import * as pulumi from "@pulumi/pulumi";
import * as gcp from "@pulumi/gcp";

const baseName = "mitch"
// Create a GCP resource (Storage Bucket)
const bucket = new gcp.storage.Bucket(`${baseName}-bucket`);

// Export the DNS name of the bucket
export const bucketName = bucket.name;

// Create and export a bucket object
const bucketObject = new gcp.storage.BucketObject(`${baseName}-object`, {
  bucket: bucketName,
  content: "This is Mitch's bucket object"
})
export const bucketObjectName = bucketObject.name
