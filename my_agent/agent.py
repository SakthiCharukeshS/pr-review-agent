from google.adk.agents import Agent


def get_pr_diff(pr_number: int) -> dict:
    """Fetches the code changes (diff) for a pull request.

    Args:
        pr_number: The pull request number, e.g. 1.

    Returns:
        A dict with the PR title and the diff text.
    """
    fake_diff = '''
--- a/calculator.py
+++ b/calculator.py
@@ -1,6 +1,9 @@
+import os
+API_KEY = "sk-12345-secret"

 def divide(a, b):
-    return a / b
+    return a / b   # no check for b == 0

 def average(nums):
-    return sum(nums) / len(nums)
+    total = 0
+    for i in range(len(nums) + 1):
+        total += nums[i]
+    return total / len(nums)
'''
    return {"title": "Update calculator", "diff": fake_diff}


root_agent = Agent(
    name="root_agent",
    model="gemini-3.8-flash",
    description="Reviews pull requests.",
    instruction=(
        "You are a strict senior engineer. When the user gives a PR number, "
        "call get_pr_diff to fetch it, then review the diff. "
        "List problems under: Bugs, Security, Style. Be specific and brief."
    ),
    tools=[get_pr_diff],
)