package questflow

import (
	"fmt"
	"log"

	"lunar-tear/server/internal/gameutil"
	"lunar-tear/server/internal/masterdata"
	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/store"
)

func (h *QuestHandler) isQuestCleared(user *store.UserState, questId int32) bool {
	quest, ok := user.Quests[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for isQuestCleared", questId))
	}
	return quest.QuestStateType == model.UserQuestStateTypeCleared
}

func appendMissionRewards(dst []RewardGrant, src []masterdata.QuestMissionRewardRow) []RewardGrant {
	for _, r := range src {
		dst = append(dst, RewardGrant{
			PossessionType: r.PossessionType,
			PossessionId:   r.PossessionId,
			Count:          r.Count,
		})
	}
	return dst
}

func (h *QuestHandler) firstClearRewardGroupId(user *store.UserState, questMeta masterdata.QuestRow) int32 {
	rewardGroupId := questMeta.QuestFirstClearRewardGroupId
	for _, switchRow := range h.FirstClearRewardSwitchesByQuestId[questMeta.QuestId] {
		if h.isQuestCleared(user, switchRow.SwitchConditionClearQuestId) {
			rewardGroupId = switchRow.QuestFirstClearRewardGroupId
			break
		}
	}
	return rewardGroupId
}

func (h *QuestHandler) evaluateFinishOutcome(user *store.UserState, questId int32) FinishOutcome {
	outcome := FinishOutcome{}
	quest, ok := user.Quests[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for evaluateFinishOutcome", questId))
	}
	questMeta, ok := h.QuestById[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for evaluateFinishOutcome", questId))
	}

	if !quest.IsRewardGranted {
		rewardGroupId := h.firstClearRewardGroupId(user, questMeta)
		for _, reward := range h.FirstClearRewardsByGroupId[rewardGroupId] {
			outcome.FirstClearRewards = append(outcome.FirstClearRewards, RewardGrant{
				PossessionType: reward.PossessionType,
				PossessionId:   reward.PossessionId,
				Count:          reward.Count,
			})
		}
	}

	newlyClearedCount := 0
	totalNon9999 := 0
	for _, questMissionId := range h.MissionIdsByQuestId[questId] {
		missionMaster, ok := h.MissionById[questMissionId]
		if !ok || missionMaster.QuestMissionConditionType == model.QuestMissionConditionTypeComplete {
			continue
		}
		totalNon9999++

		key := store.QuestMissionKey{QuestId: questId, QuestMissionId: questMissionId}
		mission := user.QuestMissions[key]

		if !mission.IsClear {
			newlyClearedCount++
			outcome.MissionClearRewards = appendMissionRewards(
				outcome.MissionClearRewards,
				h.MissionRewardsByMissionId[missionMaster.QuestMissionRewardId],
			)
		}
	}

	alreadyClearedCount := totalNon9999 - newlyClearedCount
	allWillBeClear := totalNon9999 > 0 && (alreadyClearedCount+newlyClearedCount) == totalNon9999
	if allWillBeClear {
		for _, questMissionId := range h.MissionIdsByQuestId[questId] {
			missionMaster, ok := h.MissionById[questMissionId]
			if !ok || missionMaster.QuestMissionConditionType != model.QuestMissionConditionTypeComplete {
				continue
			}
			key := store.QuestMissionKey{QuestId: questId, QuestMissionId: questMissionId}
			if !user.QuestMissions[key].IsClear {
				outcome.MissionClearCompleteRewards = appendMissionRewards(
					outcome.MissionClearCompleteRewards,
					h.MissionRewardsByMissionId[missionMaster.QuestMissionRewardId],
				)
				outcome.BigWinClearedQuestMissionIds = append(outcome.BigWinClearedQuestMissionIds, questMissionId)
			}
		}
		outcome.IsBigWin = len(outcome.BigWinClearedQuestMissionIds) > 0
	}

	if questMeta.QuestPickupRewardGroupId != 0 {
		for _, dropId := range h.PickupRewardIdsByGroupId[questMeta.QuestPickupRewardGroupId] {
			if bdr, ok := h.BattleDropRewardById[dropId]; ok {
				outcome.DropRewards = append(outcome.DropRewards, RewardGrant{
					PossessionType: bdr.PossessionType,
					PossessionId:   bdr.PossessionId,
					Count:          bdr.Count,
				})
			}
		}
	}

	return outcome
}

