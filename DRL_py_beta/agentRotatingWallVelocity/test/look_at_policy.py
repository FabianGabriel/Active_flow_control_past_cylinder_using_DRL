# -*- coding: utf-8 -*-
"""
Created on Tue Aug 17 23:05:38 2021

@author: gabri
"""

import torch
import numpy as np

policy = torch.jit.load("policy.pt")
example = torch.ones((2, 400)).double() * -1
output = policy(example)
print(output)