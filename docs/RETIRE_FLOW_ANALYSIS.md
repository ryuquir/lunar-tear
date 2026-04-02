# Retire Flow Analysis

Source: `client/dump_output/dump.cs` (IL2CPP dump) and server code review.

This document captures what the client does when a player retires from a quest battle, reconstructed from IL2CPP dump symbols, field layouts, and async state machine structures.

## Enums

### BattleEndType (Dark.DataPrimitive, TypeDefIndex: 15322)

```
Unknown = 0
Win     = 1
Lose    = 2
Retire  = 3
```

### GameplayStoryType (Dark.StateMachine, TypeDefIndex: 12447)

```
Unknown         = 0
Main            = 1
Sub             = 2
Event           = 3
Pvp             = 4
Content         = 5
Extra           = 6
BigHunt         = 7
Portal          = 8
CharacterViewer = 9
SideStory       = 10
```

### QuestResultType (Dark.Generated.Type, TypeDefIndex: 12804)

```
UNKNOWN     = 0
NONE        = 1
HALF_RESULT = 2
FULL_RESULT = 3
```

### QuestStorySkipType (Dark.Generated.Type, TypeDefIndex: 12806)

```
UNKNOWN                          = 0
NOT_SKIPPED                      = 1
SKIP_PICTURE_BOOK_IN_MAIN_FLOW   = 2
SKIP_IN_MAINFLOW                 = 3
SKIP_BY_BATTLE_ONLY_IN_SUB_FLOW  = 4
```

### StoryEvent (Dark.StateMachine.Story, TypeDefIndex: 12582)

```
CompleteStory               = 1
PlayLastStory               = 2
PlayStory                   = 3
PlayNextChapter             = 4
ReplaceStory                = 5
RespawnStory                = 6
ReturnMainStory             = 7
UpdateSceneProgress         = 8
LiteUpdateSceneProgress     = 9
ShiftSideStory              = 10
NextStepInSideStoryProgress = 11
ResetSideStoryProgress      = 12
```

### StoryState (Dark.StateMachine.Story, TypeDefIndex: 12585)

```
Unknown = 0
Idle    = 1
Playing = 2
```

### Results / ResultField (Dark.StateMachine.Story)

`Results` is a struct wrapping `ResultField`:
```
ResultField.Success      = 0
ResultField.Failure      = 1
ResultField.NetworkError = 2
```

### Client-Side QuestStateType (on EntityIUserQuest)

The client uses integer values (no named enum found in dump):
```
0 = Unknown / not started
1 = Active (in progress)
2 = Cleared
```

The server model matches: `UserQuestStateTypeUnknown=0`, `Active=1`, `Cleared=2`.

## Client Retire Call Chain

Reconstructed from dump.cs class definitions, method signatures, and field relationships.

### Phase 1: Battle UI triggers retire

1. **`MenuDialogPresenter.OnRetire()`** (RVA: `0x2BC6880`)
   - Player taps Retire button in the battle pause menu.
   - This is an async method (`<OnRetire>d__10`, MoveNext RVA: `0x2BC6E34`).

2. **`KernelTurnBattle.RetireBattle()`** (RVA: `0x3280284`, static)
   - Static entry point that signals the battle system to retire.

### Phase 2: Battle system processes retire

3. **`BattleOrderConductorAction`** (TypeDefIndex: 25347)
   - Sets `_isRequestRetireBattle = true` (field offset `0x8A`).
   - `CheckRetire()` (RVA: `0x2A5F498`) checks `_isRequestRetireBattle` and transitions via `_isRetireRequested` NodeStateLink (offset `0x58`).

4. **`TurnBattleExecuteRetire`** (TypeDefIndex: 25476)
   - `OnStateBegin()` (RVA: `0x2C025A4`) starts the retire execution.
   - `OnStateUpdate()` (RVA: `0x2C025DC`) polls `_completeRetire` (offset `0x50`) and transitions via `_retire` NodeStateLink (offset `0x60`).

5. **`QuestSetupBattle.RetireBattle()`** (RVA: `0x33C3A98`)
   - Stores `BattleEndType.Retire` as the battle result.
   - Calls `StoreBattleResultContext(BattleNextTransition, BattleEndType.Retire)`.
   - Transitions via `_retire` NodeStateLink (offset `0x60`).

### Phase 3: Story/gameplay layer sets retire flags

6. **`Dark.Kernel.Story.set_IsRetire(true)`** (RVA: `0x2C543EC`, static, write-only)
   - No `get_IsRetire` on the static `Dark.Kernel.Story` class. Write-only setter.
   - This propagates to the `Story` FSM instance.

7. **`Story.set_IsRetire(true)`** on the FSM instance (RVA: `0x279CF28`)
   - Sets `<IsRetire>k__BackingField` at offset `0x101` on the Story instance.

8. **`KernelGameplay.set_IsInRetire(true)`** (RVA: `0x2ABFEA8`, static)
   - Static flag at field offset `0x4` (relative to static fields base).
   - `get_IsInRetire` RVA: `0x2AC53A0`.

### Phase 4: Gameplay dispatches result handling

9. **`Gameplay.PlayResultAsync(isRetired=true, isContentStory, questResultType, cxlToken)`** (RVA: `0x2765E78`)
   - Called with `isRetired=true` when the battle ends via retire.
   - Async state machine `<PlayResultAsync>d__307`.

10. **`Gameplay.ScreenOfReturnDestinationRetire(currentStoryType, nextScene)`** (RVA: `0x275B94C`)
    - Determines what screen to return to after a retire. Takes the current `GameplayStoryType` and a `SceneRequestReplace` reference. Returns bool.

### Phase 5: Story DoRetireAsync

11. **`Story.DoRetireAsync(cxlToken, isFromTitleForExtra=false)`** (RVA: `0x27A6B1C`)
    - Async state machine: `<DoRetireAsync>d__415`, MoveNext RVA: `0x30AE454`.
    - Local variables (from state machine struct):
      - `requestJumpMomScreen` (bool, offset `0x30`)
      - `prevStoryType` (GameplayStoryType, offset `0x34`)
      - `isExtraAndFromTitle` (bool, offset `0x38`)
    - Calls `NeedsJumpMomScreenForMainStory()` (RVA: `0x27A6BD8`) to decide post-retire navigation.
    - Then calls `FinishEachStoryTypeQuest(storyType, chapterId, questId, retiredQuest=true, annihilated=false, cxlToken)`.

