import os

API_KEY = "sk-12345-secret"

def divide(a, b):
    return a / b

def average(nums):
    total = 0
    for i in range(len(nums) + 1):
        total += nums[i]
    return total / len(nums)