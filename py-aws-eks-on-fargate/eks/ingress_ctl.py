import pulumi
from pulumi import ComponentResource, ResourceOptions
import pulumi_aws as aws
import json

class IngressCtlArgs:

    def __init__(self,
                proj_name=None,
                provider=None,
                oidc_provider_arn=None, 
                oidc_provider_url=None, 
                 ):
        self.provider = provider
        self.proj_name = proj_name
        self.oidc_provider_arn = oidc_provider_arn
        self.oidc_provider_url = oidc_provider_url

class IngressCtl(ComponentResource):

    def __init__(self,
                 name: str,
                 args: IngressCtlArgs,
                 opts: ResourceOptions = None):

        super().__init__("custom:resource:IngressCtl", name, {}, opts)


        k8s_provider = args.provider
        proj_name = args.proj_name
        oidc_provider_arn = args.oidc_provider_arn
        oidc_provider_url = args.oidc_provider_url
        controller_name = f"{proj_name}-alb-controller"

        self.alb_ingress_controller_iam_policy = aws.iam.Policy(f"{proj_name}-alb-controller-policy",
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
        """,
        opts=ResourceOptions(parent=self),
        )

        assume_role_policy = {
          "Version": "2012-10-17",
          "Statement": [
            {
              "Effect": "Allow",
              "Principal": {
                "Federated": f"{oidc_provider_arn}"
              },
              "Action": "sts:AssumeRoleWithWebIdentity",
              "Condition": {
                "StringEquals": {
                  f"{oidc_provider_url}:sub": f"system:serviceaccount:kube-system:{controller_name}"
                }
              }
            }
          ]
        }

        print(json.dumps(assume_role_policy))

        self.eks_alb_ingress_controller = aws.iam.Role(f"{proj_name}-alb-controller-role",
          description="Permissions required by the Kubernetes AWS ALB Ingress controller to do it's job.",
          force_detach_policies=True,
          assume_role_policy=json.dumps(assume_role_policy),
          opts=ResourceOptions(parent=self),
        )

        self.alb_ingress_controller_role_attachment = aws.iam.RolePolicyAttachment(f"{proj_name}-alb-controller-role-attachment",
          policy_arn=self.alb_ingress_controller_iam_policy.arn,
          role=self.eks_alb_ingress_controller.name,
          opts=ResourceOptions(parent=self),
          )

    #### k8s cluster role ####

# # Create RBAC for Ingress deployment and service
# alb_ingress_controller_cluster_role_name = f"{proj_name}-cluster-role"
# alb_ingress_controller_cluster_role = kubernetes.rbac.v1.ClusterRole(alb_ingress_controller_cluster_role_name,
#     api_version="rbac.authorization.k8s.io/v1",
#     kind="ClusterRole",
#     metadata={
#         "labels": {
#             "app.kubernetes.io/name": "alb-ingress-controller",
#         },
#         "name": alb_ingress_controller_cluster_role_name,
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

# kube_system_ingress_service_account_name = f"{proj_name}-sa"
# kube_system_alb_ingress_controller_service_account = kubernetes.core.v1.ServiceAccount(kube_system_ingress_service_account_name,
#     api_version="v1",
#     kind="ServiceAccount",
#     metadata={
#         "labels": {
#             "app.kubernetes.io/name": kube_system_ingress_service_account_name,
#         },
#         "name": kube_system_ingress_service_account_name,
#         "namespace": "kube-system",
#         ####"annotations": [{"eks.amazonaws.com/role-arn", f"{eks_alb_ingress_controller.arn}"}]
#         "annotations": {
#             "eks.amazonaws.com/role-arn": "arn:aws:iam::052848974346:role/synapse-eks-demo-alb-role"
#         },
#     },
#     opts=ResourceOptions(parent=k8s_provider, provider=k8s_provider))
# pulumi.export("kube_system_alb_ingress_controller_service_account", kube_system_alb_ingress_controller_service_account.metadata)


# alb_ingress_cluster_role_binding_name = f"{proj_name}-role-binding"
# alb_ingress_controller_cluster_role_binding = kubernetes.rbac.v1.ClusterRoleBinding(alb_ingress_cluster_role_binding_name,
#     api_version="rbac.authorization.k8s.io/v1",
#     kind="ClusterRoleBinding",
#     metadata={
#         "labels": {
#             "app.kubernetes.io/name": alb_ingress_cluster_role_binding_name,
#         },
#         "name": alb_ingress_cluster_role_binding_name,
#     },
#     role_ref={
#         "api_group": "rbac.authorization.k8s.io",
#         "kind": "ClusterRole",
#         "name": alb_ingress_controller_cluster_role_name, #"alb-ingress-controller",
#     },
#     subjects=[{
#         "kind": "ServiceAccount",
#         "name": kube_system_ingress_service_account_name,
#         "namespace": "kube-system",
#     }],
#     opts=ResourceOptions(parent=k8s_provider, provider=k8s_provider))

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





    ### deploy controller ####

        self.register_outputs({})
