import * as pulumi from "@pulumi/pulumi";
import * as random from "@pulumi/random"
import * as aws from "@pulumi/aws";

/*
 * Module that abstracts the collection of stack-related configuration data.
 * Uses pulumi configuration mechanism currently.
 * However, could easily be augmented to also support, say, environment variables or other sources for settings.
 */

export interface ConfigData {
  nameBase: string
  vpcCidrBlock: string,
  vpcNumAvailZones: number,
  region: string
  docDbInstanceClass: string
  docDbPassword: pulumi.Output<string>
  // These are used if serving the API gateway from our zone.
  // Skipping for now
  certificateArn?: string //// FIXME Probably a resource we'll create if we go this route
  zoneId?: string //// FIXME A resource we'll create if we go this route?
  mainDomain?: string
}
export function getConfigData(): ConfigData {
  const awsConfig = new pulumi.Config("aws")
  const region = awsConfig.require("region")

  const config = new pulumi.Config();
  const nameBase = config.get("deploymentName") || `${pulumi.getProject()}-${pulumi.getStack()}`

  const vpcCidrBlock = config.get("vpcCidrBlock") || "10.0.0.0/16"
  const vpcNumAvailZones = parseInt(config.get("vpcNumAvailZones") || "2")

  const docDbInstanceClass = config.get("docDbInstanceClass") || "db.t3.medium"
  let docDbPassword = config.getSecret("docDbPassword")
  if (!docDbPassword) {
    const password = new random.RandomPassword(`${nameBase}-docDb-pwd`, {
      length: 16,
      special: true,
      overrideSpecial: " %@",
    })
    docDbPassword = password.result
  }

  return {
    nameBase: nameBase, 
    vpcCidrBlock: vpcCidrBlock, 
    vpcNumAvailZones: vpcNumAvailZones, 
    region: region,
    docDbInstanceClass: docDbInstanceClass,
    docDbPassword: docDbPassword
  }
}