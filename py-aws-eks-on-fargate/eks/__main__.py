import pulumi
from pulumi import (
    ResourceOptions,
    Output
)

# import pulumi_aws as aws
# from pulumi_aws.iam import (
#     GetPolicyDocumentStatementArgs,
#     GetPolicyDocumentStatementConditionArgs,
#     GetPolicyDocumentStatementPrincipalArgs
# )

from pulumi_eks import Cluster

import pulumi_kubernetes as kubernetes
from pulumi_kubernetes import Provider
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.core.v1 import (
    ContainerArgs,
    Namespace,
    PodSpecArgs,
    PodTemplateSpecArgs,
    Service,
    ServiceAccount,
    ServicePortArgs,
    ServiceSpecArgs,
)
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs
from pulumi_kubernetes.extensions.v1beta1 import (
    Ingress,
    IngressSpecArgs,
    IngressRuleArgs,
    HTTPIngressRuleValueArgs,
    HTTPIngressPathArgs,
    IngressBackendArgs,
)

import network
import json

proj_name = pulumi.get_project()

# Create VPC and public and private subnets
# network=network.Vpc(f'{proj_name}-net', network.VpcArgs())
# pulumi.export("priv subnets", network.private_subnet_ids)
# pulumi.export("pub subnets", network.public_subnet_ids)

vpc_id = "vpc-08cc8cd01a18e129b"
private_subnet_ids = [
        "subnet-0747d87f8a246fbf5",
        "subnet-0cf998306d4d6f9b0"
]

### CLUSTER ####
# Create an EKS cluster on Fargate.
cluster = Cluster(
    f"{proj_name}-eks",
    fargate=True,
    vpc_id=vpc_id,
    subnet_ids=private_subnet_ids,
    create_oidc_provider=True,
)
# Export the cluster's kubeconfig.
pulumi.export("kubeconfig", cluster.kubeconfig)

# ns = Namespace(f"{proj_name}-ns", 
#   opts=ResourceOptions(provider=cluster.provider)
# ).metadata.name
# # Export the Namespace name
# pulumi.export("name_space", ns)

# Createa k8s provider based on kubeconfig from EKS cluster
k8s_provider = Provider(
    "k8s", kubeconfig=cluster.kubeconfig,
)

