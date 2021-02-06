import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
const AWS = require("aws-sdk");

const awsConfig = new pulumi.Config("aws");
const region = awsConfig.get("region") || "us-east-1"

const config = new pulumi.Config();
const nameBase = config.get("nameBase") || "mitch-new"
const existingApiGwId = config.require("existingApiGwId")
const existingApiGwName = config.require("existingApiGwName")

// Import an existing API gateway
const apiGw = new aws.apigatewayv2.Api(existingApiGwName, {
  name: existingApiGwName,
  protocolType: "HTTP",
}, {import: existingApiGwId})

// Build Lambda #1 which receives requests from the imported API GW
// TODO: lambda-1 component resource
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
    ".": new pulumi.asset.FileArchive("./lambda1-app"),
  }),
  runtime: "nodejs12.x",
  role: lambdaRole.arn,
  handler: "index.handler",
});

// Give API Gateway permissions to invoke the Lambda
const lambdapermission = new aws.lambda.Permission(`${nameBase}-lambdaPermission`, {
  action: "lambda:InvokeFunction",
  principal: "apigateway.amazonaws.com",
  function: lambda,
});

// Add Lambda #1 to the API GW
// Set up route
if (!pulumi.runtime.isDryRun()) {
  const apiGwConfig = pulumi.all([apiGw.id]).apply(([apiGwId]) => {
    AWS.config.update({region:region});
    const client = new aws.sdk.ApiGatewayV2();
    const params = {
      ApiId: apiGwId,
      RouteKey: "GET /",
    }
    client.getRoute
    client.createRoute(params, function(err, data) {
      if (err) console.log(err, err.stack); // an error occurred
      else     console.log(data);           // successful response
    });
  });
}
