import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws"

interface StandardVpcArgs {
  vpcCidr?: pulumi.Input<string>;
  provider?: pulumi.ProviderResource;
  tags?: aws.Tags;
};

export class StandardVpc extends pulumi.ComponentResource {
  public readonly vpc: aws.ec2.Vpc;
  public readonly subnets: pulumi.Output<string>[];

  constructor(name: string, args: StandardVpcArgs, opts?: pulumi.ComponentResourceOptions) {
    super("custom:x:StandardVpc", name, args, opts);
    
    const cidrBlock = args.vpcCidr || "10.0.0.0/24"
    const tags = args.tags || {}

    let provider = args.provider
    if (!provider) {
       provider = this.getProvider("::aws")
    }

    this.vpc = new aws.ec2.Vpc(`${name}-vpc`, {
      cidrBlock: cidrBlock,
      enableDnsHostnames: true,
      tags: { ...args.tags },
    }, { parent: this, provider: provider })

    const igw = new aws.ec2.InternetGateway(`${name}-igw`, {
      vpcId: this.vpc.id,
      tags: { ...args.tags },
    }, { parent: this.vpc, provider: provider })

    const rt = new aws.ec2.RouteTable(`${name}-pub-rt`, {
      vpcId: this.vpc.id,
      tags: { ...args.tags },
    }, { parent: this.vpc, provider: provider });
    const pubroute = new aws.ec2.Route(`${name}-public-route`, {
      routeTableId: rt.id,
      destinationCidrBlock: "0.0.0.0/0",
      gatewayId: igw.id,
    }, { parent: rt, provider: provider });

    const azs = aws.getAvailabilityZones({
      state: "available",
    })
    

    azs.array.forEach(az => {
      
    const az1_subnet = new aws.ec2.Subnet(`${name}-az1snet`, {
      cidrBlock: cidrBlock,
      vpcId: this.vpc.id,
      availabilityZone: `${args.region}a`,
      tags: { ...args.tags },
    }, { parent: this.vpc })
    const az2_subnet = new aws.ec2.Subnet(`${name}-az2snet`, {
      cidrBlock: cidrBlock,
      vpcId: this.vpc.id,
      availabilityZone: `${args.region}b`,
      tags: { ...args.tags },
    }, { parent: this.vpc })
    this.subnets = [az1_subnet.id, az2_subnet.id ]
    });
  }
}