alb_iam_policy = f"{proj_name}-alb-iam"
alb_ingress_controller_iam_policy_policy = aws.iam.Policy(alb_iam_policy,
    name=alb_iam_policy,
    policy="""{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "acm:DescribeCertificate",
        "acm:ListCertificates",
        "acm:GetCertificate"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:CreateSecurityGroup",
        "ec2:CreateTags",
        "ec2:DeleteTags",
        "ec2:DeleteSecurityGroup",
        "ec2:DescribeAccountAttributes",
        "ec2:DescribeAddresses",
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceStatus",
        "ec2:DescribeInternetGateways",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeTags",
        "ec2:DescribeVpcs",
        "ec2:ModifyInstanceAttribute",
        "ec2:ModifyNetworkInterfaceAttribute",
        "ec2:RevokeSecurityGroupIngress"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:AddListenerCertificates",
        "elasticloadbalancing:AddTags",
        "elasticloadbalancing:CreateListener",
        "elasticloadbalancing:CreateLoadBalancer",
        "elasticloadbalancing:CreateRule",
        "elasticloadbalancing:CreateTargetGroup",
        "elasticloadbalancing:DeleteListener",
        "elasticloadbalancing:DeleteLoadBalancer",
        "elasticloadbalancing:DeleteRule",
        "elasticloadbalancing:DeleteTargetGroup",
        "elasticloadbalancing:DeregisterTargets",
        "elasticloadbalancing:DescribeListenerCertificates",
        "elasticloadbalancing:DescribeListeners",
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:DescribeLoadBalancerAttributes",
        "elasticloadbalancing:DescribeRules",
        "elasticloadbalancing:DescribeSSLPolicies",
        "elasticloadbalancing:DescribeTags",
        "elasticloadbalancing:DescribeTargetGroups",
        "elasticloadbalancing:DescribeTargetGroupAttributes",
        "elasticloadbalancing:DescribeTargetHealth",
        "elasticloadbalancing:ModifyListener",
        "elasticloadbalancing:ModifyLoadBalancerAttributes",
        "elasticloadbalancing:ModifyRule",
        "elasticloadbalancing:ModifyTargetGroup",
        "elasticloadbalancing:ModifyTargetGroupAttributes",
        "elasticloadbalancing:RegisterTargets",
        "elasticloadbalancing:RemoveListenerCertificates",
        "elasticloadbalancing:RemoveTags",
        "elasticloadbalancing:SetIpAddressType",
        "elasticloadbalancing:SetSecurityGroups",
        "elasticloadbalancing:SetSubnets",
        "elasticloadbalancing:SetWebACL"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateServiceLinkedRole",
        "iam:GetServerCertificate",
        "iam:ListServerCertificates"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cognito-idp:DescribeUserPoolClient"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "waf-regional:GetWebACLForResource",
        "waf-regional:GetWebACL",
        "waf-regional:AssociateWebACL",
        "waf-regional:DisassociateWebACL"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "tag:GetResources",
        "tag:TagResources"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "waf:GetWebACL"
      ],
      "Resource": "*"
    }
  ]
}
""")
alb_role_name = f"{proj_name}-alb-role"
eks_alb_ingress_controller = aws.iam.Role(alb_role_name,
    name=alb_role_name,
    description="Permissions required by the Kubernetes AWS ALB Ingress controller to do it's job.",
    force_detach_policies=True,
    assume_role_policy="""{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::data.aws_caller_identity.current.account_id:oidc-provider/data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer}"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "eplace(data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer:sub": "system:serviceaccount:kube-system:alb-ingress-controller"
        }
      }
    }
  ]
}
""")

alb_role_attachment_name = f"{proj_name}-alb-role-attach",
alb_ingress_controller_iam_policy_role_policy_attachment = aws.iam.RolePolicyAttachment(alb_role_attachment_name,
    policy_arn=alb_ingress_controller_iam_policy_policy.arn,
    role=eks_alb_ingress_controller.name)


# #### App ####
# # Create the deployment for our app
# labels = {"app": "nginx"}
# namespace = "default" # using default for now
# app_deployment = Deployment(
#     f"{proj_name}-app-deployment",
#     spec=DeploymentSpecArgs(
#         selector=LabelSelectorArgs(match_labels=labels),
#         replicas=1,
#         template=PodTemplateSpecArgs(
#             metadata=ObjectMetaArgs(namespace=namespace, labels=labels),
#             spec=PodSpecArgs(containers=[ContainerArgs(name="nginx", image="nginx")]),
#         ),
#     ),
#     opts=ResourceOptions(parent=k8s_provider, provider=k8s_provider),
# )

# # Create our app service
# app_service_name = f"{proj_name}-app-service"
# app_service = Service(app_service_name,
#     metadata=ObjectMetaArgs(namespace=namespace, name=app_service_name),
#     spec=ServiceSpecArgs(type="NodePort", selector=labels, ports=[ServicePortArgs(port=80)]),
#     opts=ResourceOptions(parent=k8s_provider, provider=k8s_provider),
# )



