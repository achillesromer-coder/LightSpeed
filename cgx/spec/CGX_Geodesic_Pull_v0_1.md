# CGX Geodesic Pull v0.1

CGX resolves requested work through explicit dependency edges instead of rereading the full filespace to infer the next task.

An edge is a typed semantic relation such as `requires`, `depends-on`, `derives-from` or `input`. For a requested target, the reference planner computes the dependency closure and returns dependencies before dependants. Already available nodes are not rehydrated.

This is the first executable form of geodesic pull. Future routing extends source choice with authority, privacy, network cost, locality and compute constraints. Cycles are surfaced rather than silently resolved.
