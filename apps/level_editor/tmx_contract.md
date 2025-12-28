# Level TMX Contract (Current Runtime Expectations)

This captures what the game currently assumes when loading TMX content. It is based on runtime code in `src/services/load_from_tmx_manager.py` and `src/scenes/level_scene.py` and is meant to keep an editor aligned with the live loader.

## Map Files
- Each level uses two TMX files:
  - `map.tmx`: tile layers + object layers used at runtime.
  - `map_properties.tmx`: map-wide properties (chapter/name/mission metadata). Loaded from `DATA_PATH + directory + "map_properties.tmx"` (DATA_PATH comes from the current language).
- Tile size at runtime is 48px (`TILE_SIZE`). TMX object coordinates are multiplied by 1.5 to reach 48px (assumes TMX authored at 32px tiles). Positions are then offset to center the map on the 22x14 grid (`map["x"]`, `map["y"]`).

## Required Tile Layers in `map.tmx`
- `ground` (tile layer): drawn as-is; tiles are scaled to 48x48.
- `obstacles` (tile layer): every non-void tile becomes an `Obstacle`. Tiles with property `type = "void"` are skipped.

## Required Object Layers in `map.tmx`
### Layer: `dynamic_data`
Objects are read by `type`:
- `placement`: player starting positions. No extra properties.
- `foe`: properties
  - `level` (int, required)
  - `strategy` (str, optional)
  - `number_items` (int, optional). For each `index` in range, expect `loot_item_{index}_name`.
  - `mission_target` (str, optional mission id)
  - `name` (object name) links to foe definition in XML.
- `ally`: `name` links to ally definition in XML.
- `objective`: properties
  - `mission` (str, required mission id)
  - `walkable` (bool, required)
  - `name` is the objective id.
- `chest`: properties
  - `content_possibilities` (int, required)
  - For each `index` in range: `item_{index}_name` (str), `item_{index}_probability` (float)
  - `closed_sprite` (str, required), `opened_sprite` (str, required)
  - Object image is the chest sprite on the map.
- `building`: properties
  - `sprite_link` (str, required)
  - `house_dialogs` (csv, optional) → dialog files `house_dialog_{id}.txt`
  - `gold` (int, optional), `items` (str item id, optional)
  - `kind` (str, optional). If `shop`:
    - `number_items` (int, required)
    - For each `index`: `item_{index}_name` (str), `item_{index}_quantity` (int)
    - `money` (int, optional, default 500)
  - Object image is used as the in-map sprite.
- `door`: properties
  - `sprite_link` (str, required)
  - Object image is used as the in-map sprite.
- `fountain`: `name` links to fountain definition in XML.
- `portal`: loader stub exists but is not implemented; current TMX content should avoid relying on it until implemented.
- `breakable`: loader stub exists but is not implemented.

### Layer: `events`
Each object yields an entry keyed by `type` in the events dict:
- Properties
  - `dialogs` (csv of dialog ids) → files `dialog_{id}.txt`
  - `new_players` (csv of player ids) → players spawned at the event object position
- Positions are also pulled through `_get_object_position` (same scaling and gap handling).

## Map-Wide Properties in `map_properties.tmx`
- `chapter_id` (int, required)
- `level_name` (str, required)
- `main_mission_type` (enum name from `MissionType`: POSITION, TOUCH_POSITION, KILL_TARGETS, etc., required)
- `main_mission_description` (str, required)
- Optional: `main_mission_turns` (int), `main_mission_number_players` (int)
- Optional: `secondary_missions` (csv of mission ids). For each mission id `X` the loader expects:
  - `X_mission_type` (enum name, required)
  - `X_mission_description` (str, required)
  - Optional: `X_mission_turns` (int)
  - Optional: `X_mission_number_players` (int)
  - Optional: `X_mission_gold_reward` (int). Item rewards are TODO in loader.
- Mission-objective linking:
  - POSITION/TOUCH_POSITION missions read `objective` objects where `mission` == mission id.
  - KILL_TARGETS missions read foes with `mission_target` == mission id.

## Position Math (important for editor fidelity)
- TMX object coords (x,y) are multiplied by 1.5 to convert 32px authored tiles to 48px runtime tiles.
- Map is centered on a 22x14 grid: runtime adds `map["x"]`, `map["y"]` computed from TMX dimensions and `TILE_SIZE`.
- For authoring with 48px tiles directly, you would remove the 1.5 factor in the loader or ensure the editor writes coordinates compatible with the current 1.5 scaling.

## Known Loader Gaps (risks for editor)
- `portal` and `breakable` object loading is unimplemented.
- No validation: missing properties or bad enum values will raise at runtime without clear user feedback.
- Missions: item rewards for secondary missions are TODO.
- Positions assume TMX is authored at 32px tiles; diverging from that requires changing `_get_object_position`.