# ### INGRESS ###
# # Create RBAC for Ingress deployment and service
# alb_ingress_controller_cluster_role = kubernetes.rbac.v1.ClusterRole("alb_ingress_controllerClusterRole",
#     api_version="rbac.authorization.k8s.io/v1",
#     kind="ClusterRole",
#     metadata={
#         "labels": {
#             "app.kubernetes.io/name": "alb-ingress-controller",
#         },
#         "name": "alb-ingress-controller",
#     },
#     rules=[
#         {
#             "api_groups": [
#                 "",
#                 "extensions",
#             ],
#             "resources": [
#                 "configmaps",
#                 "endpoints",
#                 "events",
#                 "ingresses",
#                 "ingresses/status",
#                 "services",
#             ],
#             "verbs": [
#                 "create",
#                 "get",
#                 "list",
#                 "update",
#                 "watch",
#                 "patch",
#             ],
#         },
#         {
#             "api_groups": [
#                 "",
#                 "extensions",
#             ],
#             "resources": [
#                 "nodes",
#                 "pods",
#                 "secrets",
#                 "services",
#                 "namespaces",
#             ],
#             "verbs": [
#                 "get",
#                 "list",
#                 "watch",
#             ],
#         },
#     ],
#     opts=ResourceOptions(parent=k8s_provider, provider=k8s_provider))

# alb_ingress_controller_cluster_role_binding = kubernetes.rbac.v1.ClusterRoleBinding("alb_ingress_controllerClusterRoleBinding",
#     api_version="rbac.authorization.k8s.io/v1",
#     kind="ClusterRoleBinding",
#     metadata={
#         "labels": {
#             "app.kubernetes.io/name": "alb-ingress-controller",
#         },
#         "name": "alb-ingress-controller",
#     },
#     role_ref={
#         "api_group": "rbac.authorization.k8s.io",
#         "kind": "ClusterRole",
#         "name": "alb-ingress-controller",
#     },
#     subjects=[{
#         "kind": "ServiceAccount",
#         "name": "alb-ingress-controller",
#         "namespace": "kube-system",
#     }],
#     opts=ResourceOptions(parent=k8s_provider, provider=k8s_provider))

# kube_system_alb_ingress_controller_service_account = kubernetes.core.v1.ServiceAccount("kube_systemAlb_ingress_controllerServiceAccount",
#     api_version="v1",
#     kind="ServiceAccount",
#     metadata={
#         "labels": {
#             "app.kubernetes.io/name": "alb-ingress-controller",
#         },
#         "name": "alb-ingress-controller",
#         "namespace": "kube-system",
#     },
#     opts=ResourceOptions(parent=k8s_provider, provider=k8s_provider))



# # Create a Service Account with the ELB role IAM role annotated to use with the Pod.
# sa_name = f"{proj_name}-sa"
# alb_role_arn = "arn:aws:iam::052848974346:role/aws-service-role/elasticloadbalancing.amazonaws.com/AWSServiceRoleForElasticLoadBalancing"
# sa = ServiceAccount(sa_name,
#     metadata=ObjectMetaArgs(
#       namespace=namespace,
#       name=sa_name,
#       annotations={
#         'eks.amazonaws.com/role-arn': alb_role_arn
#       }),
#     opts=ResourceOptions(parent=k8s_provider, provider=k8s_provider),
# )

# # Create the deployment for the alb ingress controller
# alb_deployment_name = f"{proj_name}-alb-deployment"
# alb_labels = {"app.kubernetes.io/name":"alb-ingress-controller"}
# alb_deployment = Deployment(
#     alb_deployment_name, 
#     metadata=ObjectMetaArgs(name=alb_deployment_name, namespace="kube-system", labels=alb_labels),
#     spec=DeploymentSpecArgs(
#         selector=LabelSelectorArgs(match_labels=alb_labels),
#         template=PodTemplateSpecArgs(
#             metadata=ObjectMetaArgs(labels=alb_labels),
#             spec=PodSpecArgs(containers=[ContainerArgs(
#                 name="alb-ingress-controller", 
#                 image="docker.io/amazon/aws-alb-ingress-controller:v1.1.6",
#                 args=["--ingress-class=alb","--cluster-name=synapse-eks-demo-eks-eksCluster-61add7c","--aws-vpc-id=vpc-08cc8cd01a18e129b","--aws-region=us-east-2"]
#                 #args=["--ingress-class=alb",f"--cluster-name={cluster.name}",f"--aws-vpc-id={vpc_id}","--aws-region=us-east-2"]
#                 )]
#             )
#         )
#     ),
#     opts=ResourceOptions(parent=k8s_provider, provider=k8s_provider),
# )
# # Create the ingress.
# # EKS with fargate will create an ALB
# # https://aws.amazon.com/blogs/containers/using-alb-ingress-controller-with-amazon-eks-on-fargate/
# app_ingress_name = f"{proj_name}-ingress"
# app_ingress = Ingress(
#     app_ingress_name,
#     metadata=ObjectMetaArgs(namespace=namespace, name=app_ingress_name, annotations={
#         "kubernetes.io/ingress.class": "alb",
#         "alb.ingress.kubernetes.io/scheme": "internet-facing",
#         "alb.ingress.kubernetes.io/target-type": "ip"}),
#     spec=IngressSpecArgs(
#         rules=[IngressRuleArgs(
#             http=HTTPIngressRuleValueArgs(
#                 paths=[HTTPIngressPathArgs(
#                     path="/*", backend=IngressBackendArgs(service_name=app_service_name, service_port=80)
#                 )]
#             )
#         )]
#     ),
#     opts=ResourceOptions(parent=k8s_provider, provider=k8s_provider),
# )

