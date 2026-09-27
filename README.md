# Project Tracker CLI

A command-line project management tool for a small development team. You can create users, give them projects, add tasks to those projects, assign contributors and mark work complete. Everything is saved to a local JSON file.

The tool also has an **AI summary feature**: `summarize-project` sends a project's data to a local AI model through [Ollama](https://ollama.com) and prints a short summary, risks and next steps. If the model isn't available, the tool says so and shows a rule-based summary instead of crashing.

## Features

- Create and list users, with email validation
- Add projects to users and list them by user (one-to-many: a user owns many projects)
- Add tasks to projects, assign contributors and mark tasks complete (many-to-many: a task can have many contributors, and a user can work on many tasks)
- See progress per project (tasks done, percentage, status)
- Data saved to `data/tracker.json`, with error handling for missing or corrupted files
- Readable tables in the terminal, made with `tabulate`
- AI-generated project summaries through a reusable Ollama client, with an offline fallback

## Setup

Requires Python 3.10 or newer.

```bash
git clone https://github.com/brotherhood1511-boop/OOP-with-Python-1--Project-Management-CLI-Tool.git
cd OOP-with-Python-1--Project-Management-CLI-Tool
pipenv install
pipenv shell
```

Or with pip:

```bash
pip install -r requirements.txt
```

### Optional: set up the AI model

Only `summarize-project` uses the AI. Every other command works without it.

1. Install Ollama from https://ollama.com/download
2. Download the model: `ollama pull llama3.2`
3. Make sure Ollama is running


## Usage

Run commands with `python main.py <command> [options]`. Add `-h` to any command to see its options, for example `python main.py add-task -h`.

| Command | What it does | Example |
|---|---|---|
| `add-user` | Create a user | `python main.py add-user --name "Alex" --email "alex@example.com"` |
| `list-users` | Show all users | `python main.py list-users` |
| `add-project` | Create a project for a user | `python main.py add-project --user "Alex" --title "CLI Tool" --description "Build project tracker" --due 2026-10-03` |
| `list-projects` | Show all projects, or one user's | `python main.py list-projects --user "Alex"` |
| `add-task` | Add a task, optionally with contributors | `python main.py add-task --project "CLI Tool" --title "Write README" --assign Alex Jordan` |
| `list-tasks` | Show tasks for a project or a user | `python main.py list-tasks --project "CLI Tool"` |
| `assign-task` | Add a contributor to a task | `python main.py assign-task --project "CLI Tool" --task "Write README" --user "Alex"` |
| `complete-task` | Mark a task complete | `python main.py complete-task --project "CLI Tool" --task "Write README"` |
| `summarize-project` | AI summary, risks and next steps | `python main.py summarize-project --project "CLI Tool"` |

Names and titles are not case-sensitive, so `--user alex` finds "Alex".

### AI summary options

- `--model mistral` uses a different Ollama model (default: `llama3.2`, or set `OLLAMA_MODEL`)
- `--offline` skips the AI and uses the rule-based summary
- Set `OLLAMA_HOST` to use an Ollama server at a different address

If Ollama isn't installed or running, you'll see a warning followed by an offline summary.

### Data file

Data is saved to `data/tracker.json`. The repo includes sample data so you can try the commands right away. To start fresh, delete that file. To use a different file, pass `--data path/to/file.json` before the command.

## Project structure

```text
├── main.py                         # Entry point
├── data/tracker.json               # Saved users, projects and tasks
└── project_tracker/
    ├── cli.py                      # argparse commands and output
    ├── tracker.py                  # ProjectTracker: rules, relationships, load/save
    ├── storage.py                  # JSONStorage: safe file reading and writing
    ├── utils.py                    # Validation and table formatting helpers
    ├── models/                     # BaseModel, User, Project, Task
    └── services/                   # OllamaChatClient and ProjectSummarizer
```

## Design notes

- **Inheritance and encapsulation:** `User`, `Project` and `Task` all extend the abstract `BaseModel`, which provides ids, timestamps and the `to_dict()`/`from_dict()` contract. Attributes are validated through properties.
- **Separation of concerns:** the CLI only parses commands and prints output. `ProjectTracker` holds the business rules, and `JSONStorage` handles the file.
- **Reusable AI client:** `OllamaChatClient` knows nothing about projects. It sends a prompt and returns text, so it can be reused for other features. `ProjectSummarizer` builds the project-specific prompt.
- **Safe saves:** data is written to a temporary file and then swapped into place, so an interrupted save can't corrupt the data file.

## Dependencies

- `tabulate`: table output in the terminal
- `ollama`: Python client for the local AI model