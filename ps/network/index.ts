import * as pulumi from '@pulumi/pulumi';
import Vpc from './vpc';

// basic call to vpc module and exporting what it exports

const config = new pulumi.Config();
const name = config.require('namebase')

const vpc = new Vpc(name, {
});

export { vpc };