# # Get the OIDC provider's URL for the cluster.
# cluster_oidc_provider = cluster.core.oidc_provider
# pulumi.export("oidc url",cluster_oidc_provider.url)
# pulumi.export("oidc arn",cluster_oidc_provider.arn)

# # Create the new IAM policy for the Service Account using the AssumeRoleWebWebIdentity action.
# sa_assume_role_policy = Output.all([cluster_oidc_provider.url, cluster_oidc_provider.arn]).apply(
#     lambda args: aws.iam.get_policy_document(statements = [GetPolicyDocumentStatementArgs(
#         actions= ['sts:AssumeRoleWithWebIdentity'],
#         conditions = [GetPolicyDocumentStatementConditionArgs(
#               test='StringEquals',
#               values=[f"system:serviceaccount:${namespace}:${sa_name}"],
#               variable=f"{args[0]}:sub",
#         )],
#         effect='Allow',
#         principals=[GetPolicyDocumentStatementPrincipalArgs(identifiers=[f"{args[1]}"], type='Federated')],
#     )])
# )


# sa_assume_role_policy_json = {
#   "Version": "2012-10-17",
#   "Statement": [
#     {
#       "Effect": "Allow",
#       "Action": [
#         "elasticloadbalancing:AddListenerCertificates",
#         "elasticloadbalancing:AddTags",
#         "elasticloadbalancing:CreateListener",
#         "elasticloadbalancing:CreateLoadBalancer",
#         "elasticloadbalancing:CreateRule",
#         "elasticloadbalancing:CreateTargetGroup",
#         "elasticloadbalancing:DeleteListener",
#         "elasticloadbalancing:DeleteLoadBalancer",
#         "elasticloadbalancing:DeleteRule",
#         "elasticloadbalancing:DeleteTargetGroup",
#         "elasticloadbalancing:DeregisterTargets",
#         "elasticloadbalancing:DescribeListenerCertificates",
#         "elasticloadbalancing:DescribeListeners",
#         "elasticloadbalancing:DescribeLoadBalancers",
#         "elasticloadbalancing:DescribeLoadBalancerAttributes",
#         "elasticloadbalancing:DescribeRules",
#         "elasticloadbalancing:DescribeSSLPolicies",
#         "elasticloadbalancing:DescribeTags",
#         "elasticloadbalancing:DescribeTargetGroups",
#         "elasticloadbalancing:DescribeTargetGroupAttributes",
#         "elasticloadbalancing:DescribeTargetHealth",
#         "elasticloadbalancing:ModifyListener",
#         "elasticloadbalancing:ModifyLoadBalancerAttributes",
#         "elasticloadbalancing:ModifyRule",
#         "elasticloadbalancing:ModifyTargetGroup",
#         "elasticloadbalancing:ModifyTargetGroupAttributes",
#         "elasticloadbalancing:RegisterTargets",
#         "elasticloadbalancing:RemoveListenerCertificates",
#         "elasticloadbalancing:RemoveTags",
#         "elasticloadbalancing:SetIpAddressType",
#         "elasticloadbalancing:SetSecurityGroups",
#         "elasticloadbalancing:SetSubnets",
#         "elasticloadbalancing:SetWebACL"
#       ],
#       "Resource": "*"
#     },
#   ]
# }
# #     {
# #       "Effect": "Allow",
# #       "Action": [
# #         "iam:CreateServiceLinkedRole",
# #         "iam:GetServerCertificate",
# #         "iam:ListServerCertificates"
# #       ],
# #       "Resource": "*"
# #     },
# #     {
# #       "Effect": "Allow",
# #       "Action": [
# #         "tag:GetResources",
# #         "tag:TagResources"
# #       ],
# #       "Resource": "*"
# #     }
# #   ]
# # }