### Phase 6: FinishEachStoryTypeQuest sends the Finish RPC

12. **`Story.FinishEachStoryTypeQuest(storyType, playedChapterId, playedQuestId, retiredQuest, annihilated, cxlToken)`** (RVA: `0x27A3698`)
    - Async state machine: `<FinishEachStoryTypeQuest>d__358`, MoveNext RVA: `0x30AF6E4`.
    - State machine awaiter fields reveal which RPCs it can call:
      - `UniTask.Awaiter<FinishMainQuestResponse>` at offset `0x40` (awaiter 1)
      - `UniTask.Awaiter<FinishEventQuestResponse>` at offset `0x50` (awaiter 2)
      - `UniTask.Awaiter<FinishBattleResponse>` at offset `0x60` (awaiter 3, PvP)
      - `UniTask.Awaiter` at offset `0x70` (awaiter 4, generic -- likely BigHunt/Extra which return void-like)
    - Dispatches based on `storyType`:
      - **Main (1) / Sub (2):** `SendFinishMainQuestAsync(retiredQuest, annihilated, playedQuestId, cxlToken)` (RVA: `0x27A18DC`)
      - **Event (3):** `SendFinishEventQuestAsync(retiredQuest, annihilated, playedChapterId, playedQuestId, cxlToken)` (RVA: `0x27A19F8`)
      - **Pvp (4):** `SendFinishPvpAsync(...)` (RVA: `0x27A3380`)
      - **Extra (6):** `SendFinishExtraAsync(retiredQuest, annihilated, cxlToken)` (RVA: `0x27A2D10`)
      - **BigHunt (7):** `SendFinishBigHuntAsync(retiredQuest, annihilated, cxlToken)` (RVA: `0x27A28C8`)
    - Stores the response in the corresponding Story field:
      - Main: `Story.MainQuestResult` (offset `0xC0`)
      - Event: `Story.EventQuestResult` (offset `0xC8`)
      - Extra: `Story.ExtraQuestResult` (offset `0xD8`)
      - BigHunt: `Story.BigHuntQuestResult` (offset `0xE8`)

### Phase 7: Scene transition

13. **`KernelGameplay.MoveToNextScene(isRetire=true)`** (RVA: `0x2AC9C00`, static)
    - Central dispatch for post-quest scene transitions. The `isRetire` param changes navigation.
    - Calls into `Dark.Kernel.Scene.MoveToNextScene(skipped, isRetire, isReplaySkipped)` (RVA: `0x2C52734`).

14. **`MainStoryHierarchy.GetRetireSceneIdInCurrentScenes()`** (RVA: `0x3080478`)
    - Returns the scene ID to navigate back to when retiring from a main story quest.
    - Uses the current story hierarchy to find the appropriate re-entry point.

### Parallel path: Static RetireStory entry point

**`Dark.Kernel.Story.RetireStory(cxlToken)`** (RVA: `0x2C57F48`, static)
- Async state machine: `<RetireStory>d__150`, MoveNext RVA: `0x2ABFBBC`.
- This is the static wrapper that external callers use. Internally it delegates to `Story.DoRetireAsync` on the current Story FSM instance.

## Story Instance Fields (retire-relevant)

All offsets relative to the `Dark.StateMachine.Story.Story` object (TypeDefIndex: 12528):

| Field | Offset | Type | Notes |
|-------|--------|------|-------|
| `LatestResult` | `0x50` | `Results` (struct) | Success/Failure/NetworkError |
| `CurrentGameplayStoryType` | `0x54` | `GameplayStoryType` (int) | Which quest type is active |
| `CurrentQuestId` | `0x68` | int | Current quest being played |
| `ClearedCurrentQuestId` | `0x6C` | bool | Whether current quest is cleared |
| `CurrentSceneId` | `0x70` | int | Current scene in quest |
| `HeadSceneId` | `0x74` | int | Furthest scene reached |
| `CurrentChapterId` | `0x64` | int | Current chapter |
| `PlayingQuest` | `0xB0` | bool | Whether a quest is actively playing |
| `InQuestLastScene` | `0xB5` | bool | Whether at the last scene of a quest |
| `IsVictory` | `0x100` | bool | Battle won |
| `IsRetire` | `0x101` | bool | Battle retired |
| `IsAnnihilated` | `0x102` | bool | Party wiped |
| `IsSceneSkip` | `0x103` | bool | Story skipped |
| `MainQuestResult` | `0xC0` | ptr | FinishMainQuestResponse |
| `EventQuestResult` | `0xC8` | ptr | FinishEventQuestResponse |
| `ExtraQuestResult` | `0xD8` | ptr | FinishExtraQuestResponse |
| `BigHuntQuestResult` | `0xE8` | ptr | FinishBigHuntQuestResponse |
| `CurrentBattleDropReward` | `0x108` | ptr | RepeatedField\<BattleDropReward\> |
| `CurrentBattleBinary` | `0x110` | ptr | byte[] |

## Story.UserData Transaction Payload

When `FinishEachStoryTypeQuest` completes, it creates a `UserData` transaction object (TypeDefIndex: 12587) with:

| Field | Offset | Type |
|-------|--------|------|
| `PlayedChapterId` | `0x10` | int |
| `PlayedQuestId` | `0x14` | int |
| `PlayedExtraQuestIndex` | `0x1C` | int |
| `RetiredQuest` | `0x20` | bool |
| `Annihilated` | `0x21` | bool |
| `GameplayStoryType` | `0x24` | GameplayStoryType |
| ... | ... | ... |

The `RetiredQuest` field at offset `0x20` is the bool that flows through the post-retire logic on the client side. It has only a getter (`get_RetiredQuest`, RVA: `0x30BC630`) -- set during construction.

## Proto Contract: What the Client Sends on Retire

### FinishMainQuestRequest (retire case)

```
questId     = <current quest id>
isRetired   = true
isMainFlow  = <depends on flow type>
isAnnihilated = false  (retire is not annihilation)
isAutoOrbit = false
storySkipType = <depends on skip state>
isReplayFlow = <depends on replay state>
vt          = ""
```

### FinishEventQuestRequest (retire case)

