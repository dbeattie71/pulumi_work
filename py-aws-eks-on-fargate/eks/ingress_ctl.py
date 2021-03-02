import pulumi
from pulumi import ComponentResource, ResourceOptions
from pulumi_kubernetes.rbac.v1 import ClusterRole,ClusterRoleBinding,RoleRefArgs,SubjectArgs
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.core.v1 import ContainerArgs, PodSpecArgs, PodTemplateSpecArgs, ServiceAccount
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs, LabelSelectorArgs
import pulumi_aws as aws
import ingress_ctl_jsons
import json

class IngressCtlArgs:

  def __init__(self,
              proj_name=None,
              provider=None,
              oidc_provider_arn=None, 
              oidc_provider_url=None, 
              cluster_name=None,
              vpc_id=None,
              aws_region="us-east-2",
                ):
    self.provider = provider
    self.proj_name = proj_name
    self.oidc_provider_arn = oidc_provider_arn
    self.oidc_provider_url = oidc_provider_url
    self.cluster_name = cluster_name
    self.vpc_id = vpc_id
    self.aws_region = aws_region

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
    cluster_name = args.cluster_name
    vpc_id = args.vpc_id
    aws_region = args.aws_region
    controller_name = f"{proj_name}-alb-controller"
    service_account_name = f"{proj_name}-sa"

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
              f"{oidc_provider_url}:sub": f"system:serviceaccount:kube-system:{service_account_name}"
            }
          }
        }
      ]
    }

    self.ingress_ctl_iam_role = aws.iam.Role(f"{proj_name}-ingress-ctl-iam-role",
      description="Permissions required by the Kubernetes AWS ALB Ingress controller to do it's job.",
      force_detach_policies=True,
      assume_role_policy=json.dumps(assume_role_policy),
      opts=ResourceOptions(parent=self))

    self.ingress_ctl_iam_policy = aws.iam.Policy(f"{proj_name}-ingress-ctl-iam-policy",
      policy=json.dumps(ingress_ctl_jsons.ingress_ctl_iam_policy),
      opts=ResourceOptions(parent=self))

    self.ingress_ctl_role_attachment = aws.iam.RolePolicyAttachment(f"{proj_name}-ingress-ctl-iam-role-attachment",
      policy_arn=self.ingress_ctl_iam_policy.arn,
      role=self.ingress_ctl_iam_role.name,
      opts=ResourceOptions(parent=self))

    #### k8s cluster role ####
    #ctl_iam_role_arn = self.ingress_ctl_iam_role.arn.apply(lambda arn: arn)
    self.ingress_ctl_k8s_service_account = ServiceAccount(service_account_name,
      #api_version="v1",
      #kind="ServiceAccount",
      metadata=ObjectMetaArgs(
        labels={ "app.kubernetes.io/name": "aws-load-balancer-controller" },
        name=service_account_name,
        namespace="kube-system",
        ####"annotations": [{"eks.amazonaws.com/role-arn", f"{eks_alb_ingress_controller.arn}"}]
        #annotations={"eks.amazonaws.com/role-arn": ctl_iam_role_arn},
        annotations={"eks.amazonaws.com/role-arn": self.ingress_ctl_iam_role.arn},
      ),
      opts=ResourceOptions(parent=self, provider=k8s_provider))


    # Create RBAC for Ingress deployment and service
    ingress_ctl_k8s_role_name = f"{proj_name}-k8s-cluster-role"
    self.ingress_ctl_k8s_role = ClusterRole(ingress_ctl_k8s_role_name,
      #api_version="rbac.authorization.k8s.io/v1",
      #kind="ClusterRole",
      metadata=ObjectMetaArgs(
        labels={"app.kubernetes.io/name": "aws-load-balancer-controller"},
      ),
      #rules=json.dumps(ingress_ctl_jsons.ingress_ctl_k8s_role_rules),
      rules=ingress_ctl_jsons.ingress_ctl_k8s_role_rules,
      opts=ResourceOptions(parent=self, provider=k8s_provider))


    ingress_ctl_k8s_role_binding_name = f"{proj_name}-k8s-ingress-ctl-role-binding"
    self.ingress_ctl_k8s_role_binding = ClusterRoleBinding(ingress_ctl_k8s_role_binding_name,
      #api_version="rbac.authorization.k8s.io/v1",
      #kind="ClusterRoleBinding",
      metadata=ObjectMetaArgs(
        labels={"app.kubernetes.io/name": "aws-load-balancer-controller"},
        #"name": ingress_ctl_k8s_role_binding_name,
      ),
      role_ref=RoleRefArgs(
        api_group="rbac.authorization.k8s.io",
        kind="ClusterRole",
        name=self.ingress_ctl_k8s_role.metadata.name #  alb_ingress_controller_cluster_role_name, #"alb-ingress-controller",
      ),
      subjects=[SubjectArgs(
        kind="ServiceAccount",
        name=self.ingress_ctl_k8s_service_account.metadata.name, #kube_system_ingress_service_account_name,
        namespace="kube-system",
      )],
      opts=ResourceOptions(parent=self, provider=k8s_provider))

    # Create the deployment for the alb ingress controller
    alb_deployment_name = f"{proj_name}-alb-deployment"
    alb_labels = {"app.kubernetes.io/name":"alb-ingress-controller"}
    self.alb_deployment = Deployment(
      alb_deployment_name, 
      #metadata=ObjectMetaArgs(name=alb_deployment_name, namespace="kube-system", labels=alb_labels),
      metadata=ObjectMetaArgs(name="aws-load-balancer-controller", namespace="kube-system", labels=alb_labels),
      spec=DeploymentSpecArgs(
        selector=LabelSelectorArgs(match_labels=alb_labels),
        template=PodTemplateSpecArgs(
          metadata=ObjectMetaArgs(labels=alb_labels),
          spec=PodSpecArgs(containers=[ContainerArgs(
              name="alb-ingress-controller", 
              #image="docker.io/amazon/aws-alb-ingress-controller:v1.1.6",
              image="602401143452.dkr.ecr.us-west-2.amazonaws.com/amazon/aws-load-balancer-controller",
              args=["--ingress-class=alb",f"--cluster-name={cluster_name}",f"--aws-vpc-id={vpc_id}",f"--aws-region={aws_region}"]
              #args=["--ingress-class=alb","--cluster-name=eks-main-eks-eksCluster-76d53ff","--aws-vpc-id=vpc-0b7b646c66cd6f099","--aws-region=us-east-2"]
              #args=["--ingress-class=alb",f"--cluster-name={cluster.name}",f"--aws-vpc-id={vpc_id}","--aws-region=us-east-2"]
              )],
            service_account_name=self.ingress_ctl_k8s_service_account.metadata.name,
          )
        )
      ),
      opts=ResourceOptions(parent=self, provider=k8s_provider),
    )

    ### deploy controller ####

    self.register_outputs({})
