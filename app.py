#!/usr/bin/env python3
import os

import aws_cdk as cdk

from workshop_deployment.workshop_deployment_stack import WorkshopDeploymentStack


app = cdk.App()
stack = WorkshopDeploymentStack(app, "WorkshopDeploymentStack")
cdk.Tags.of(stack).add("project", "Workshop")

app.synth()
