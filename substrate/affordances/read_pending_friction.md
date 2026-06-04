---
id: read_pending_friction
name: Read pending Friction
materials:
- smoother_read_pending_friction
---
Return Friction observations the Judge has emitted and no Smoother has addressed yet. Supports both listing pending Friction with limit and reading one exact pending Friction with friction_id. When a Smoother is dispatched to a specific Friction id, pass that id as the material's top-level friction_id argument so the trail records the exact observation content and evidence used as the closure basis, rather than relying on an elidable bulk pending list. A targeted read must return that exact pending Friction's content and observation_data, or an empty result if the Friction is absent or already addressed.
