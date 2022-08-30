from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_autoscaling as autoscaling,
    aws_elasticloadbalancingv2 as elbv2,
)
from constructs import Construct


class Compute(Construct):

    def __init__(self, scope: Construct, id_: str, vpc: ec2.Vpc, lambda_url: str) -> None:
        super().__init__(scope, id_)

        # Image
        amzn_linux = ec2.MachineImage.latest_amazon_linux(
            generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            edition=ec2.AmazonLinuxEdition.STANDARD,
            virtualization=ec2.AmazonLinuxVirt.HVM,
            storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE,
            cpu_type=ec2.AmazonLinuxCpuType.X86_64
        )

        # Role
        role = iam.Role(
            self,
            "WebServerRole",
            role_name="WebServerRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            # managed_policies=[
            #     iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"),
            #     iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMPatchAssociation"),
            # ]
        )

        # Security Group
        ins_sg = ec2.SecurityGroup(
            self,
            "WebServerInsSG",
            vpc=vpc,
            description="Security Group for Instance",
            security_group_name="WebServerInsSG"
        )

        ins_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(22),
            description="SSH",
            remote_rule=False
        )

        # LaunchTemplate
        block_device = ec2.BlockDevice(
            device_name="/dev/xvda",
            volume=ec2.BlockDeviceVolume.ebs(
                volume_size=8,
                volume_type=ec2.EbsDeviceVolumeType.GP3,
                delete_on_termination=True,
            )
        )

        data = ec2.UserData.for_linux()
        data.add_commands("yum update -y")
        data.add_commands("amazon-linux-extras install -y nginx1")
        data.add_commands("chown root:nginx /var/log/nginx")
        data.add_commands("chmod 760 /var/log/nginx")
        data.add_commands("systemctl restart nginx")
        data.add_commands("systemctl enable nginx")

        with open("compute/resource/index.html") as f:
            html = f.read()
            data.add_commands(f"echo '{html}' | tee /usr/share/nginx/html/index.html > /dev/null")
            data.add_commands(f"sed -i 's=$your_lambda_url={lambda_url}=' /usr/share/nginx/html/index.html")

        launch_template = ec2.LaunchTemplate(
            self,
            "WebServerTemplate",
            launch_template_name="WebServerTemplate",
            block_devices=[block_device],
            cpu_credits=ec2.CpuCredits.STANDARD,
            ebs_optimized=True,
            instance_type=ec2.InstanceType.of(
                instance_class=ec2.InstanceClass.BURSTABLE3,
                instance_size=ec2.InstanceSize.SMALL
            ),
            machine_image=amzn_linux,
            role=role,
            security_group=ins_sg,
            user_data=data
        )

        # ASG
        asg = autoscaling.AutoScalingGroup(
            self,
            "WebServerASG",
            auto_scaling_group_name="WebServerASG",
            launch_template=launch_template,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
            ),
            min_capacity=2,
            max_capacity=5,
        )

        asg.scale_on_cpu_utilization(
            "CPUUtilization",
            target_utilization_percent=70
        )

        # Application Load Balancer
        alb_sg = ec2.SecurityGroup(
            self,
            "WebServerALBSG",
            vpc=vpc,
            description="Security Group for ALB",
            security_group_name="WebServerALBSG"
        )

        alb_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="HTTP",
            remote_rule=False
        )

        ins_sg.connections.allow_from(
            other=alb_sg,
            port_range=ec2.Port.tcp(80),
            description="Load balancer to target"
        )

        alb = elbv2.ApplicationLoadBalancer(
            self,
            "WebServerALB",
            load_balancer_name="WebServerALB",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            security_group=alb_sg,
            internet_facing=True,
            ip_address_type=elbv2.IpAddressType.IPV4
        )

        listener = alb.add_listener(
            "ALBHTTPListener",
            port=80,
            open=True
        )

        listener.add_targets(
            "WebServerInstances",
            target_group_name="WebServerInstances",
            port=80,
            targets=[asg]
        )






