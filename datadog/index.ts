import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import * as awsx from "@pulumi/awsx";
import * as datadog from "@pulumi/datadog";
import {checkKeys} from "./config";

const apiKey = checkKeys();

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

// Some userdata to install Datadog agent
const userData = pulumi.interpolate `#!/bin/bash
export DD_API_KEY=${apiKey}
export DD_AGENT_MAJOR_VERSION=7 
bash -c "$(curl -L https://raw.githubusercontent.com/DataDog/datadog-agent/master/cmd/agent/install_script.sh)"`

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

const ddogMonitor = instance.id.apply(hostId => {
    // Create Datadog Monitor for the Instance just created
    const ddogMonitor = new datadog.Monitor(nameBase+"-monitor", {
        name: vmName+"-cpu",
        message: vmName+"-cpu Monitor",
        type: "metric alert",
        query: "avg(last_1m):avg:datadog.trace_agent.cpu_percent{host:"+hostId+"} > 10"
    })

    const ddogDashboard = new datadog.Dashboard(nameBase+"-dashboard", {
        layoutType: "ordered",
        title: "Pulumi Created Dashboard",
        widgets: [
            {
                alertValueDefinition: {
                "alertId": ddogMonitor.id,
                "title": ddogMonitor.name,
                "titleSize": "16",
                "titleAlign": "left",
                "unit": "auto",
                "textAlign": "left",
                "precision": 2
                },
            },
            {
                timeseriesDefinition: {
                "title": "Avg of CPU Utilization over host:"+hostId,
                "titleSize": "16",
                "titleAlign": "left",
                "showLegend": false,
                "time": {},
                "requests": [
                  {
                    "q": "avg:system.cpu.user{host:"+hostId+"}",
                    "style": {
                      "palette": "dog_classic",
                      "lineType": "solid",
                      "lineWidth": "normal"
                    },
                    "displayType": "line"
                  }
                ],
                "yaxis": {
                  "scale": "linear",
                  "label": "",
                  "includeZero": true,
                  "min": "auto",
                  "max": "auto"
                },
                "markers": []
              }
            }
        ]
    })
})

export const test = pulumi.output(datadog.getDashboard({
    name: "Mitch Test",
}, { async: true }));


export const instanceId = instance.id
export const instanceIp = instance.publicIp

