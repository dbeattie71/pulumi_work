import pulumi
from pulumi import ComponentResource, ResourceOptions
from pulumi_kubernetes.rbac.v1 import ClusterRole,ClusterRoleBinding,RoleRefArgs,SubjectArgs
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.core.v1 import ContainerArgs, PodSpecArgs, PodTemplateSpecArgs, ServiceAccount
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs, LabelSelectorArgs
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts, FetchOpts
from pulumi_kubernetes.yaml import ConfigFile
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


    # Using the helm chart to deploy the AWS ALB controller as per:
    # https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/deploy/installation/
    # The documenation for the chart describes a sequence of steps to be taken. 
    # The Pulumi code that goes with the steps are indicated in the comments.
    # step 1: addressed when creating EKS cluster
    # step 2: policy json is stored in ingress_ctl_jsons.py to make this code a bit more legible.
    # step 3: create AWS IAM policy as follows:
    self.ingress_ctl_iam_policy = aws.iam.Policy(f"{proj_name}-ingress-ctl-iam-policy",
      policy=json.dumps(ingress_ctl_jsons.ingress_ctl_iam_policy),
      opts=ResourceOptions(parent=self))

    # step 4: create IAM role and ServiceAccount for the AWS Load balancer controller as follows:
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

    self.ingress_ctl_role_attachment = aws.iam.RolePolicyAttachment(f"{proj_name}-ingress-ctl-iam-role-attachment",
      policy_arn=self.ingress_ctl_iam_policy.arn,
      role=self.ingress_ctl_iam_role.name,
      opts=ResourceOptions(parent=self))

    self.ingress_ctl_k8s_service_account = ServiceAccount(service_account_name,
      metadata=ObjectMetaArgs(
        labels={ "app.kubernetes.io/name": "aws-load-balancer-controller" },
        name=service_account_name,
        namespace="kube-system",
        annotations={"eks.amazonaws.com/role-arn": self.ingress_ctl_iam_role.arn},
      ),
      opts=ResourceOptions(parent=self, provider=k8s_provider))

    # helm steps from the above referenced documentation has a few steps ... 
    # helm-1: "Add the EKS chart repo to helm" is not applicable in pulumi
    # This is a helper function to remove the .status field from CRDs and charts because it's not a valid field and Pulumi doesn't like it. 
    # See https://github.com/pulumi/pulumi-kubernetes/issues/800
    def remove_status(obj, opts):
      if obj["kind"] == "CustomResourceDefinition":
        del obj["status"]

    # helm-2: install TargetGroupBinding CRD that was downloaded from here: https://github.com/aws/eks-charts/blob/master/stable/aws-load-balancer-controller/crds/crds.yaml
    # skipped since helm chart creates the target bindings so adding the crd is not needed.
    # self.alb_controller_crd = ConfigFile(f"{proj_name}-alb-crd",
    #   file="aws-lb-controller-crd.yaml",
    #   transformations=[remove_status],
    #   opts=ResourceOptions(parent=self, provider=k8s_provider))

    # helm-3: install helm chart
    # Chart found here: https://artifacthub.io/packages/helm/aws/aws-load-balancer-controller
    alb_controller_name = f"{proj_name}-alb-controller"
    self.alb_controller = Chart(alb_controller_name,
      ChartOpts(
          chart="aws-load-balancer-controller", # Get this from the second line of the artifact hub TL;DR
          namespace="kube-system",
          version="1.1.5",
          transformations=[remove_status],
          fetch_opts=FetchOpts(
            repo="https://aws.github.io/eks-charts" # Get this from the first line of the artifcat hub TL;DR
          ),
          # Need to set these values as per the chart docs
          values={
            "clusterName":cluster_name, 
            "region":aws_region,
            "vpcId":vpc_id,
            "serviceAccount": {
            # Need to assign the ServiceAccount created above. 
            # Without this, the helm chart creates a ServiceAccount but it doesn't have the permissions needed to allow the controller to create ALBs.
              "create": False,
              "name": service_account_name, #self.ingress_ctl_k8s_service_account.metadata.name 
            }
          }
      ),
      opts=ResourceOptions(parent=self, provider=k8s_provider))

    self.register_outputs({})
