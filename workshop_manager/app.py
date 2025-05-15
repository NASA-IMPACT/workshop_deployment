#!/usr/bin/env python3
import os

import aws_cdk as cdk

from workshop_deployment.workshop_deployment_stack import WorkshopDeploymentStack


app = cdk.App()

workshop_name = app.node.try_get_context("workshop_name")
if not workshop_name:
    print("Error: workshop_name context parameter is required")
    exit(1)

stack = WorkshopDeploymentStack(app, f"{workshop_name}-WorkshopDeploymentStack", workshop_name=workshop_name)
cdk.Tags.of(stack).add("project", "cmt-workshop")

app.synth()
