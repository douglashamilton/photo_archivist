
# Development (execution) plan

Outline the development plan required to build the slice. 

Assess the design and breakdown the application into single classes / components, as required to build the solution incrementally.

Each increment represents a vertical slice of functionality. 

Each increment is likely to require:
1. A spike investigation
2. Development work
3. Test creation
4. Execution and debugging

The plan needs to contain everything required for you (the agent) to generate the next vertical slice. 

It is expected that you (the agent) re-appraise the solution upon each increment. 

## PLAN Template

# <Short, action-oriented description>

This Plan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

## Purpose / Big Picture

Explain in a few sentences what someone gains after this change and how they can see it working. State the user-visible behavior you will enable.

## Progress

Use a list with checkboxes to summarize granular steps. Every stopping point must be documented here, even if it requires splitting a partially completed task into two (“done” vs. “remaining”). This section must always reflect the actual current state of the work.

- [x] (2025-10-01 13:00Z) Example completed step.
- [ ] Example incomplete step.
- [ ] Example partially completed step (completed: X; remaining: Y).

Use timestamps to measure rates of progress.

## Plan of Work

Describe, in prose, the sequence of edits and additions. For each edit, name the file and location (function, module) and what to insert or change. Keep it concrete and minimal.

## Concrete Steps

State the exact commands to run and where to run them (working directory). When a command generates output, show a short expected transcript so the reader can compare. This section must be updated as work proceeds.

## Validation and Acceptance

Describe how to start or exercise the system and what to observe. Phrase acceptance as behavior, with specific inputs and outputs. If tests are involved, say "run <project’s test command> and expect <N> passed; the new test <name> fails before the change and passes after>".

## Interfaces and Dependencies

Be prescriptive. Name the libraries, modules, and services to use and why. Specify the types, traits/interfaces, and function signatures that must exist at the end of the milestone. Prefer stable names and paths such as `crate::module::function` or `package.submodule.Interface`. E.g.:

In crates/foo/planner.rs, define:

    pub trait Planner {
        fn plan(&self, observed: &Observed) -> Vec<Action>;
    }

