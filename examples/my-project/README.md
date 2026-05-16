# Example Project

Demonstrates the minimal layout for a project using SkillMCP.

```
my-project/
├── skillmcp.toml              ← skill folder config (created by skills-mcp init)
└── .agents/
    ├── AGENT.md               ← behavioral rules injected every session
    └── skills/
        └── greet/
            └── SKILL.md       ← example skill
```

## Usage

```bash
# From the SkillMCP install directory, register this example project:
skills-mcp init /path/to/examples/my-project

# Or reference it at runtime by passing project_path= to list_skills / read_skill:
list_skills(project_path="/path/to/examples/my-project")
```

The `greet` skill will appear alongside any global skills from the server's own `.agents/skills/`.
