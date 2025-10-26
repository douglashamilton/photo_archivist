# Plan and Execute

## Step 1

Read the PRD and TDD both located in the `../docs/` folder. If either document does not exist, inform the user that the documents are missing and request that they complete the previous steps first.

## Step 2

Iteratively plan and execute the development of the application in vertical slices, following these steps:
1. **Review Current State**: Assess the current codebase and the gap to the MVP.
2. **Plan the Next Slice**: Create a development plan for the next vertical slice (slice ID) based on the PRD, TDD and current codebase. Use the format in `./.agent/plan-template.md`. Write the plan in markdown format to the following folder: `../docs/` with the filename `slice-<slice_ID>-plan.md`.
3. **Execute the Slice**: Implement the planned slice, put testing in place to ensure the new code works as expected and does not introduce regressions.
4. **Document Changes**: Update the build log concisely with relevant documentation to reflect the changes made, in following folder: `../docs/` with the filename `build-log.md`.. 
5. After each iteration, the plan needs to inform the user of a manual test that can be performed to inspect the change. 
6. **Loop Back**: Repeat steps 1-5 until the MVP is fully developed.