```
eventQuestChapterId = <current event chapter>
questId             = <current quest id>
isRetired           = true
isAnnihilated       = false
isAutoOrbit         = false
storySkipType       = <depends>
vt                  = ""
```

### FinishExtraQuestRequest (retire case)

```
questId       = <current extra quest id>
isRetired     = true
isAnnihilated = false
storySkipType = <depends>
vt            = ""
```

## Current Server Behavior vs Expected

### What the server currently does on `isRetired=true`

In `questflow/quest.go` `HandleQuestFinish`:
- Skips `applyQuestRewards` (correct)
- Skips `grantWeaponStoryUnlocksForQuestScene` (correct)
- Skips drop reward application (correct)
- Sets `QuestStateType = Cleared` (WRONG)
- Sets `ClearCount = 1` (WRONG)
- Sets `DailyClearCount = 1` (WRONG)
- Sets `LastClearDatetime = nowMillis` (WRONG)
- Resets `MainQuest.ProgressQuestSceneId = 0` (needs verification)
- Resets `MainQuest.ProgressHeadQuestSceneId = 0` (needs verification)
- Resets `MainQuest.ProgressQuestFlowType = 0` (needs verification)
- Sets `MainQuest.CurrentQuestFlowType = Unknown` (needs verification)
- Calls `clearQuestMissions` (WRONG)

In `questflow/event_quest.go` `HandleEventQuestFinish`:
- Same reward-skipping behavior (correct)
- Sets `QuestStateType = Cleared` (WRONG)
- Increments `ClearCount++` (WRONG)
- Increments `DailyClearCount++` (WRONG)
- Clears `EventQuest.CurrentQuestId = 0` etc. (needs verification)
- Calls `clearQuestMissions` (WRONG)

### What the server SHOULD do on `isRetired=true`

Retire means "abort the quest without clearing it." The expected behavior:
- **Do NOT** mark the quest as Cleared
- **Do NOT** increment clear counts
- **Do NOT** clear quest missions
- **Do NOT** grant any rewards
- The quest should return to its pre-start state OR remain active (needs disasm confirmation)
- Stamina consumed at `StartMainQuest` is likely NOT refunded (needs disasm confirmation)
- Main quest progress pointers should be handled appropriately for the return-to-menu flow

### What the client expects in the response

The client stores the `FinishMainQuestResponse` / `FinishEventQuestResponse` in `Story.MainQuestResult` / `Story.EventQuestResult` respectively. On retire, the response should have:
- Empty reward arrays (no drops, no first-clear, no mission rewards)
- `isBigWin = false`
- Empty `bigWinClearedQuestMissionIdList`
- A valid `diffUserData` that reflects the quest state correctly (NOT cleared)

## Disassembly Analysis (ARM64, frida/disasm_retire_flow.js)

All 6 methods disassembled at runtime from `libil2cpp.so`.

### 1. RetireStory MoveNext (0x2ABFBBC) — Static Entry Point

This is the static `Dark.Kernel.Story.RetireStory(cxlToken)` async state machine. Sequence:

1. Calls a helper at RVA `0x2ABFDAC` with `w0=0x100` — resolves the Gameplay singleton, traverses `[singleton]→[+0xB8]→[+0x30]→[+0x48]` and calls it with an input-disable flag. This disables player input during the retire animation.

2. Calls a helper at RVA `0x2ABFE3C` with `w0=0` — resolves the same singleton chain, writes `false` at offset `0x5C` on a nested object. This clears some gameplay state flag.

3. **`KernelGameplay.set_IsInRetire(true)`** — sets the static IsInRetire flag.

4. **`DKStory.set_IsRetire(true)`** — sets the static IsRetire flag, which propagates to the Story FSM instance field at offset `0x101`.

5. **`RequestUpdateForCurrentStory(StoryEvent.RespawnStory, cxlToken)`** (RVA `0x2C59DAC`) — passes `w0=6` which is `StoryEvent.RespawnStory`. This is the story event used for retire, NOT `CompleteStory(1)` or `ReturnMainStory(7)`. The `RespawnStory` event triggers the Story FSM to run the DoRetireAsync path.

6. Awaits completion, then enters state=-2 (done).

**Key insight:** The retire path uses `StoryEvent.RespawnStory = 6`. This is the signal to the Story FSM to enter the retire-specific async flow (DoRetireAsync).

### 2. DoRetireAsync MoveNext (0x30AE454) — Main Retire Orchestration

State machine with states: -1 (initial), 0 (first await continuation), 1 (second await continuation for Extra-from-title), -2 (completed).

**Initial state (-1):**

```
strb wzr, [x19, #0x30]           ; requestJumpMomScreen = false
ldrb w9, [x19, #0x20]            ; isFromTitleForExtra param
ldr  w8, [x20, #0x54]            ; CurrentGameplayStoryType from Story
cmp  w9, #0                      ; isFromTitleForExtra?
cset w9, ne
cmp  w8, #6                      ; storyType == Extra?
str  w8, [x19, #0x34]            ; prevStoryType = storyType
cset w8, eq
and  w8, w8, w9                  ; isExtraAndFromTitle = (storyType==Extra) && isFromTitleForExtra
strb w8, [x19, #0x38]
```

Then if `PlayingQuest` (0xB0) is true:

```
bl   NeedsJumpMomScreenForMainStory
and  w8, w0, #1
strb w8, [x19, #0x30]            ; requestJumpMomScreen = result

ldr  w1, [x20, #0x54]            ; arg: CurrentGameplayStoryType
ldp  w2, w3, [x20, #0x64]        ; arg: CurrentChapterId, CurrentQuestId
ldrb w4, [x20, #0x101]           ; arg: IsRetire (directly from Story field!)
ldrb w5, [x20, #0x102]           ; arg: IsAnnihilated (from Story field)
ldr  x6, [x19, #0x28]            ; arg: cxlToken
bl   FinishEachStoryTypeQuest     ; CALL
```

**Critical: `IsRetire` is read from Story+0x101 and passed directly as `retiredQuest` to `FinishEachStoryTypeQuest`.** No transformation or conditional logic.

If `PlayingQuest` is false (rare case — retire without active quest), skips directly to post-retire scene management.

**After first await (state 0):**

If `isExtraAndFromTitle`:
- Calls `ApplyNewestPlayingScene()` (RVA `0x27A4E88`)
- If it returns true, calls `FinishEachStoryTypeQuest` again (same args re-read from Story)
- This handles the case where Extra quests loaded from title need a second finish call