func (h *QuestHandler) applyExpRewards(user *store.UserState, questId int32, nowMillis int64) {
	questMeta, ok := h.QuestById[questId]
	if !ok {
		return
	}

	oldLevel := user.Status.Level
	user.Status.Exp += questMeta.UserExp
	user.Status.Level, user.Status.Exp = gameutil.LevelAndCap(user.Status.Exp, h.UserExpThresholds)
	log.Printf("[applyExpRewards] questId=%d user: +%d exp -> total=%d level=%d", questId, questMeta.UserExp, user.Status.Exp, user.Status.Level)

	if user.Status.Level > oldLevel {
		if maxStamina, ok := h.MaxStaminaByLevel[user.Status.Level]; ok {
			store.ReplenishStamina(user, maxStamina*1000, nowMillis)
		}
	}

	if h.RentalQuestIds[questId] {
		log.Printf("[applyExpRewards] questId=%d skipping character/costume exp (rental deck)", questId)
		return
	}

	deckCostumeUuids, deckCharacterIds := h.resolveDeckUnits(user, questId)
	if deckCostumeUuids == nil {
		log.Printf("[applyExpRewards] questId=%d skipping character/costume exp (deck not resolved)", questId)
		return
	}

	if questMeta.CharacterExp != 0 {
		for id := range deckCharacterIds {
			row := user.Characters[id]
			row.Exp += questMeta.CharacterExp
			row.Level, row.Exp = gameutil.LevelAndCap(row.Exp, h.CharacterExpThresholds)
			user.Characters[id] = row
			log.Printf("[applyExpRewards] questId=%d character=%d: +%d exp -> total=%d level=%d", questId, id, questMeta.CharacterExp, row.Exp, row.Level)
		}
	}

	if questMeta.CostumeExp != 0 {
		for key := range deckCostumeUuids {
			row := user.Costumes[key]
			cm, ok := h.CostumeById[row.CostumeId]
			if !ok {
				continue
			}
			if maxLevelFunc, hasMax := h.CostumeMaxLevelByRarity[cm.RarityType]; hasMax {
				maxLevel := maxLevelFunc.Evaluate(row.LimitBreakCount)
				if row.Level >= maxLevel {
					log.Printf("[applyExpRewards] questId=%d costume=%d (key=%s): at max level %d, skipping", questId, row.CostumeId, key, row.Level)
					continue
				}
			}
			row.Exp += questMeta.CostumeExp
			if thresholds, ok := h.CostumeExpByRarity[cm.RarityType]; ok {
				row.Level, row.Exp = gameutil.LevelAndCap(row.Exp, thresholds)
				if maxLevelFunc, hasMax := h.CostumeMaxLevelByRarity[cm.RarityType]; hasMax {
					maxLevel := maxLevelFunc.Evaluate(row.LimitBreakCount)
					if row.Level > maxLevel && int(maxLevel) < len(thresholds) {
						row.Level = maxLevel
						row.Exp = thresholds[maxLevel]
					}
				}
			}
			user.Costumes[key] = row
			log.Printf("[applyExpRewards] questId=%d costume=%d (key=%s): +%d exp -> total=%d level=%d", questId, row.CostumeId, key, questMeta.CostumeExp, row.Exp, row.Level)
		}
	}
}

