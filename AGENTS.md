# Agent Guidelines

Welcome! 

## Navigation

Review the following folders before suggesting or making any substantive changes:
- Product requirement specs, technical design documents and build plans are in `./docs/`.
- Templates that you (the agent) can follow are in `./.agent/`.

## Development Practices
- Favor small, focused commits and clearly describe your changes.
- Keep changes within scope; open follow-up tasks for large refactors.
- Ensure new or modified code is covered by existing tests or add new ones as needed.
- Run the relevant test suite(s) before committing.
- Where files have been created that **should not** be version-controlled, update `/.gitignore` accordingly. Create a new `/.gitignore` if none exists. 

## Pull Requests
- Summarize user-facing and technical changes succinctly.
- Reference any docs or decisions from the `./docs/` folder that guided your work.