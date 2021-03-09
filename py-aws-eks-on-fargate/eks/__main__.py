import pulumi
import app  
import ingress_ctl
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import time

from pulumi import ResourceOptions, Output
from pulumi_eks import Cluster
from pulumi_eks.cluster import FargateProfileArgs
from pulumi_aws.eks import FargateProfileSelectorArgs, get_cluster_auth
from pulumi_kubernetes import Provider
from pulumi_kubernetes.core.v1 import Namespace
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs
from pulumi_kubernetes.extensions.v1beta1 import (
    Ingress,
    IngressSpecArgs,
    IngressRuleArgs,
    HTTPIngressRuleValueArgs,
    HTTPIngressPathArgs,
    IngressBackendArgs)




# Get config values to use for the stack
config = pulumi.Config()
proj_name = config.get("projName") or pulumi.get_project()
vpc_stack = config.get("vpcStack")

# One way environments can be structured is via a multi-stack architecture,
# where different stacks deploy different sets of infrastructure.
# In this case, we have a network stack that stands up the VPC and related parts, and
# this main EKS stack that stands up the EKS cluster.
# So, get the network information from the network stack.
vpc_stack_ref = pulumi.StackReference(vpc_stack)
vpc_id = vpc_stack_ref.get_output("vpcId")
priv_subnet_ids = vpc_stack_ref.get_output("privateSubnetIds")
public_subnet_ids = vpc_stack_ref.get_output("publicSubnetIds")

### EKS CLUSTER ON FARGATE ###
# Using an app-specific namespace instead of default.
app_namespace_name = f"{proj_name}-app"
alb_controller_namespace_name = f"{proj_name}-aws-lb-controller"
pulumi.export("App Namespace", app_namespace_name)
sys_namespace_name = "kube-system" # the system namespace where things like coredns run

# Create an EKS cluster on Fargate.
cluster = Cluster(
    f"{proj_name}-eks",
    fargate=FargateProfileArgs(selectors=[
        FargateProfileSelectorArgs(namespace=app_namespace_name),
        FargateProfileSelectorArgs(namespace=sys_namespace_name),
        FargateProfileSelectorArgs(namespace=alb_controller_namespace_name),
    ]),
    vpc_id=vpc_id,
    private_subnet_ids = priv_subnet_ids,
    create_oidc_provider=True,
    version="1.19",
)
# Get the kubeconfig but keep it a secret.
kubeconfig = pulumi.Output.secret(cluster.kubeconfig)
pulumi.export("kubeconfig", kubeconfig)

# Create a k8s provider based on kubeconfig from EKS cluster.
k8s_provider = Provider(
    "k8s", kubeconfig=kubeconfig,
)

### INGRESS Controller ###
# Deploy the aws alb ingress controller and any related bits
# ingress_controller = Output.all(cluster.core.oidc_provider.arn, cluster.core.oidc_provider.url).apply(
#     lambda args: ingress_ctl.IngressCtl(f"{proj_name}", ingress_ctl.IngressCtlArgs(
ingress_controller = ingress_ctl.IngressCtl(f"{proj_name}", ingress_ctl.IngressCtlArgs(
        provider=k8s_provider,
        proj_name=proj_name,
        oidc_provider=cluster.core.oidc_provider,
        # oidc_provider_arn=args[0],
        # oidc_provider_url=args[1],
        cluster_name = cluster.core.cluster.name,
        namespace_name = alb_controller_namespace_name,
        vpc_id = cluster.core.vpc_id,
        aws_region= "us-east-2",
    ))
# # )

### App ###
# Use custom resource to create the App
app_name = f"{proj_name}-app"
app_labels = {"app": "nginx"}
#app_labels = {"app": "game"}
app = app.App(app_name, app.AppArgs(
    provider=k8s_provider,
    app_namespace_name=app_namespace_name,
    app_name=app_name,
    image_name="nginx",
    #image_name="alexwhen/docker-2048",
    labels=app_labels,
    replicas=2,
    service_port=80,
))

