// This creates a simple Lambda function that gets the Pulumi audit logs and puts them into a DynamoDB indexed by timestamp.
// It also creates a periodic cloudwatch trigger to trigger the function.
// Ultimately it wouuld also push the data to a log aggregator.

import * as pulumi from "@pulumi/pulumi";
import { Input, Output } from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
const fetch = require("node-fetch");

// import * as awsx from "@pulumi/awsx";
// import axios from 'axios';

const projectName = pulumi.getProject();
const stackName = pulumi.getStack()
const nameBase = `${projectName}-${stackName}`

const config = new pulumi.Config();
const pulumiAccessToken = config.requireSecret("pulumi_access_token") 

interface AuditLogEntry {
    timestamp: string;
    sourceIP: string;
    event: string;
    description: string;
    user: object;
    reqStackAdmin: boolean
}

// Create DynamoDB table the audit log entries keyed by timestamp.
const logTable = new aws.dynamodb.Table(`${nameBase}-auditlog-table`, {
    attributes: [{
        name: "timestamp",
        type: "N",
    }],
    hashKey: "timestamp",
    readCapacity: 5,
    writeCapacity: 5,
});

async function storeLogs(auditEvents: AuditLogEntry[]) {
    const client = new aws.sdk.DynamoDB.DocumentClient();
    console.log("*** Length ***", auditEvents.length)
    // just grabbing the 5 most recent audit log entries to keep things manageable
    //for (let i = 0; i < auditEvents.length; i++) { 
    for (let i = 0; i < 5; i++) { 
        const event  = auditEvents[i]
        // Push the event into the table and assume success.
        const pushresult = await client.put({
            TableName: logTable.name.get(),
            Item: event
        }).promise()
    }
}

async function getAuditLogs(org: string, accessToken: string): Promise<AuditLogEntry[]> {
    // Get all audit logs
    const auditLogUrl = `https://api.pulumi.com/api/orgs/${org}/auditlogs?startTime=999999999999999999`

    const headers =  {
        'Authorization': `token ${accessToken}`,
        'content-type': 'application/json;charset=UTF-8',
    }

    const logs = await fetch(auditLogUrl, {
        method: 'GET',
        headers: headers
    })
    const auditLogs = await logs.json();
    
    return auditLogs.auditLogEvents;
}

// Lambda function that reads Pulumi audit log and stores the data in DynamoDB
// and related Cloudwatch event to run every 5 minutes.
const lambdaFunc = pulumiAccessToken.apply(token => {
    // const lambda = new aws.lambda.CallbackFunction(`${nameBase}-process-logs`, {
    //     callback: async (e) => {
    //         const auditEvents = await getAuditLogs("demo", token)
    //         await storeLogs(auditEvents)
    //     }
    // });

    const eventRuleHandler: aws.cloudwatch.EventRuleEventHandler = async (
        event: aws.cloudwatch.EventRuleEvent,
      ) => {
        const auditEvents = await getAuditLogs("demo", token)
        await storeLogs(auditEvents)
    }

    const runLogGrabber: aws.cloudwatch.EventRuleEventSubscription = aws.cloudwatch.onSchedule(
        `${nameBase}-log-event-subscription`,
        "rate(1 minute)",
        eventRuleHandler,
      );



    // // Cloudwatch Event Rule to run the lambda function every 5 minutes.
    // const logGrabberSchedule = new aws.cloudwatch.EventRule(`${nameBase}-log-schedule`, {
    //     description: "Run lambda to get audit logs.",
    //     scheduleExpression: "rate(1 minute)",
    // });

    // const goo = new aws.cloudwatch.onSchedule()

    // const logGrabberEvent = new aws.cloudwatch.EventTarget(`${nameBase}-log-runner`, {
    //     arn: lambda.arn,
    //     rule: logGrabberSchedule.name,
    // });

})




// // A handler function that will list objects in the bucket and bulk delete them
// const emptyTrash: aws.cloudwatch.EventRuleEventHandler = async (
//     event: aws.cloudwatch.EventRuleEvent
//   ) => {
//     const s3Client = new aws.sdk.S3(); //creates interface to service
//     const bucket = trashBucket.id.get();
  
//     const { Contents = [] } = await s3Client //get list of objects in bucket
//       .listObjects({ Bucket: bucket })
//       .promise();
//     const objects: ObjectIdentifier[] = Contents.map(object => {
//       return { Key: object.Key! };
//     });
  
//     await s3Client //delete objects
//       .deleteObjects({
//         Bucket: bucket,
//         Delete: { Objects: objects, Quiet: false }
//       })
//       .promise()
//       .catch(error => console.log(error));
//     console.log(
//       `Deleted ${Contents.length} item${
//         Contents.length === 1 ? "" : "s"
//       } from ${bucket}.`
//     );
//   };



// async function storeAuditLogs(dbName: string, auditLogEventss: object) {
//     const dbClient = new AWS.DynamoDB.DocumentClient();
//     // DynamoDB entry
//     let dbParams = {
//         Key: {
//             email: email, 
//         },
//         TableName: dbName,
//     }
//     console.log("GET dbParams",dbParams)

//     // get the DB entry
//     const tableItem = await dbClient.get(dbParams, function(err, data) {
//         if (err) {
//             console.log("DB GET ERROR",err);
//         } else {
//             console.log("DB GET SUCCESS", data);
//         };
//     }).promise();
//     return tableItem.Item;
// }

// // Create an API endpoint
// // Exposes a GET endpoint that runs the function to get the audit logs and push them into Dynamodb.
// const endpoint = new awsx.apigateway.API(`${nameBase}-auditlog-endpoint`, {
//     routes: [
//     {
//         path: "/ushdatage",  // ?whatever=whatever&something=something
//         method: "POST",
//         eventHandler: async (event) => {
//             const client = new aws.sdk.DynamoDB.DocumentClient();
//             let params = event.queryStringParameters || {}; // params
//             let body = event.body || ""; // Body is base64 encoded
//             let decodedBody:string = Buffer.from(body, 'base64').toString('ascii') // decode from base64 to string json
//             let jsonBody = JSON.parse(decodedBody); // convert from string formatted json to a json object that can be referenced.

//             // Get current table size and calculate the next index
//             // This is not a perfect approach since if someone deletes a table entry other than the last one we get stuck.
//             // But it's sufficient for this use-case.
//             const tableScan = await client.scan({
//                 TableName: logTable.name.get(),
//                 Select: "COUNT"
//             }).promise();
//             let nextItemNumber = (tableScan.Count ? tableScan.Count + 1 : 1)

//             // Push the next item into the table and assume success.
//             await client.put({
//                 TableName: logTable.name.get(),
//                 Item: {id: nextItemNumber, parameters: params, body: jsonBody} 
//             }).promise()
//             return {
//                 statusCode: 200,
//                 body: decodedBody,
//             }
//         }
//     },
//     {
//         path: "/showdata",  // ?whatever=whatever&something=something
//         method: "GET",
//         eventHandler: async (event) => {
//             const client = new aws.sdk.DynamoDB.DocumentClient();

//             // Get current contents and return the data.
//             const tableDump= await client.scan({
//                 TableName: logTable.name.get(),
//                 Select: "ALL_ATTRIBUTES"
//             }).promise();
//             return {
//                 statusCode: 200,
//                 body: JSON.stringify(tableDump, null, 4),
//             }
//         }
//     }]

// });

// exports.WebHookURL = pulumi.interpolate`${endpoint.url}pushdata`;
// exports.DumpLogDataURL = pulumi.interpolate`${endpoint.url}showdata`
// exports.BackendTable = logTable.name