Then sets `PlayingQuest = false` via `ApplyCurrentPlayingQuest(false)` (RVA `0x279FD28`).

**Post-retire scene resolution (no branching on isRetire):**

The scene resolution is the same regardless of retire/victory — it determines where to navigate back to:

```
if isExtraAndFromTitle:
    if storyType==Extra && !isExtraAndFromTitle:
        ApplyNewestPlayingScene() → if false: ApplyPortalOrMainScene(false)
    else:
        if ExistSideStory(): ApplySideStory()
        elif ExistPortal(): ApplyPortal()
        else: ApplyHeadMainScene(skipReplayConfirmation=false)
```

**Finalization:**

```
strb #1, [x20, #0x149]           ; _playingQuestForAuto = true (marks story as auto-ready)
ldr  w21, [x20, #0x70]           ; CurrentSceneId
ldr  w20, [x20, #0x54]           ; CurrentGameplayStoryType
ldrb w22, [x19, #0x30]           ; requestJumpMomScreen
cset w2, ne                      ; w2 = requestJumpMomScreen ? 1 : 0
mov  w0, w21                     ; w0 = CurrentSceneId
mov  w1, w20                     ; w1 = storyType
bl   0x2AC9C7C                   ; MoveToNextScene(sceneId, storyType, requestJumpMomScreen)
```

**Note:** DoRetireAsync calls the 3-arg `MoveToNextScene(sceneId, storyType, requestJumpMomScreen)` overload at `0x2AC9C7C`, NOT the `MoveToNextScene(bool isRetire)` overload at `0x2AC9C00`. The scene navigation is based on the scene ID the story FSM determined, not on a simple isRetire flag.

### 3. FinishEachStoryTypeQuest MoveNext (0x30AF6E4) — RPC Dispatch

Uses a jump table indexed by `storyType - 1` (values 1–7 → indices 0–6). Transparent dispatch — no local side effects based on `retiredQuest`.

| storyType | Handler | RPC Called | retiredQuest passed? |
|-----------|---------|-----------|---------------------|
| 1 (Main) | `0x30AF830` | `SendFinishMainQuestAsync(retiredQuest, annihilated, questId, cxlToken)` | Yes |
| 2 (Sub) | `0x30AFAC4` | `SendFinishMainQuestAsync(retiredQuest, annihilated, questId, cxlToken)` | Yes (same as Main) |
| 3 (Event) | `0x30AF9B4` | `SendFinishEventQuestAsync(retiredQuest, annihilated, chapterId, questId, cxlToken)` | Yes |
| 4 (Pvp) | `0x30AFA40` | `SendFinishPvpAsync(opponentPlayerId, isVictory, cxlToken)` | No (uses IsVictory instead) |
| 5 (Content) | `0x30AF94C` | `SendFinishContentStoryAsync(sceneId, cxlToken)` | No (no retire concept) |
| 6 (Extra) | `0x30AFB4C` | `SendFinishExtraAsync(retiredQuest, IsAnnihilated, cxlToken)` | Yes |
| 7 (BigHunt) | `0x30AFBB8` | `SendFinishBigHuntAsync(retiredQuest, IsAnnihilated, cxlToken)` | Yes |

**Disasm confirmation for Main (storyType=1):**
```
ldrb w1, [x19, #0x28]            ; w1 = retiredQuest (from struct offset 0x28)
ldr  x4, [x19, #0x30]            ; x4 = cxlToken
ldr  w3, [x19, #0x2c]            ; w3 = playedQuestId
ldrb w2, [x19, #0x29]            ; w2 = annihilated
bl   SendFinishMainQuestAsync
```

**Disasm confirmation for Event (storyType=3):**
```
ldrb w1, [x19, #0x28]            ; retiredQuest
ldr  x5, [x19, #0x30]            ; cxlToken
ldr  w4, [x19, #0x2c]            ; playedQuestId
ldr  w3, [x19, #0x38]            ; playedChapterId (extra field for events)
ldrb w2, [x19, #0x29]            ; annihilated
bl   SendFinishEventQuestAsync
```

After each RPC await, the response is stored via the awaiter infrastructure. The state machine simply stores the awaiter, suspends, and upon resumption transitions to state=-2 (complete). **No post-RPC branching on retiredQuest.**

### 4. KernelGameplay.MoveToNextScene (0x2AC9C00) — Scene Transition

**Overload 1: `MoveToNextScene(bool isRetire)` at `0x2AC9C00`:**

```
; Resolves Gameplay singleton chain:
; singleton → [+0xB8] → [+0x30] → [+0x80] → Scene object
and  w2, w19, #1                  ; w2 = isRetire & 1
mov  w1, wzr                     ; w1 = skipped = false
mov  w3, wzr                     ; w3 = isReplaySkipped = false
b    Scene.MoveToNextScene        ; tail call: Scene.MoveToNextScene(scene, false, isRetire, false)
```

Simple delegation. The `isRetire` parameter becomes arg3 of `Scene.MoveToNextScene`.

**Overload 2: at `0x2AC9C7C` (called from DoRetireAsync):**

```
; w0=sceneId, w1=storyType, w2=requestJumpMomScreen
; Resolves same singleton chain
and  w3, w20, #1                  ; w3 = requestJumpMomScreen
mov  w2, w19                     ; w2 = storyType? (some param ordering)
mov  w1, w21                     ; w1 = sceneId
b    0x2C52160                   ; tail call into a different Scene method
```

This overload navigates to a specific scene ID rather than relying on the `isRetire` flag for navigation decisions. **DoRetireAsync uses this overload because it has already resolved the target scene.**

### 5. ScreenOfReturnDestinationRetire (0x275B94C) — Return Screen Logic

Parameters: `(GameplayStoryType currentStoryType, SceneRequestReplace nextScene)`.
Returns: `bool` (whether to use a specific return destination).

