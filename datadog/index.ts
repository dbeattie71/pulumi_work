import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import * as awsx from "@pulumi/awsx";
import * as datadog from "@pulumi/datadog";
import {checkKeys, ddogWorthy} from "./config";
import {setupDatadog} from "./datadog";

const apiKey = checkKeys();
const dDoggy = ddogWorthy();

const nameBase = "ddog-demo"
const vpcCidr = "10.0.0.0/16"
const vpcName = nameBase+"-vpc"
const sgName = nameBase+"-sg"
const vpc = new awsx.ec2.Vpc(vpcName, {
    cidrBlock : vpcCidr,
    subnets: [ 
        {type: "public"},
    ],
    numberOfNatGateways: 0, 
    tags: { "Name": vpcName}
});
const instanceNet = pulumi.output(vpc.publicSubnetIds.then(ids => ids[0])) 

// Allocate a security group and some access rules 
const sg = new awsx.ec2.SecurityGroup(sgName, { vpc: vpc});
// Inbound HTTP traffic on port 80 from anywhere
sg.createIngressRule("http-access", {
    location: new awsx.ec2.AnyIPv4Location(),
    ports: new awsx.ec2.TcpPorts(80),
    description: "allow HTTP access from anywhere",
});
sg.createIngressRule("ssh-access", {
    location: new awsx.ec2.AnyIPv4Location(),
    ports: new awsx.ec2.TcpPorts(22),
    description: "allow ssh access from anywhere",
})
// Outbound TCP traffic on any port to anywhere
sg.createEgressRule("outbound-access", {
    location: new awsx.ec2.AnyIPv4Location(),
    ports: new awsx.ec2.AllTcpPorts(),
    description: "allow outbound access to anywhere",
});

// Some userdata to install Datadog agent if ddogWorthy
let userData = pulumi.interpolate``
if (dDoggy) {
    userData = pulumi.interpolate `#!/bin/bash
export DD_API_KEY=${apiKey}
export DD_AGENT_MAJOR_VERSION=7 
bash -c "$(curl -L https://raw.githubusercontent.com/DataDog/datadog-agent/master/cmd/agent/install_script.sh)"`
}

// Launch the instances of various types and counts.
const ubuntu_ami = aws.getAmi({
    filters: [
        { name: "name", values: ["ubuntu/images/*/ubuntu-bionic-*-amd64-server-*"]},
        { name: "root-device-type", values: ["ebs"] },
    ],
    owners: ["099720109477"], // canonical
    mostRecent: true,
}, { async: true }).then(result => result.id);

// Build the instance
const vmName = nameBase + "-server"
const instance = new aws.ec2.Instance(vmName, {
    ami: ubuntu_ami,
    instanceType: "t3.small",
    associatePublicIpAddress: true,
    subnetId: instanceNet,
    vpcSecurityGroupIds: [sg.id],
    userData: userData,
    tags: {
        "Name": vmName,
    },
    keyName: "mitch-ssh-key"
});

if (dDoggy) {
    const ddogSetup = instance.id.apply(hostId => {
        const target = {
            "hostName": vmName,
            "hostId": hostId,
        }
        setupDatadog(target);
    })
}

export const instanceId = instance.id
export const instanceIp = instance.publicIp