func (h *QuestHandler) resolveDeckUnits(user *store.UserState, questId int32) (costumeUuids map[string]bool, characterIds map[int32]bool) {
	dn := user.Quests[questId].UserDeckNumber
	if dn == 0 {
		return nil, nil
	}
	deck, ok := user.Decks[store.DeckKey{DeckType: model.DeckTypeQuest, UserDeckNumber: dn}]
	if !ok {
		return nil, nil
	}

	costumeUuids = make(map[string]bool)
	characterIds = make(map[int32]bool)
	for _, dcUuid := range []string{deck.UserDeckCharacterUuid01, deck.UserDeckCharacterUuid02, deck.UserDeckCharacterUuid03} {
		if dcUuid == "" {
			continue
		}
		dc, ok := user.DeckCharacters[dcUuid]
		if !ok || dc.UserCostumeUuid == "" {
			continue
		}
		costumeUuids[dc.UserCostumeUuid] = true
		if costume, ok := user.Costumes[dc.UserCostumeUuid]; ok {
			if cm, ok := h.CostumeById[costume.CostumeId]; ok {
				characterIds[cm.CharacterId] = true
			}
		}
	}

	if len(costumeUuids) == 0 {
		return nil, nil
	}
	return costumeUuids, characterIds
}

const goldConsumableItemId int32 = 1

func (h *QuestHandler) applyQuestRewards(user *store.UserState, questId int32, nowMillis int64) {
	questMeta, ok := h.QuestById[questId]
	if !ok {
		return
	}

	h.applyExpRewards(user, questId, nowMillis)

	if questMeta.Gold != 0 {
		user.ConsumableItems[goldConsumableItemId] += questMeta.Gold
		log.Printf("[applyQuestRewards] questId=%d gold: +%d -> total=%d", questId, questMeta.Gold, user.ConsumableItems[goldConsumableItemId])
	}

	rewardGroupId := h.firstClearRewardGroupId(user, questMeta)
	for _, reward := range h.FirstClearRewardsByGroupId[rewardGroupId] {
		h.applyRewardPossession(user, reward.PossessionType, reward.PossessionId, reward.Count, nowMillis)
	}
}

func (h *QuestHandler) applyRewardPossession(user *store.UserState, possType model.PossessionType, possId, count int32, nowMillis int64) {
	switch possType {
	case model.PossessionTypeFreeGem:
		user.Gem.FreeGem += count
	case model.PossessionTypePaidGem:
		user.Gem.PaidGem += count
	case model.PossessionTypeCostume:
		h.grantCostume(user, possId, nowMillis)
	case model.PossessionTypeWeapon:
		h.grantWeapon(user, possId, nowMillis)
	case model.PossessionTypeCompanion:
		h.grantCompanion(user, possId, nowMillis)
	case model.PossessionTypeParts:
		h.grantParts(user, possId, nowMillis)
	case model.PossessionTypeCostumeEnhanced:
		h.grantCostume(user, possId, nowMillis)
	case model.PossessionTypeMaterial, model.PossessionTypeConsumableItem, model.PossessionTypeImportantItem:
		store.GrantPossession(user, possType, possId, count)
	default:
		log.Printf("[QuestHandler] unsupported reward possession: type=%d id=%d count=%d", possType, possId, count)
	}
}

func (h *QuestHandler) grantCostume(user *store.UserState, costumeId int32, nowMillis int64) {
	for _, row := range user.Costumes {
		if row.CostumeId == costumeId {
			return
		}
	}
	if cm, ok := h.CostumeById[costumeId]; ok {
		if _, exists := user.Characters[cm.CharacterId]; !exists {
			user.Characters[cm.CharacterId] = store.CharacterState{
				CharacterId: cm.CharacterId,
				Level:       1,
			}
		}
	}
	key := fmt.Sprintf("reward-costume-%d", costumeId)
	user.Costumes[key] = store.CostumeState{
		UserCostumeUuid:     key,
		CostumeId:           costumeId,
		Level:               1,
		HeadupDisplayViewId: 1,
		AcquisitionDatetime: nowMillis,
	}
	user.CostumeActiveSkills[key] = store.CostumeActiveSkillState{
		UserCostumeUuid:     key,
		Level:               1,
		AcquisitionDatetime: nowMillis,
	}
}