# # Create a new IAM role that assumes the AssumeRoleWebWebIdentity policy.
# sa_role = aws.iam.Role(f"{proj_name}-sa",
#     assume_role_policy = sa_assume_role_policy_json
# )

# // Attach the IAM role to an AWS S3 access policy.
# const saS3Rpa = new aws.iam.RolePolicyAttachment(saName, {
#   policyArn: 'arn:aws:iam::aws:policy/AmazonS3FullAccess',
#   role: saRole,
# });
#kind: Ingress
# metadata:
#   namespace: game-2048
#   name: ingress-2048
#   annotations:
#     kubernetes.io/ingress.class: alb
#     alb.ingress.kubernetes.io/scheme: internet-facing
#     alb.ingress.kubernetes.io/target-type: ip
# spec:
#   rules:
#     - http:
#         paths:
#           - path: /*
#             backend:
#               serviceName: service-2048
#               servicePort: 80



    # spec:
    #   containers:
    #   - image: alexwhen/docker-2048
    #     imagePullPolicy: Always
    #     name: app-2048
    #     ports:
    #     - containerPort: 80
# ---
# apiVersion: v1
# kind: Service
# metadata:
#   namespace: game-2048
#   name: service-2048
# spec:
#   ports:
#     - port: 80
#       targetPort: 80
#       protocol: TCP
#   type: NodePort
#   selector:
#     app.kubernetes.io/name: app-2048
# ---
# apiVersion: extensions/v1beta1
# kind: Ingress
# metadata:
#   namespace: game-2048
#   name: ingress-2048
#   annotations:
#     kubernetes.io/ingress.class: alb
#     alb.ingress.kubernetes.io/scheme: internet-facing
#     alb.ingress.kubernetes.io/target-type: ip
# spec:
#   rules:
#     - http:
#         paths:
#           - path: /*
#             backend:
#               serviceName: service-2048
#               servicePort: 80






# # Deploy an "app" - in this case just an NGINX container
# labels = {"app": "nginx"}
# namespace = "default" # using default for now
# app = Deployment(
#     f"{proj_name}-app",
#     spec=DeploymentSpecArgs(
#         selector=LabelSelectorArgs(match_labels=labels),
#         replicas=1,
#         template=PodTemplateSpecArgs(
#             metadata=ObjectMetaArgs(namespace=namespace, labels=labels),
#             spec=PodSpecArgs(containers=[ContainerArgs(name="nginx", image="nginx")]),
#         ),
#     ),
#     opts=ResourceOptions(parent=k8s_provider, provider=k8s_provider),
# )

# # Expose our app via a loadbalancer service
# frontend_service = Service(
#     f"{proj_name}-lb",
#     spec=ServiceSpecArgs(type="LoadBalancer", selector=labels, ports=[ServicePortArgs(port=80)]),
#     opts=ResourceOptions(parent=k8s_provider, provider=k8s_provider),
# )

# ingress = frontend_service.status.apply(lambda status: status.load_balancer.ingress[0])
# frontend_ip = ingress.apply(lambda ingress: ingress.ip or ingress.hostname or "")
# pulumi.export("frontend_ip", frontend_ip)
