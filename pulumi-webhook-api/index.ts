// Copyright 2016-2019, Pulumi Corporation.  All rights reserved.

import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import * as awsx from "@pulumi/awsx";

export const projectName = pulumi.getProject();
export const stackName = pulumi.getStack()
const nameBase = `${projectName}-${stackName}`

// Create DynamoDB table to store the data from the API.
const counterTable = new aws.dynamodb.Table(`${nameBase}-webhook-table`, {
    attributes: [{
        name: "id",
        type: "N",
    }],
    hashKey: "id",
    readCapacity: 5,
    writeCapacity: 5,
});

// Create an API endpoint
// Only bothering with a POST since that's what's used by Pulumi Webhooks
// You can also optionally pass query parameters - you can use any names or values.
// This is supported in case someone wants to see it with query parameters.
// This API simply stores the payload and any query parameters in the dynamodb table.
const endpoint = new awsx.apigateway.API(`${nameBase}-webhook-endpoint`, {
    routes: [{
        path: "/activity",  // ?whatever=whatever&something=something
        method: "POST",
        eventHandler: async (event) => {
            const client = new aws.sdk.DynamoDB.DocumentClient();
            let params = event.queryStringParameters || {}; // params
            let body = event.body || ""; // Body is base64 encoded
            let decodedBody:string = Buffer.from(body, 'base64').toString('ascii') // decode from base64 to string json
            let jsonBody = JSON.parse(decodedBody); // convert from string formatted json to a json object that can be referenced.
            const tableScan = await client.scan({
                TableName: counterTable.name.get(),
                Select: "COUNT"
            }).promise();
            let nextItemNumber = 1
            if (tableScan.Count) {
                nextItemNumber = tableScan.Count + 1
            } 
            await client.put({
                TableName: counterTable.name.get(),
                Item: {id: nextItemNumber, parameters: params, body: jsonBody} 
            }).promise()
            return {
                statusCode: 200,
                body: decodedBody,
            }
        }
    }]


    //     path: "/{route+}",
    //     method: "GET",
    //     eventHandler: async (event) => {
    //         const route = event.pathParameters!["route"];
    //         console.log(`Getting count for '${route}'`);

    //         const client = new aws.sdk.DynamoDB.DocumentClient();

    //         // get previous value and increment
    //         // reference outer `counterTable` object
    //         const tableData = await client.get({
    //             TableName: counterTable.name.get(),
    //             Key: { id: route },
    //             ConsistentRead: true,
    //         }).promise();

    //         const value = tableData.Item;
    //         let count = (value && value.count) || 0;

    //         await client.put({
    //             TableName: counterTable.name.get(),
    //             Item: { id: route, count: ++count },
    //         }).promise();

    //         console.log(`Got count ${count} for '${route}'`);
    //         return {
    //             statusCode: 200,
    //             body: JSON.stringify({ route, count }),
    //         };
    //     },
    // }],
});

exports.endpoint = endpoint.url;