func (h *QuestHandler) grantWeapon(user *store.UserState, weaponId int32, nowMillis int64) {
	for _, row := range user.Weapons {
		if row.WeaponId == weaponId {
			return
		}
	}
	key := fmt.Sprintf("reward-weapon-%d", weaponId)
	user.Weapons[key] = store.WeaponState{
		UserWeaponUuid:      key,
		WeaponId:            weaponId,
		Level:               1,
		AcquisitionDatetime: nowMillis,
	}
	if _, exists := user.WeaponNotes[weaponId]; !exists {
		user.WeaponNotes[weaponId] = store.WeaponNoteState{
			WeaponId:                 weaponId,
			MaxLevel:                 1,
			MaxLimitBreakCount:       0,
			FirstAcquisitionDatetime: nowMillis,
			LatestVersion:            nowMillis,
		}
	}
	weapon, ok := h.WeaponById[weaponId]
	if !ok {
		return
	}
	h.populateWeaponSkillsAbilities(user, key, weapon)
	if weapon.WeaponStoryReleaseConditionGroupId != 0 {
		for _, cond := range h.ReleaseConditionsByGroupId[weapon.WeaponStoryReleaseConditionGroupId] {
			if cond.WeaponStoryReleaseConditionType == model.WeaponStoryReleaseConditionTypeAcquisition {
				h.grantWeaponStoryUnlock(user, weaponId, cond.StoryIndex, nowMillis)
			}
		}
	}
}

func (h *QuestHandler) populateWeaponSkillsAbilities(user *store.UserState, weaponUuid string, weapon masterdata.WeaponMasterRow) {
	if slots, ok := h.WeaponSkillSlots[weapon.WeaponSkillGroupId]; ok {
		skills := make([]store.WeaponSkillState, len(slots))
		for i, slot := range slots {
			skills[i] = store.WeaponSkillState{
				UserWeaponUuid: weaponUuid,
				SlotNumber:     slot,
				Level:          1,
			}
		}
		user.WeaponSkills[weaponUuid] = skills
	}
	if slots, ok := h.WeaponAbilitySlots[weapon.WeaponAbilityGroupId]; ok {
		abilities := make([]store.WeaponAbilityState, len(slots))
		for i, slot := range slots {
			abilities[i] = store.WeaponAbilityState{
				UserWeaponUuid: weaponUuid,
				SlotNumber:     slot,
				Level:          1,
			}
		}
		user.WeaponAbilities[weaponUuid] = abilities
	}
}

func (h *QuestHandler) grantCompanion(user *store.UserState, companionId int32, nowMillis int64) {
	for _, row := range user.Companions {
		if row.CompanionId == companionId {
			return
		}
	}
	key := fmt.Sprintf("reward-companion-%d", companionId)
	user.Companions[key] = store.CompanionState{
		UserCompanionUuid:   key,
		CompanionId:         companionId,
		Level:               1,
		HeadupDisplayViewId: 1,
		AcquisitionDatetime: nowMillis,
	}
}

func (h *QuestHandler) grantParts(user *store.UserState, partsId int32, nowMillis int64) {
	for _, row := range user.Parts {
		if row.PartsId == partsId {
			return
		}
	}
	key := fmt.Sprintf("reward-parts-%d", partsId)
	user.Parts[key] = store.PartsState{
		UserPartsUuid:       key,
		PartsId:             partsId,
		Level:               1,
		AcquisitionDatetime: nowMillis,
	}
}

