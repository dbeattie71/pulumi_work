import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

const stack = pulumi.getStack();
const project = pulumi.getProject();

const config = new pulumi.Config();
const nameBase = config.get("nameBase") || "mitch-new"
const existingApiGwId = config.require("existingApiGwId")
const existingApiGwName = config.require("existingApiGwName")
const eventBridgeName = config.get("eventBridgeName") || `${project}-${stack}`


/////// API GATEWAY -> LAMBDA PLUMBING
// Find existing API gateway
const apiGw = aws.apigatewayv2.Api.get(existingApiGwName, existingApiGwId)

// Build Lambda #1 which receives requests from the imported API GW
const lambdaRole = new aws.iam.Role(`${nameBase}-lambdarole`, {
  assumeRolePolicy: {
    Version: "2012-10-17",
    Statement: [
      {
        Action: "sts:AssumeRole",
        Principal: {
          Service: "lambda.amazonaws.com",
        },
        Effect: "Allow",
        Sid: "",
      },
    ],
  },
});

// Attach the fullaccess policy to the Lambda role created above
const rolepolicyattachment = new aws.iam.RolePolicyAttachment(`${nameBase}-lambdaRoleAttachment`, {
  role: lambdaRole,
  policyArn: aws.iam.ManagedPolicy.AWSLambdaBasicExecutionRole,
});

// Create the Lambda to execute
const lambda = new aws.lambda.Function(`${nameBase}-lambdaFunction`, {
  code: new pulumi.asset.AssetArchive({
    "infra_info.js": new pulumi.asset.StringAsset(`module.exports.params={eventBridgeName: "${eventBridgeName}"}`),
    ".": new pulumi.asset.FileArchive("./lambda1-app"),
  }),
  runtime: "nodejs12.x",
  role: lambdaRole.arn,
  handler: "index.handler",
});

// Give API Gateway permissions to invoke the Lambda
const lambdaPermission = new aws.lambda.Permission(`${nameBase}-lambdaPermission`, {
  action: "lambda:InvokeFunction",
  principal: "apigateway.amazonaws.com",
  function: lambda,
  sourceArn: pulumi.interpolate`${apiGw.executionArn}/*/*`,
});

const integration = new aws.apigatewayv2.Integration(`${nameBase}-lambdaIntegration`, {
  apiId: apiGw.id,
  integrationType: "AWS_PROXY",
  integrationUri: lambda.arn,
  integrationMethod: "POST",
  payloadFormatVersion: "2.0",
  passthroughBehavior: "WHEN_NO_MATCH",
});

const route = new aws.apigatewayv2.Route(`${nameBase}-apiRoute`, {
  apiId: apiGw.id,
  routeKey: "GET /demo",
  target: pulumi.interpolate`integrations/${integration.id}`,
});

const stage = new aws.apigatewayv2.Stage(`${nameBase}-apiStage`, {
  apiId: apiGw.id,
  name: stack,
  routeSettings: [
    {
      routeKey: route.routeKey,
      throttlingBurstLimit: 5000,
      throttlingRateLimit: 10000,
    },
  ],
  autoDeploy: true,
});
///// END OF API GATEWAY -> LAMBDA 1 PLUMBING

///// EVENT BRIDGE SET UP


export const apiUrl = pulumi.interpolate`${stage.invokeUrl}/demo`