import * as pulumi from "@pulumi/pulumi";
import * as datadog from "@pulumi/datadog";
import {checkKeys} from "./config";

checkKeys();

export const test = pulumi.output(datadog.getDashboardList({
    name: "Test List"
}, { async: true }));