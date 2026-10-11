import json
import os

dataset_path = "/run/media/pranav/Work/SoloProjects/my own ideas/TaskMateV0/apps/api/evaluation/dataset.json"

with open(dataset_path, "r") as f:
    data = json.load(f)

start_id = 51

new_items = [
    {
        "message": "Check my recent GitHub issues and create a task for each one",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_github",
        "description": "Multi-step workflow checking github and creating tasks"
    },
    {
        "message": "Summarize the PRs for the Acme Website and update the project notes",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"project_name": "Acme Website"},
        "category": "agent_github",
        "description": "Cross-system PR summary and project update"
    },
    {
        "message": "Find any bugs reported on GitHub yesterday and make them high priority tasks",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"priority": "HIGH"},
        "category": "agent_github",
        "description": "Search github issues and map to high priority tasks"
    },
    {
        "message": "What is the status of the frontend repository on GitHub?",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_github",
        "description": "GitHub repo info request"
    },
    {
        "message": "Look up issue #42 on Github and add a comment that we are working on it",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_github",
        "description": "Interact with specific GitHub issue"
    },
    {
        "message": "Review my open pull requests and list any that are failing CI",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_github",
        "description": "Check PR statuses"
    },
    {
        "message": "Are there any mentions of me in the Mobile App repo?",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"project_name": "Mobile App"},
        "category": "agent_github",
        "description": "Check github mentions"
    },
    {
        "message": "Close the task 'login bug' and close the corresponding issue on github",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"task_name": "login bug"},
        "category": "agent_github",
        "description": "Multi-step local and remote action"
    },
    {
        "message": "Sync all my github repositories with my TaskMate projects",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_workflow",
        "description": "Broad sync request"
    },
    {
        "message": "Analyze the codebase for the Client Portal and suggest tasks",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"project_name": "Client Portal"},
        "category": "agent_workflow",
        "description": "Analysis and suggestion"
    },
    {
        "message": "Gather all overdue tasks and open a github issue for each",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_workflow",
        "description": "Local tasks to remote issues"
    },
    {
        "message": "Summarize my day and commit the summary to my daily-log repo",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_workflow",
        "description": "Summarize and commit"
    },
    {
        "message": "Can you check if there are any new releases for the dependencies of Beta Corp project?",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"client_name": "Beta Corp"},
        "category": "agent_workflow",
        "description": "Complex dependency check"
    },
    {
        "message": "Create tasks for all the TODO comments in the latest PR",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_workflow",
        "description": "Parse PR and create tasks"
    },
    {
        "message": "Give me an overview of the workload based on GitHub issues and TaskMate tasks",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_workflow",
        "description": "Cross-system workload overview"
    },
    {
        "message": "List all repositories I have access to",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_github",
        "description": "GitHub list repos"
    },
    {
        "message": "Find the last 5 closed issues in the Acme Website repo",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"project_name": "Acme Website"},
        "category": "agent_github",
        "description": "GitHub closed issues search"
    },
    {
        "message": "Create a new project for my personal website and link it to the github repo",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"project_name": "personal website"},
        "category": "agent_workflow",
        "description": "Create project and link repo"
    },
    {
        "message": "Mark all tasks related to 'caching' as done and close PR #12",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"search_query": "caching"},
        "category": "agent_workflow",
        "description": "Multi-step completion"
    },
    {
        "message": "Create a high priority task to review PR #100",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"priority": "HIGH"},
        "category": "agent_github",
        "description": "Task creation from PR"
    },
    {
        "message": "Who opened the last PR in the Mobile App repo?",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"project_name": "Mobile App"},
        "category": "agent_github",
        "description": "GitHub PR metadata request"
    },
    {
        "message": "Is there any task assigned to me in GitHub that is not in TaskMate?",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_workflow",
        "description": "Cross-system diff"
    },
    {
        "message": "Update the priority of the database migration task based on the Github issue urgency",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"task_name": "database migration"},
        "category": "agent_workflow",
        "description": "Dynamic priority update"
    },
    {
        "message": "Create a task for each client to send a weekly update",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_workflow",
        "description": "Looping task creation"
    },
    {
        "message": "Find all tasks that are IN_PROGRESS but have no recent github activity",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"status": "IN_PROGRESS"},
        "category": "agent_workflow",
        "description": "Cross-system correlation"
    },
    {
        "message": "Search GitHub for 'memory leak' and add a task to investigate if found",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"search_query": "memory leak"},
        "category": "agent_workflow",
        "description": "Conditional task creation"
    },
    {
        "message": "What is the most active project right now based on github commits?",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_github",
        "description": "GitHub activity analysis"
    },
    {
        "message": "Create tasks for all open issues labeled 'bug' in the Client Portal",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"project_name": "Client Portal", "label": "bug"},
        "category": "agent_workflow",
        "description": "Task creation from GitHub labels"
    },
    {
        "message": "Are there any blockers for the current tasks?",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_workflow",
        "description": "Ambiguous status request requiring context"
    },
    {
        "message": "Summarize the latest comments on issue #56",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_github",
        "description": "GitHub issue comments summary"
    },
    {
        "message": "Add a task to follow up with Acme Inc and check their open PRs",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"client_name": "Acme Inc"},
        "category": "agent_workflow",
        "description": "Multi-step client task and PR check"
    },
    {
        "message": "List all my clients and their active github repos",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_workflow",
        "description": "Cross-system listing"
    },
    {
        "message": "Change the status of all overdue tasks to REVIEW and comment on their github issues",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"status": "REVIEW"},
        "category": "agent_workflow",
        "description": "Bulk multi-step action"
    },
    {
        "message": "Which client has the most pending tasks?",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_workflow",
        "description": "Data aggregation and analysis"
    },
    {
        "message": "Create a task to refactor auth and assign it to the Acme project",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"title": "refactor auth", "project_name": "Acme"},
        "category": "agent_workflow",
        "description": "Agent task creation with specific project"
    },
    {
        "message": "Delete the testing task and close issue #99",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"task_name": "testing"},
        "category": "agent_workflow",
        "description": "Destructive multi-step action"
    },
    {
        "message": "Fetch the readme from the Mobile App repo and summarize its goals",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"project_name": "Mobile App"},
        "category": "agent_github",
        "description": "GitHub file fetch and summarize"
    },
    {
        "message": "Find any closed tasks that still have open PRs",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_workflow",
        "description": "Cross-system inconsistency check"
    },
    {
        "message": "Set up a new workspace for project Zeta with a github repo and initial tasks",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"project_name": "Zeta"},
        "category": "agent_workflow",
        "description": "Complex scaffolding"
    },
    {
        "message": "Check the API docs task. If the PR is merged, mark the task as DONE.",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"task_name": "API docs"},
        "category": "agent_workflow",
        "description": "Conditional execution"
    },
    {
        "message": "What did I work on yesterday across all projects and GitHub?",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_workflow",
        "description": "Cross-system daily summary"
    },
    {
        "message": "Compile a report of all HIGH priority bugs across all my repos",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"priority": "HIGH"},
        "category": "agent_workflow",
        "description": "Cross-system reporting"
    },
    {
        "message": "Find out who reviewed PR #10 and add a task to thank them",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_workflow",
        "description": "GitHub PR metadata to task creation"
    },
    {
        "message": "Clean up my workspace by closing completed tasks and their issues",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_workflow",
        "description": "Maintenance workflow"
    },
    {
        "message": "Sync the due dates of TaskMate tasks with the milestones in GitHub",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_workflow",
        "description": "Data sync"
    },
    {
        "message": "Create a summary issue in the Client Portal repo with all pending tasks",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"project_name": "Client Portal"},
        "category": "agent_workflow",
        "description": "Task export to GitHub"
    },
    {
        "message": "Check if there are any urgent issues on github, if so notify me, else get me a coffee",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_workflow",
        "description": "Humorous/ambiguous conditional request"
    },
    {
        "message": "What is the average time to close an issue in the Acme Website repo?",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {"project_name": "Acme Website"},
        "category": "agent_github",
        "description": "GitHub analytics"
    },
    {
        "message": "Audit my tasks and flag any that have no corresponding GitHub issue",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_workflow",
        "description": "Audit workflow"
    },
    {
        "message": "Generate a changelog for the last week based on merged PRs and closed tasks",
        "expected_intent": "RUN_AGENT",
        "expected_entities": {},
        "category": "agent_workflow",
        "description": "Changelog generation"
    }
]

for i, item in enumerate(new_items):
    item["id"] = start_id + i
    data.append(item)

with open(dataset_path, "w") as f:
    json.dump(data, f, indent=2)

print(f"Added {len(new_items)} items. Total is now {len(data)}.")

