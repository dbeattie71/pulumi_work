import * as pulumi from "@pulumi/pulumi";

import { Backend } from "./backend";
import { Bus } from "./bus"
import { Frontend } from "./frontend"

const stack = pulumi.getStack();
const config = new pulumi.Config();
const nameBase = config.get("nameBase") || stack
const appName = config.get("appName") || "custom.EventProcessor"

const backend = new Backend(nameBase)

const bus = new Bus(nameBase, {reader: backend.reader, appName: appName})

const frontend = bus.arn.apply(arn => new Frontend(nameBase, {busArn: arn, appName: appName}))

// The URL to hit to cause events
export const apiUrl = frontend.url

// This part is just to make it easy to get to the backend table to test end-to-end
const awsConfig = new pulumi.Config("aws");
const region = awsConfig.require("region");
export const EventsTableLink = pulumi.interpolate`https://console.aws.amazon.com/dynamodbv2/home?region=${region}#table?name=${backend.eventsTableName}`