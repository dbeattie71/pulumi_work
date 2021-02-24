import pulumi
from pulumi import ResourceOptions

from pulumi_eks import Cluster

from pulumi_kubernetes import Provider
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.core.v1 import (
    ContainerArgs,
    Namespace,
    PodSpecArgs,
    PodTemplateSpecArgs,
    Service,
    ServicePortArgs,
    ServiceSpecArgs,
)
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs

import network

proj_name = pulumi.get_project()

# Create VPC and public and private subnets
network=network.Vpc(f'{proj_name}-net', network.VpcArgs())
pulumi.export("priv subnets", network.private_subnet_ids)
pulumi.export("pub subnets", network.public_subnet_ids)

# Create an EKS cluster on Fargate.
cluster = Cluster(
    f"{proj_name}-eks",
    fargate=True,
    vpc_id=network.vpc.id,
    subnet_ids=network.private_subnet_ids,
)
# Export the cluster's kubeconfig.
pulumi.export("kubeconfig", cluster.kubeconfig)

# kcfg = cluster.kubeconfig.apply(lambda cfg: output_kubeconfig(cfg))
# def output_kubeconfig(kubeconfig):
#       f = open("./kubeconfig.txt","w")
#       f.write(kubeconfig)
#       f.close()

# # Create a Kubernetes Namespace
# Export the cluster's kubeconfig.
pulumi.export("kubeconfig", cluster.kubeconfig)

# kcfg = cluster.kubeconfig.apply(lambda cfg: output_kubeconfig(cfg))
# def output_kubeconfig(kubeconfig):
#       f = open("./kubeconfig.txt","w")
#       f.write(kubeconfig)
#       f.close()
# ns = Namespace(f"{proj_name}-ns", 
#   opts=ResourceOptions(provider=cluster.provider)
# ).metadata.name
# # Export the Namespace name
# pulumi.export("name_space", ns)

# # Createa k8s provider based on kubeconfig from EKS cluster
# k8s_provider = Provider(
#     "k8s", kubeconfig=cluster.kubeconfig,
# )

# # Deploy NGINX container
# labels = {"app": "nginx"}
# nginx = Deployment(
#     "k8s-nginx",
#     spec=DeploymentSpecArgs(
#         selector=LabelSelectorArgs(match_labels=labels),
#         replicas=1,
#         template=PodTemplateSpecArgs(
#             metadata=ObjectMetaArgs(namespace=ns, labels=labels),
#             spec=PodSpecArgs(containers=[ContainerArgs(name="nginx", image="nginx")]),
#         ),
#     ),
#     opts=ResourceOptions(parent=k8s_provider, provider=k8s_provider),
# )

# ingress = Service(
#     "k8s-nginx",
#     spec=ServiceSpecArgs(type="LoadBalancer", selector=labels, ports=[ServicePortArgs(port=80)]),
#     opts=ResourceOptions(parent=k8s_provider, provider=k8s_provider),
# )


