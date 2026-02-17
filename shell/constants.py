"""Shell constants - commands, roles, mentions."""
from typing import Dict
from agents.factory import Role


COMMANDS = [
    "help", "team", "workflows", "workflow", "config",
    "clear", "history", "save", "exit", "quit",
    "projects", "newproject", "files", "tree", "readfile", "workspace",
    "stages", "stage",
    "github", "tools", "kickoff",
]

ROLES = ["senior_dev", "coder", "coder_2", "qa", "ba", "reviewer"]

WORKFLOWS = ["feature", "review", "bugfix", "architecture", "project_setup", "pr_review", "full_feature", "test_and_verify"]

STAGES = [
    "planning_discussion",
    "architecture_alignment",
    "implementation_breakdown",
    "verification_hardening",
    "release_handoff",
]

MENTION_ALIASES: Dict[str, Role] = {
    "@senior": Role.SENIOR_DEV,
    "@seniordev": Role.SENIOR_DEV,
    "@architect": Role.SENIOR_DEV,
    "@lead": Role.SENIOR_DEV,
    "@tech": Role.SENIOR_DEV,
    
    "@dev": Role.CODER,
    "@coder": Role.CODER,
    "@dev1": Role.CODER,
    "@developer": Role.CODER,
    "@code": Role.CODER,
    
    "@dev2": Role.CODER_2,
    "@coder2": Role.CODER_2,
    "@gemini": Role.CODER_2,
    
    "@qa": Role.QA,
    "@test": Role.QA,
    "@tester": Role.QA,
    "@quality": Role.QA,
    "@bug": Role.QA,
    
    "@ba": Role.BA,
    "@analyst": Role.BA,
    "@specs": Role.BA,
    "@reqs": Role.BA,
    
    "@reviewer": Role.REVIEWER,
    "@review": Role.REVIEWER,
    "@cr": Role.REVIEWER,
}

TEAM_MENTIONS = ["@team", "@all", "@devteam", "@everyone"]