```
bl   KernelGameplay.get_StateStory  ; get current StateStory
cbz  x0, exit                      ; null → crash guard

; Load story hierarchy from StateStory+0x50
ldr  x21, [x0, #0x50]              ; x21 = current MainStoryHierarchy

bl   DKStory.ExistSideStory         ; static: does a side story exist?
tbz  w0, #0, check_main_flow       ; if no side story → check main flow

bl   DKStory.get_PrevChapterId      ; get previous chapter ID
cbz  x21, exit                     ; null hierarchy → crash guard
; x21 = hierarchy, w0 = prevChapterId
bl   QuestIdIncludedInSideStory     ; is prevChapterId in the side story?
tbz  w0, #0, check_main_flow       ; if not → check main flow
mov  w0, wzr                       ; return false (stay on current screen)
ret

check_main_flow:
bl   DKStory.InMainFlow             ; are we in main flow?
tbz  w0, #0, return_true           ; if NOT in main flow → return true

; In main flow: check if currentStoryType is Event (3) or BigHunt (7)
orr  w8, w20, #4                   ; currentStoryType | 4
cmp  w8, #7                        ; == 7? (matches storyType 3: 3|4=7)
b.ne check_next_scene              ; if not Event → check nextScene

return_true:
mov  w0, #1                        ; return true
ret

check_next_scene:
cbz  x19, exit                     ; null nextScene → crash guard
ldrb w0, [x19, #0x24]              ; return nextScene.someFlag (offset 0x24)
ret
```

**Summary:** Returns `true` (use retire return destination) when:
- NOT in main flow, OR
- In main flow but storyType is Event (3)
Returns `false` when a side story includes the previous chapter.
Falls back to a flag on `nextScene` otherwise.

### 6. GetRetireSceneIdInCurrentScenes (0x3080478) — Scene ID Computation

Iterates through scenes in the MainStoryHierarchy's scene list. Algorithm:

```
result = 0
for i = 0; i < scenes.Count; i++:
    scene = scenes[i]
    if scene.HasBattle():       // interface method index 5
        break                   // stop at the battle scene
    result = scene.GetSceneId() // interface method index 1
return result
```

**The retire scene ID is the last non-battle scene before the first battle scene in the current hierarchy.** This is the story scene the player was viewing before entering battle — the natural "go back to where you were before the fight" point.

## Confirmed Findings Summary

### 1. No stamina refund on retire

The entire retire flow (`RetireStory` → `DoRetireAsync` → `FinishEachStoryTypeQuest` → `Send*Async`) contains zero references to stamina. Stamina is consumed at `StartMainQuest` and is never refunded. **The server should NOT refund stamina on retire.**

### 2. retiredQuest is passed through transparently

The client reads `Story.IsRetire` (offset `0x101`) and passes it directly as `retiredQuest` to the Finish RPC. No local state changes are conditioned on this flag — it's purely a signal to the server.

### 3. The client applies whatever diffUserData the server sends

After the Finish RPC returns, the client stores the response and continues with post-retire scene navigation. The `diffUserData` in the response is applied to the client's local database. Whatever the server puts in the diff is what the client will believe.

### 4. Quest state must NOT become "Cleared" on retire

Since the client treats the diff literally, sending `QuestStateType=2 (Cleared)` on a retire makes the client think the quest is completed. The correct behavior is:
- Keep quest as `QuestStateType=1 (Active)` or remove it from the active quest list
- Do NOT increment ClearCount or DailyClearCount
- Do NOT set LastClearDatetime
- Do NOT trigger quest mission clears

### 5. Post-retire navigation is determined by the client, not the server

The client determines the return scene via `GetRetireSceneIdInCurrentScenes` (last non-battle scene) and navigates there. The server does not need to tell the client where to go. The server just needs to correctly update the quest progress pointers so the client can replay the quest later.

### 6. StoryEvent.RespawnStory (6) is the retire event

The static `RetireStory` uses `StoryEvent.RespawnStory = 6` to signal the Story FSM. This is distinct from `CompleteStory = 1` (victory) and `ReturnMainStory = 7`.

### 7. Both Main and Sub story types use SendFinishMainQuestAsync

The Sub story type (2) dispatches to the same `SendFinishMainQuestAsync` as Main (1). The server's `FinishMainQuest` handler must handle both.

## Server Fix Requirements (Confirmed)

### HandleQuestFinish when isRetired=true:

| Action | Current | Should Be |
|--------|---------|-----------|
| Skip rewards | Correct | Correct |
| Skip weapon story unlocks | Correct | Correct |
| Skip drop rewards | Correct | Correct |
| QuestStateType | Set to Cleared (2) | Keep as Active (1) or leave unchanged |
| ClearCount | Incremented | Do NOT increment |
| DailyClearCount | Incremented | Do NOT increment |
| LastClearDatetime | Updated | Do NOT update |
| clearQuestMissions | Called | Do NOT call |
| Stamina refund | Not done | Not done (correct) |
| Progress pointers | Reset to 0 | Reset to 0 (correct — quest is aborted) |

### HandleEventQuestFinish when isRetired=true:

Same fixes apply: do not mark as Cleared, do not increment counts, do not clear missions.

### diffUserData response for retire:

The response should contain:
- `EntityIUserQuest` with `QuestStateType=1` (Active), unchanged counts
- Main quest flow/progress status reflecting that no quest is actively playing
- Empty reward/drop arrays
- `isBigWin = false`
- Empty `bigWinClearedQuestMissionIdList`

## IUserQuest Table Shape (EntityIUserQuest)

Client-side field layout (TypeDefIndex: 11466):

| Key | Field | Type | Offset |
|-----|-------|------|--------|
| 0 | UserId | long | 0x10 |
| 1 | QuestId | int | 0x18 |
| 2 | QuestStateType | int | 0x1C |
| 3 | IsBattleOnly | bool | 0x20 |
| 4 | LatestStartDatetime | MPDateTime | 0x28 |
| 5 | ClearCount | int | 0x30 |
| 6 | DailyClearCount | int | 0x34 |
| 7 | LastClearDatetime | MPDateTime | 0x38 |
| 8 | ShortestClearFrames | int | 0x40 |
| 9 | LatestVersion | long | 0x48 |

Server mirror (`userdata.EntityIUserQuest`): matches the Key ordering exactly (Key 0..9).

## Phase 2: Black Screen Root Cause (Post-Retire Navigation)

### Problem
After FinishMainQuest(isRetired=true) returns OK, the client hits a black screen.
The DoRetireAsync flow completes correctly (scene 97/Main is sent via
SendSceneRequestReplace), but `EndEventMap.MoveNext` runs afterward and
corrupts the navigation state.

### Key disassembly findings

