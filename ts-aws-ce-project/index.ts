import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

import { StandardVpc } from "./vpc";


const nameBase = "ce-proj"

const config = new pulumi.Config("aws");
const reg = config.require("region") 

const vpc = new StandardVpc(`${nameBase}`, {
  
})

export const msk = new aws.msk.Cluster(`${nameBase}-msk`, {
  brokerNodeGroupInfo: {
    clientSubnets: vpc.subnets,
    ebsVolumeSize: 5,
    instanceType: "kafka.t3.small",
    securityGroups: vpc.sgs,
  },
  kafkaVersion: "2.2.1",
  numberOfBrokerNodes: 2,
  clusterName: `${nameBase}-msk`
})
