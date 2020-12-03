import * as pulumi from "@pulumi/pulumi";

function keyMessage(keyName: string) {
  console.log(`**** MISSING ${keyName} config ****`)
  console.log("**** Get key from DataDog console: Integrations -> APIs")
  console.log(`**** And execute the command: pulumi config set ${keyName} --secret`)
  console.log("****")
}
// Ensure the required datadog keys are configured
export function checkKeys() {
  const config = new pulumi.Config();
  const apiKey = config.get("apiKey") || "missing"
  const appKey = config.get("appKey") || "missing"
  if (apiKey == "missing") keyMessage("apiKey")
  if (appKey == "missing") keyMessage("appKey")
  return apiKey
}

