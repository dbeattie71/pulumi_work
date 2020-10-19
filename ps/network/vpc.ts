import * as pulumi from '@pulumi/pulumi';
import * as aws from '@pulumi/aws';
import * as awsx from '@pulumi/awsx';

// no args in this basic use-case
interface Args {

}


export default class Vpc extends pulumi.ComponentResource {
  id: pulumi.Output<string>;
  publicSubnetIds: Promise<pulumi.Output<string>[]>;
  privateSubnetIds: Promise<pulumi.Output<string>[]>;

  constructor(
    componentName: string,
    args: Args,
    options?: pulumi.ComponentResourceOptions
  ) {
    super('Vpc', componentName, args, options);

    // build VPC with default stuff
    const vpc = new awsx.ec2.Vpc(
      `${componentName}-vpc`,
      {
        numberOfAvailabilityZones: 2,
        subnets: [
          { type: 'public', cidrMask: 20 },
          { type: 'private', cidrMask: 20 },
        ],
        tags: { "Name": `${componentName}-vpc`},
      },
      {
        parent: this,
      }
    );

    this.id = vpc.id;
    this.publicSubnetIds = vpc.publicSubnetIds;
    this.privateSubnetIds = vpc.privateSubnetIds;
  }
}
