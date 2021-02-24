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
from pulumi_kubernetes.extensions.v1beta1 import Ingress

import network

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

# Create an EKS cluster on Fargate.
cluster = Cluster(
    f"{proj_name}-eks",
    fargate=True,
    vpc_id=vpc_id,
    subnet_ids=private_subnet_ids,
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

labels = {"app": "nginx"}
namespace = "default" # using default for now
app_deployment = Deployment(
    f"{proj_name}-app-deployment",
    spec=DeploymentSpecArgs(
        selector=LabelSelectorArgs(match_labels=labels),
        replicas=1,
        template=PodTemplateSpecArgs(
            metadata=ObjectMetaArgs(namespace=namespace, labels=labels),
            spec=PodSpecArgs(containers=[ContainerArgs(name="nginx", image="nginx")]),
        ),
    ),
    opts=ResourceOptions(parent=k8s_provider, provider=k8s_provider),
)

# Create our app service
app_service = Service(
    f"{proj_name}-app-service",
    spec=ServiceSpecArgs(type="NodePort", selector=labels, ports=[ServicePortArgs(port=80)]),
    opts=ResourceOptions(parent=k8s_provider, provider=k8s_provider),
)

# Create the ingress.
# EKS with fargate will create an ALB
app_ingress = Ingress(
    f"{proj_name}-ingress",
    metadata=ObjectMetaArgs(namespace=namespace),
    spec=IngressSpecArgs(rules=[RulesArgs()])


)


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

ingress = frontend_service.status.apply(lambda status: status.load_balancer.ingress[0])
frontend_ip = ingress.apply(lambda ingress: ingress.ip or ingress.hostname or "")
pulumi.export("frontend_ip", frontend_ip)
