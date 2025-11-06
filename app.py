#!/usr/bin/env python3
import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (
    Stack,
    aws_organizations as orgs,
    aws_config as config,
    aws_guardduty as guardduty,
    aws_securityhub as securityhub,
)

class MultiAccountGovernanceStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # AWS Organizations structure (declarative)
        # Root
        #  ├── Security OU
        #  ├── Infrastructure OU
        #  └── Workloads OU
        #       ├── Dev OU
        #       ├── Staging OU
        #       └── Production OU

        # Service Control Policies
        scp_deny_region = orgs.CfnPolicy(
            self, "DenyNonApprovedRegions",
            content={
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Deny",
                    "Action": "*",
                    "Resource": "*",
                    "Condition": {
                        "StringNotEquals": {
                            "aws:RequestedRegion": ["us-east-1", "us-west-2", "eu-west-1"]
                        }
                    }
                }]
            },
            description="Restrict to approved regions only",
            name="DenyNonApprovedRegions",
            type="SERVICE_CONTROL_POLICY"
        )

        # AWS Config for compliance monitoring
        config_recorder = config.CfnConfigurationRecorder(
            self, "ConfigRecorder",
            role_arn=f"arn:aws:iam::{self.account}:role/aws-service-role/config.amazonaws.com/AWSServiceRoleForConfig",
            recording_group=config.CfnConfigurationRecorder.RecordingGroupProperty(
                all_supported=True,
                include_global_resource_types=True
            )
        )

        # GuardDuty for threat detection
        guardduty_detector = guardduty.CfnDetector(
            self, "GuardDutyDetector",
            enable=True,
            finding_publishing_frequency="FIFTEEN_MINUTES"
        )

        # Security Hub for centralized security findings
        security_hub = securityhub.CfnHub(
            self, "SecurityHub",
            control_finding_generator="SECURITY_CONTROL"
        )

app = cdk.App()
MultiAccountGovernanceStack(app, "EnterpriseGovernance",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region") or "us-east-1"
    )
)
app.synth()