**ScreenOfReturnDestinationRetire** (RVA 0x275B94C):
```
ScreenOfReturnDestinationRetire(storyType, nextScene):
  if DKStory.ExistSideStory():        # reads IUserSideStoryQuestSceneProgressStatus
    if hierarchy.Match(prevChapterId):
      return false                     # side story match → no special return
  if !DKStory.InMainFlow():           # SubFlow returns false here
    return true                        # NOT in main flow → special return path
  if (storyType | 4) == 7:            # storyType == Event (3)
    return true
  return nextScene.RequestJumpMomScreen
```

For SubFlow retires: `DKStory.InMainFlow() → false` → always returns true.

**Story.ApplyNewestEventScene** (RVA 0x27A4DA4):
```
ApplyNewestEventScene():
  entity = ActivePlayerToEntityEventQuestStatus()   # RVA 0x2AC3550
  if entity == null: return false
  sceneId = entity.CurrentQuestSceneId              # offset +0x20
  return ApplyScene(sceneId, Event)                 # storyType=3 hardcoded
```

**Caller of ApplyScene(0, Event)**: LR = RVA 0x27A4E20, inside
`Story.ApplyNewestEventScene`. Confirmed by Frida hook with LR logging.

### Root cause

The server's `IUserEventQuestProgressStatus` projection always includes a
record (even when all fields are zero). The client interprets this as
"event quest exists but with sceneId=0". This non-null entity causes
`EndEventMap.MoveNext` to enter an event-quest-specific code path that
fails and corrupts the post-retire navigation state.

On the official server, when no event quest is active, the table is empty
(`[]`), so `ActivePlayerToEntityEventQuestStatus()` returns null, and the
state machine skips the event path entirely.

### Fix

`server/internal/userdata/proj_quest.go`: Return `"[]"` for
`IUserEventQuestProgressStatus` when `CurrentQuestId`, `CurrentQuestSceneId`,
and `CurrentEventQuestChapterId` are all zero (no active event quest).

### Entity layouts referenced

| Entity | Offset | Field |
|--------|--------|-------|
| EntityIUserEventQuestProgressStatus +0x10 | UserId | long |
| EntityIUserEventQuestProgressStatus +0x18 | CurrentEventQuestChapterId | int |
| EntityIUserEventQuestProgressStatus +0x1C | CurrentQuestId | int |
| EntityIUserEventQuestProgressStatus +0x20 | CurrentQuestSceneId | int |
| EntityIUserEventQuestProgressStatus +0x24 | HeadQuestSceneId | int |
| EntityIUserSideStoryQuestSceneProgressStatus +0x18 | CurrentSideStoryQuestId | int |
| EntityIUserSideStoryQuestSceneProgressStatus +0x1C | CurrentSideStoryQuestSceneId | int |
| SceneRequestReplace +0x10 | ReplaceSceneId | int |
| SceneRequestReplace +0x18 | StoryType | GameplayStoryType |
| SceneRequestReplace +0x24 | RequestJumpMomScreen | bool |

### RVA reference table (Phase 2)

| RVA | Symbol |
|-----|--------|
| 0x275B94C | Gameplay.ScreenOfReturnDestinationRetire |
| 0x27A4DA4 | Story.ApplyNewestEventScene |
| 0x27A4E88 | Story.ApplyNewestPlayingScene |
| 0x2AC3550 | ActivePlayerToEntityEventQuestStatus |
| 0x2ABC3A8 | ActivePlayerToEntitySideStoryQuestSceneProgressStatus |
| 0x2C58910 | DKStory.InMainFlow |
| 0x2C5878C | DKStory.ExistSideStory |
| 0x2C537F0 | DKStory.get_PrevChapterId |
| 0x2C58910 | DKStory.InMainFlow |
| 0x28CA94C | Gameplay.EndEventMap.MoveNext |

## Phase 3: Persistent Black Screen After Phantom Entity Fix

### Verification: Phase 2 fix is deployed and working

Server logs confirm the projection guard is active:
```
2026/04/01 12:47:49 [Projection] IUserEventQuestProgressStatus -> [] (no active event quest)
2026/04/01 12:48:32 [Projection] IUserEventQuestProgressStatus -> [] (no active event quest)
2026/04/01 12:48:32 <<< /apb.api.quest.QuestService/FinishMainQuest OK
```

Frida confirms every call to `ActivePlayerToEntityEventQuestStatus` returns NULL.
`ApplyScene(0, Event)` is **no longer called**. The phantom entity bug is fixed.

### New trace: Full EndEventMap flow after retire (hooks_endeventmap_trace.js)

14 methods instrumented. Below is the retire-critical subsequence.

**Pre-retire (normal scene progression):**
Scenes 96 -> 222004001 -> 97 progress via `UpdateMainQuestSceneProgress`. Each triggers:
`ApplyNewestEventScene -> NULL -> skip` then `ApplyNewestPlayingScene -> success`.
Three `EndEventMap.MoveNext` entries at `state=-1` (initial) with `isRetired=0`.

**DoRetireAsync (seq 60-72):**
```
#61 DoRetireAsync.MoveNext state=-1
#62 DoRetireAsync.MoveNext state=0   (after FinishMainQuest RPC returns)
#63 Story.ExistSideStory -> 0
#67 Story.ExistPortal -> 0
#69 ApplyHeadMainScene(skip=0)
#70 ApplyScene(sceneId=97, storyType=Main) -> 1
#72 ApplyHeadMainScene -> 1
```

DoRetireAsync then calls `RespawnStory(97, Main, jumpMom=1)` and
`SendSceneRequestReplace(97, retired=1, forced=1, Main, jumpMom=1)` (not hooked
in this script, confirmed from previous Phase 2 traces).

**EndEventMap.MoveNext at state=7 (seq 73-93) -- THE HANG:**
```
#73 EndEventMap.MoveNext ENTER state=7
     isRetired=1  nextSceneId=222005001  curStoryType=Sub
     questResult=3  reqReturnMain=0  gotoPortalCage=0
     prevStoryType=Unknown  isEventStory=0  isSubResult=0
#74 ScreenOfReturnDestRetire(storyType=Sub, nextScene=0x79e20a3960)
#75   Kernel.ExistSideStory -> 0
#81   InMainFlow -> 0          <-- SubFlow, so InMainFlow=false
#83 ScreenOfReturnDestRetire -> 1   <-- takes "special return" path
#84 InSideStory -> 0
#86 ApplyNewestEventScene -> NULL -> 0   <-- correctly, no phantom entity
#90 ApplyNewestPlayingScene -> ApplyScene(97, Sub) -> 1
#93 ApplyNewestPlayingScene -> 1
    *** NO FURTHER MOVENEXT CALLS -- STATE MACHINE IS HUNG ***
```

