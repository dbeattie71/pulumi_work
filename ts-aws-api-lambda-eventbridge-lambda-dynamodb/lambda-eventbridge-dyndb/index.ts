import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

const stack = pulumi.getStack();
const project = pulumi.getProject();

const config = new pulumi.Config();
const nameBase = config.get("nameBase") || "mitch-new"
const existingApiGwId = config.require("existingApiGwId")
const existingApiGwName = config.require("existingApiGwName")

const eventSource = `custom.mitchApp`

////// BUILD THE LAMBDA THAT WILL SERVICE THE EVENT BUS //////
// Build Lambda #2 which receives requests from the Event Bus
const lambda2Role = new aws.iam.Role(`${nameBase}-lambda2role`, {
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

// Attach policies to the Lambda role created above
const lambda2RoleAttachmentLambdaExecution = new aws.iam.RolePolicyAttachment(`${nameBase}-lambda2RoleLambdaExecution`, {
  role: lambda2Role,
  policyArn: aws.iam.ManagedPolicy.AWSLambdaBasicExecutionRole,
});
// const lambda2RoleAttachmentEventBus = new aws.iam.RolePolicyAttachment(`${nameBase}-lambda2RoleEventBus`, {
//   role: lambda2Role,
//   policyArn: "arn:aws:iam::aws:policy/AmazonEventBridgeFullAccess"
// });

// Create the Lambda to execute
const lambda2 = new aws.lambda.Function(`${nameBase}-lambda2Function`, {
    code: new pulumi.asset.AssetArchive({
      ".": new pulumi.asset.FileArchive("./lambda2-app"),
    }),
    runtime: "nodejs12.x",
    role: lambda2Role.arn,
    handler: "index.handler",
  });



/////// BUILD THE EVENTBRIDGE BUS AND RELATED BITS /////
const eventBus = new aws.cloudwatch.EventBus(`${nameBase}-eventBus`, {}, {dependsOn: lambda2});

const eventRule = new aws.cloudwatch.EventRule(`${nameBase}-eventRule`, {
  eventBusName: eventBus.name,
  description: "Process events",
  eventPattern: `{
  "source": [
    "${eventSource}"
  ]
}
`,
});
// const eventTarget = new aws.cloudwatch.EventTarget(`${nameBase}-eventTarget`, {
//     rule: eventRule.name,
//     arn: lambda2.arn
//     //eventBusName: eventBus.name
// });

// const eventPermission = new aws.cloudwatch.EventPermission(`${nameBase}-eventPermission`, {
//   principal: "123456789012",
//   statementId: "DevAccountAccess",
// });


/////// API GATEWAY -> LAMBDA PLUMBING
// Find existing API gateway
const apiGw = aws.apigatewayv2.Api.get(existingApiGwName, existingApiGwId)

// Build Lambda #1 which receives requests from the imported API GW
const lambda1Role = new aws.iam.Role(`${nameBase}-lambda1role`, {
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

// Attach policies to the Lambda role created above
const lambda1RoleAttachmentLambdaExecution = new aws.iam.RolePolicyAttachment(`${nameBase}-lambda1RoleLambdaExecution`, {
  role: lambda1Role,
  policyArn: aws.iam.ManagedPolicy.AWSLambdaBasicExecutionRole,
});
const lambda1RoleAttachmentEventBus = new aws.iam.RolePolicyAttachment(`${nameBase}-lambda1RoleEventBus`, {
  role: lambda1Role,
  policyArn: "arn:aws:iam::aws:policy/AmazonEventBridgeFullAccess"
});

// Create the Lambda to execute
const lambda1 = eventBus.arn.apply(arn =>  {
  return new aws.lambda.Function(`${nameBase}-lambda1Function`, {
    code: new pulumi.asset.AssetArchive({
      "infra_info.js": new pulumi.asset.StringAsset(`module.exports.infraInfo=
        {
          eventBusName: "${arn}",
          eventSource: "${eventSource}"
        }
      `),
      ".": new pulumi.asset.FileArchive("./lambda1-app"),
    }),
    runtime: "nodejs12.x",
    role: lambda1Role.arn,
    handler: "index.handler",
  });
});

// Give API Gateway permissions to invoke the Lambda
const lambda1Permission = new aws.lambda.Permission(`${nameBase}-lambda1Permission`, {
  action: "lambda:InvokeFunction",
  principal: "apigateway.amazonaws.com",
  function: lambda1,
  sourceArn: pulumi.interpolate`${apiGw.executionArn}/*/*`,
});

const lambda1Integration = new aws.apigatewayv2.Integration(`${nameBase}-lambda1Integration`, {
  apiId: apiGw.id,
  integrationType: "AWS_PROXY",
  integrationUri: lambda1.arn,
  integrationMethod: "POST",
  payloadFormatVersion: "2.0",
  passthroughBehavior: "WHEN_NO_MATCH",
});

const lambda1Route = new aws.apigatewayv2.Route(`${nameBase}-lambda1Route`, {
  apiId: apiGw.id,
  routeKey: "GET /demo",
  target: pulumi.interpolate`integrations/${lambda1Integration.id}`,
});

const stage = new aws.apigatewayv2.Stage(`${nameBase}-apiStage`, {
  apiId: apiGw.id,
  name: stack,
  routeSettings: [
    {
      routeKey: lambda1Route.routeKey,
      throttlingBurstLimit: 5000,
      throttlingRateLimit: 10000,
    },
  ],
  autoDeploy: true,
});
///// END OF API GATEWAY -> LAMBDA 1 PLUMBING




export const apiUrl = pulumi.interpolate`${stage.invokeUrl}/demo`