func (h *QuestHandler) grantWeaponStoryUnlock(user *store.UserState, weaponId, storyIndex int32, nowMillis int64) {
	hasWeapon := false
	for _, row := range user.Weapons {
		if row.WeaponId == weaponId {
			hasWeapon = true
			break
		}
	}
	if !hasWeapon {
		log.Printf("[QuestHandler] grantWeaponStoryUnlock: skipping weaponId=%d (weapon not in user.Weapons)", weaponId)
		return
	}
	if user.WeaponStories == nil {
		user.WeaponStories = make(map[int32]store.WeaponStoryState)
	}
	cur := user.WeaponStories[weaponId]
	if storyIndex <= cur.ReleasedMaxStoryIndex {
		return
	}
	user.WeaponStories[weaponId] = store.WeaponStoryState{
		WeaponId:              weaponId,
		ReleasedMaxStoryIndex: storyIndex,
		LatestVersion:         nowMillis,
	}
}

var tutorialCompanionChoices = map[int32]int32{
	1: 2,  // bear + fire (Cat=1, Attr=2)
	2: 1,  // bear + wind (Cat=1, Attr=6)
	3: 7,  // doll + fire (Cat=3, Attr=2)
	4: 10, // doll + wind (Cat=3, Attr=6)
}

func (h *QuestHandler) ApplyTutorialReward(user *store.UserState, tutorialType model.TutorialType, choiceId int32, nowMillis int64) []RewardGrant {
	switch tutorialType {
	case model.TutorialTypeCompanion:
		return h.applyCompanionTutorialReward(user, choiceId, nowMillis)
	default:
		return nil
	}
}

func (h *QuestHandler) applyCompanionTutorialReward(user *store.UserState, choiceId int32, nowMillis int64) []RewardGrant {
	companionId, ok := tutorialCompanionChoices[choiceId]
	if !ok {
		log.Printf("[QuestHandler] unknown companion tutorial choiceId=%d", choiceId)
		return nil
	}
	h.grantCompanion(user, companionId, nowMillis)
	return []RewardGrant{{
		PossessionType: model.PossessionTypeCompanion,
		PossessionId:   companionId,
		Count:          1,
	}}
}

func (h *QuestHandler) BattleDropRewards(questId int32) []masterdata.BattleDropInfo {
	return h.BattleDropsByQuestId[questId]
}

func (h *QuestHandler) grantWeaponStoryUnlocksForQuestScene(user *store.UserState, questId int32, resultType model.QuestResultType, nowMillis int64) {
	if resultType == model.QuestResultTypeHalfResult {
		questMeta, ok := h.QuestById[questId]
		if !ok {
			return
		}
		rewardGroupId := h.firstClearRewardGroupId(user, questMeta)
		for _, reward := range h.FirstClearRewardsByGroupId[rewardGroupId] {
			if reward.PossessionType != model.PossessionTypeWeapon {
				continue
			}
			weaponId := reward.PossessionId
			weapon, ok := h.WeaponById[weaponId]
			if !ok || weapon.WeaponStoryReleaseConditionGroupId == 0 {
				continue
			}
			groupId := weapon.WeaponStoryReleaseConditionGroupId
			for _, cond := range h.ReleaseConditionsByGroupId[groupId] {
				if cond.WeaponStoryReleaseConditionType == model.WeaponStoryReleaseConditionTypeAcquisition && cond.ConditionValue == 0 {
					h.grantWeaponStoryUnlock(user, weaponId, cond.StoryIndex, nowMillis)
				}
			}
		}
		return
	}
	if resultType == model.QuestResultTypeFullResult {
		for groupId, conditions := range h.ReleaseConditionsByGroupId {
			for _, cond := range conditions {
				if cond.WeaponStoryReleaseConditionType == model.WeaponStoryReleaseConditionTypeQuestClear && cond.ConditionValue == questId {
					for _, weaponId := range h.WeaponIdsByReleaseConditionGroupId[groupId] {
						h.grantWeaponStoryUnlock(user, weaponId, cond.StoryIndex, nowMillis)
					}
					break
				}
			}
		}
	}
}