No further hooks fire after #93. The state machine entered an async await
that never completes. The client shows a black screen.

### Analysis of the hang

**Why `ScreenOfReturnDestRetire` returns 1:**
Our quest is SubFlow (`currentQuestFlowType=2`), so `InMainFlow()` returns false.
The function's logic (from Phase 2 disasm):
```
if ExistSideStory() && hierarchy matches prevChapter: return false
if !InMainFlow(): return true    <-- THIS PATH
if storyType == Event: return true
return nextScene.RequestJumpMomScreen
```
This would be the same on the official server for SubFlow quests.

**The wrapper function `ApplyNewestScene`** (RVA `0x27A4370`):
Caller LRs `0x27a4424` and `0x27a4444` confirm `ApplyNewestEventScene` and
`ApplyNewestPlayingScene` are called from `Story.ApplyNewestScene(bool omitSideStory)`,
which returns `FirstQuestStates` enum:
```
FirstQuestStates:
  NotPlaying = 0
  Playing    = 1
  Failure    = 2
```
Since `ApplyNewestPlayingScene -> true`, `ApplyNewestScene` returns `Playing` (1).

**EndEventMap state machine struct** (`Gameplay.<EndEventMap>d__144`):
```
offset  field
0x00    <>1__state (int)
0x08    <>t__builder (AsyncUniTaskMethodBuilder<int>)
0x20    <>4__this (Gameplay)
0x28    nextScene (SceneRequestReplace)
0x30    cxlToken (CancellationToken)
0x48    <stateEventMap>5__2 (StateEventMap)
0x50    <isRetired>5__3 (bool)
0x54    <nextSceneId>5__5 (int)
0x58    <currentGameplayStoryType>5__6 (GameplayStoryType)
0x5C    <inContentStory>5__7 (bool)
0x60    <questResultType>5__8 (QuestResultType)
0x64    <isRequestReturnMainStory>5__9 (bool)
0x68    <>u__1 -- UniTask.Awaiter (generic)
0x70    <isGotoPortalCage>5__10 (bool)
0x74    <playStoryId>5__11 (int)
0x78    <nextPicturebookScene>5__12 (IScene)
0x80    <prevStoryType>5__13 (GameplayStoryType)
0x84    <isCurrentEventStory>5__14 (bool)
0x85    <isSubQuestResult>5__15 (bool)
0x88    <>u__2 -- UniTask.Awaiter<SideStoryReturnType>
0x98    <playedStoryHierarchy>5__16 (IStoryHierarchy)
0xA0    <>u__3 -- UniTask.Awaiter<UpdateSceneProgressResult>
0xB0    <currentStoryHierarchy>5__17 (IStoryHierarchy)
0xB8    <>u__4 -- UniTask.Awaiter<QuestContinueConfirmationDialogPresenter>
```

Four possible awaiters. After `ScreenOfReturnDestRetire=1` and `ApplyNewestScene`
returning `Playing`, the state machine is awaiting one of:
- `<>u__1` (generic UniTask) -- scene transition/loading
- `<>u__3` (UpdateSceneProgressResult) -- scene progress RPC
- `<>u__4` (QuestContinueConfirmationDialogPresenter) -- dialog

**Server evidence against `<>u__3`:** No `UpdateMainQuestSceneProgress` RPC
appears in server logs after `FinishMainQuest`. Either the client never sends
it (stuck before that point), or it uses `<>u__1` or `<>u__4` instead.

**`UpdateSceneProgressResult` enum:**
```
Unknown      = 0
FinishedQuest = 1
```

**`NeedsNextPlayingQuest(bool playedMainStory, UpdateSceneProgressResult result)`**
-- used by EndEventMap to decide if another quest should play.

### Key observations

1. **The official server follows the same path** for SubFlow retires:
   `InMainFlow=false -> ScreenOfReturnDestRetire=1 -> ApplyNewestScene`.
   The special return path is BY DESIGN for SubFlow. The hang is NOT caused
   by taking the wrong branch.

2. **The hang is in what happens AFTER `ApplyNewestScene` returns `Playing`.**
   The state machine sets up an async operation (probably `UpdateSceneProgress`
   or a scene transition await) that never completes on our server.

3. **Story type conflict:** `DoRetireAsync` applies scene 97 as `Main` via
   `ApplyHeadMainScene`. Then `EndEventMap.MoveNext` overrides with
   `ApplyScene(97, Sub)` via `ApplyNewestPlayingScene`. The final active
   story type is `Sub`, not `Main`.

4. **`nextSceneId=222005001`** at state=7 entry -- this is the next scene
   from the quest progression (not the retire target). It may be used by
   the state machine for the `UpdateSceneProgress` call.

### Next investigation required

Disassemble `EndEventMap.MoveNext` (RVA `0x28CA94C`, ~13KB, ends at `0x28CDDC8`)
focusing on the state=7 switch case. Specifically find:
1. What code runs after `ApplyNewestScene` returns `Playing` (1)
2. Which awaiter is set up (`<>u__1`, `<>u__3`, or `<>u__4`)
3. What async operation is started (UpdateSceneProgress? dialog? scene load?)
4. Why that operation never completes

### RVA reference table (Phase 3 additions)

| RVA | Symbol |
|-----|--------|
| 0x27A4370 | Story.ApplyNewestScene(bool omitSideStory) -> FirstQuestStates |
| 0x27A4310 | Story.ApplyFirstScene() -> FirstQuestStates |
| 0x27A4F90 | Story.ApplyPortalOrMainScene(bool omitSideStory) -> FirstQuestStates |
| 0x27A44D8 | Story.IfNeedsApplyAutoPlaying() -> bool |
| 0x2AC0C34 | Story.UpdateSceneProgress.MoveNext (d__145) |
| 0x2C57BB4 | Story.UpdateSceneProgress(sceneId, cxlToken) -> UniTask\<UpdateSceneProgressResult\> |
| 0x2C57CB0 | Story.LiteUpdateSceneProgress(storyType, sceneId, cxlToken) -> UniTask |
| 0x279E734 | Story.ExistSideStory (instance) |
| 0x30AE454 | Story.DoRetireAsync.MoveNext (d__415) |
| 0x275B94C | Gameplay.ScreenOfReturnDestinationRetire |