# Create the ingress - the above created controller but not the actual ingress to direct traffic to the application pod.
# So, create an ingress that will trigger the aws alb controller to create the ALB and plumb things to the application pod(s).
# https://aws.amazon.com/blogs/containers/using-alb-ingress-controller-with-amazon-eks-on-fargate/
app_ingress_name = f"{proj_name}-ingress"
app_ingress = Ingress(
    app_ingress_name,
    metadata=ObjectMetaArgs(namespace=app_namespace_name, name=app_ingress_name, annotations={
        "kubernetes.io/ingress.class": "alb",
        "alb.ingress.kubernetes.io/scheme": "internet-facing",
        "alb.ingress.kubernetes.io/target-type": "ip",
        #"pulumi.com/timeoutSeconds": "360",
        "pulumi.com/skipAwait": "true" # This skipAwait annotation is needed because the ALB controller doesn't return a status and so Pulumi timesout waiting for a value that never shows up.
    }),
    spec=IngressSpecArgs(
        rules=[IngressRuleArgs(
            http=HTTPIngressRuleValueArgs(
                paths=[HTTPIngressPathArgs(
                    path="/*", 
                    backend=IngressBackendArgs(service_name=app.app_service.metadata.name, service_port=80)
                )]
            )
        )]
    ),
    opts=ResourceOptions(parent=k8s_provider, provider=k8s_provider, depends_on=[ingress_controller,app]),
)

### use python k8s client to wait for the ingress status to show the ALB information.
def get_alb_endpoint(args):
    cluster = args[0]
    #cluster_address = cluster.kubeconfig.apply(lambda kubeconfig: kubeconfig["clusters"][0]["cluster"]["server"]
    cluster_address = pulumi.Output(cluster.kubeconfig["clusters"][0]["cluster"]["server"])
    print("cluster_address", cluster_address)
    cluster_auth_obj = get_cluster_auth(cluster.core.cluster.id)
    cluster_auth = cluster_auth_obj.token
    print("cluster_auth", cluster_auth)
    api_config = client.Configuration()
    api_config.host = cluster_address
    api_config.verify_ssl = False
    api_config.api_key['authorization'] = cluster_auth
    api_config.api_key_prefix['authorization'] = 'Bearer'
    api_instance = client.ExtensionsV1beta1Api(client.ApiClient(api_config))
    name = app_ingress_name
    namespace = app_namespace_name
    found_lb = False
    done = False
    lb_check_count = 0
    while not done:
        print("lb_check_count", lb_check_count)
        try:
            api_response = api_instance.read_namespaced_ingress_status(name, namespace) 
            print("getting response")
            alb_endpoint = api_response.status.load_balancer.ingress[0].hostname
            print("alb_endpoint", alb_endpoint)
            found_lb = True
            done = True
        except:
            print("exception")
            lb_check_count = lb_check_count + 1
            if lb_check_count > 2:
                done = True
            print("sleeping")
            time.sleep(15)
    return f"{alb_endpoint}"

if not pulumi.runtime.is_dry_run():
    alb_endpoint = Output.all(cluster).apply(lambda args: get_alb_endpoint(args))
    #pulumi.export("App URL", f"http://{alb-endpoint}")
    pulumi.export("App URL", alb_endpoint.apply(lambda ep: f"http://{ep}"))


# get_ingress = Ingress.get("my-gotten_ingress", 
#     id=app_ingress.id,
#     opts=ResourceOptions(provider=k8s_provider, depends_on=[app_ingress]),
# )
# pulumi.export("gotten ingress", get_ingress)

# # lb_dns = app_ingress.status.apply(lambda status: status.load_balancer.ingress[0].hostname)
# # pulumi.export("lb dns", lb_dns)


# CAVEATS:
# The AWS ALB ingress controller doesn't populate the Ingress' address field (related to the skipAwait setting above).
# So, there's no property to tell me the ALB DNS name that I can export to the user.
# So, need to figure out how to get that ALB DNS name so it can be outputted from the stack to confirm things are working.
# In the mean time, going to the AWS console view for EC2-Load Balancers will show the ALB and provide that DNS name. :(
# NOTE: You will have a wait a few minutes for the LB and Target group and targets to be fully configured.



