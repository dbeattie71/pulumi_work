import {Input, ComponentResourceOptions, ComponentResource} from '@pulumi/pulumi';
import * as awsx from '@pulumi/awsx';

interface Args {
  vpc: awsx.ec2.Vpc;
  //subnets: pulumi.Input<pulumi.Input<string>[]>;
  subnets: Input<Input<string>[]>;
}

export default class LoadBalancer extends ComponentResource {
  constructor(
    componentName: string,
    args: Args,
    options?: ComponentResourceOptions
  ) {
    super('LoadBalancer', componentName, args, options);
    const alb = new awsx.lb.ApplicationLoadBalancer(
      `${componentName}-lb`,
      {
        vpc: args.vpc,
        subnets: args.subnets
      },
      { parent: this }
    );
  }
}