---

## Phase 4 — Orphaned HeadQuestSceneId causing d__422 hang

### Summary

The Phase 3 fix (clearing `ProgressQuestSceneId`, `ProgressHeadQuestSceneId`,
`ProgressQuestFlowType`, `CurrentQuestFlowType`) successfully eliminates stale
SubFlow progress: `ApplyNewestPlayingScene -> 0` after retire. However, it
leaves `HeadQuestSceneId` and `CurrentQuestSceneId` set to the last sub-quest
scene (97), creating a new hang.

### Mechanism

After retire, EndEventMap state=7 with `isRetired=1`:

1. `ApplyHeadMainScene(skip=0)` reads `IUserMainQuestMainFlowStatus.headQuestSceneId=97`
   -> `ApplyScene(97, Main) -> 1` -> returns true
2. `ScreenOfReturnDestRetire(Sub) -> 1`
3. `ApplySceneIdForStoryHierarchy(Main, 97, updateChapter=1)` — sets story hierarchy
4. `Kernel.Story.NeedsUpdateSceneProgress() -> 1` — hierarchy changed, needs update
5. `UpdateSceneProgress(97)` starts d__145, which starts d__422
6. Inside d__422:
   - `SendUpdateSceneProgressAsync(d__325)` starts
   - `GetUpdateStoryType(97, 0) -> Sub (2)` — scene 97 IS a Sub scene (QuestId=28,
     `IsCountedAsQuest=true`, `IsBattleOnlyTarget=true`)
   - `NeedsUpdateSceneProgress(Sub, 97, 0) -> 0 (SKIP)` — Sub progress was cleared,
     nothing to send
   - d__422 continues: `ApplyNewestScene -> NotPlaying(0)`,
     `ApplySceneIdForStoryHierarchy(Main, 97, 0)`
   - d__145 resumes at state=0... **HANG** — no further hooks fire

### Root cause

`HandleMainQuestSceneProgress` unconditionally updates BOTH Progress fields
AND MainFlow fields (`CurrentQuestSceneId`, `HeadQuestSceneId`). The Phase 3
retire fix cleared the Progress fields but not the MainFlow fields, leaving an
inconsistent state:

- `IUserMainQuestProgressStatus`: `currentQuestSceneId=0`, `currentQuestFlowType=0` (cleared)
- `IUserMainQuestMainFlowStatus`: `headQuestSceneId=97`, `currentQuestSceneId=97` (stale)

The client enters d__422's "SKIP" code path (no Sub progress to send), which
hangs on one of its subsequent awaiters (`<>u__2` or `<>u__3`). This is a client
bug we cannot fix; we must prevent the client from entering this path.

### Server logs confirmation

Server logs from a retire session showed NO `UpdateMainQuestSceneProgress` or
`UpdateMainFlowSceneProgress` RPCs after `FinishMainQuest(isRetired=true)`.
This confirms the SKIP — no RPC is sent, the hang is purely client-side.

### Master data context

- Scene 97: QuestId=28, SortOrder=10307040, QuestSceneType=3 (battle),
  `IsMainFlowQuestTarget=true`, `IsBattleOnlyTarget=true`
- Quest 28: `IsRunInTheBackground=false`, `IsCountedAsQuest=true`
  -> `isMainQuestPlayable=true`
- Quest 28 route: `routeIdByQuestId[28] = 1` (via MainQuestSequenceId=4, Chapter 4)

### Fix applied

In `HandleQuestFinish`, also clear `CurrentQuestSceneId` and `HeadQuestSceneId`
on retire:

```go
user.MainQuest.CurrentQuestSceneId = 0
user.MainQuest.HeadQuestSceneId = 0
```

This makes `ApplyHeadMainScene` return false, preventing EndEventMap from
entering the broken UpdateSceneProgress chain.

### d__422 struct layout (for reference)

```
Story.<OnUpdateSceneProgress>d__422 : IAsyncStateMachine  (TypeDefIndex: 12579)
  <>1__state                          0x0   int32
  <>t__builder                        0x8   AsyncUniTaskMethodBuilder
  <>4__this                           0x18  Story
  userdata                            0x20  ITransactionUserData
  cxlToken                            0x28  CancellationToken
  <data>5__2                          0x30  UserData
  <prevGamePlayStoryType>5__3         0x38  GameplayStoryType (int32)
  <nextSceneId>5__4                   0x3C  int32
  <sw>5__5                            0x40  Stopwatch
  <>u__1                              0x48  UniTask.Awaiter<int>     — UpdateSceneProgress result
  <>u__2                              0x58  UniTask.Awaiter<bool>    — unknown (possibly hangs)
  <>u__3                              0x68  UniTask.Awaiter          — unknown (possibly hangs)
MoveNext RVA: 0x30B4B5C
```

### RVA reference table (Phase 4 additions)

| RVA | Symbol |
|-----|--------|
| 0x30B4B5C | Story.OnUpdateSceneProgress.MoveNext (d__422) |
| 0x27A1E94 | Story.GetUpdateStoryType(int sceneId, bool replayed) -> GameplayStoryType |
| 0x27A2614 | Story.NeedsUpdateSceneProgress(GameplayStoryType, int, bool) -> bool |
| 0x27A264C | Story.IsRequestMainFlow(bool isMainFlow) -> bool |
| 0x27A6EEC | Story.ApplySceneIdForStoryHierarchy(int sceneId) |
| 0x27A6F70 | Story.ApplySceneIdForStoryHierarchy(GameplayStoryType, int, UpdateChapterStatus) |
| 0x30BA89C | Story.SendUpdateSceneProgressAsync.MoveNext (d__325) |
| 0x30BB8A0 | Story.SendUpdateSceneProgressForMainAsync.MoveNext (d__327) |
| 0x30BBD2C | Story.SendUpdateSceneProgressForSubAsync.MoveNext (d__328) |
| 0x30BB310 | Story.SendUpdateSceneProgressForEventAsync.MoveNext (d__329) |
| 0x2C563AC | Kernel.Story.NeedsUpdateSceneProgress() static |
