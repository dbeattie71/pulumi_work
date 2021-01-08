import * as aws from "@pulumi/aws";
import * as pulumi from "@pulumi/pulumi";
import { OutputFile } from "./output-file"
// Create an AWS resource (S3 Bucket)
const bucket = new aws.s3.Bucket("my-bucket", {
  tags: {
    project: "foo"
  }
});

// write the bucket's property
const outputFileName = new OutputFile("outputs", {
  propName: "BUCKET_ID",
  prop: bucket.id,
})
