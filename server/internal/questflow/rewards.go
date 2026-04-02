package questflow

import (
	"fmt"
	"log"

	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/store"
)

func (e *Engine) isQuestCleared(user *store.UserState, questId int32) bool {
	quest, ok := user.Quests[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for isQuestCleared", questId))
	}
	return quest.QuestStateType == model.UserQuestStateTypeCleared
}

func appendMissionRewards(dst []RewardGrant, src []missionReward) []RewardGrant {
	for _, r := range src {
		dst = append(dst, RewardGrant{
			PossessionType: r.PossessionType,
			PossessionId:   r.PossessionId,
			Count:          r.Count,
		})
	}
	return dst
}

func (e *Engine) firstClearRewardGroupId(user *store.UserState, questMeta quest) int32 {
	rewardGroupId := questMeta.QuestFirstClearRewardGroupId
	for _, switchRow := range e.firstClearRewardSwitchesByQuestId[questMeta.QuestId] {
		if e.isQuestCleared(user, switchRow.SwitchConditionClearQuestId) {
			rewardGroupId = switchRow.QuestFirstClearRewardGroupId
			break
		}
	}
	return rewardGroupId
}

func (e *Engine) evaluateFinishOutcome(user *store.UserState, questId int32) FinishOutcome {
	outcome := FinishOutcome{}
	quest, ok := user.Quests[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for evaluateFinishOutcome", questId))
	}
	questMeta, ok := e.questById[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for evaluateFinishOutcome", questId))
	}

	if !quest.IsRewardGranted {
		rewardGroupId := e.firstClearRewardGroupId(user, questMeta)
		for _, reward := range e.firstClearRewardsByGroupId[rewardGroupId] {
			outcome.FirstClearRewards = append(outcome.FirstClearRewards, RewardGrant{
				PossessionType: reward.PossessionType,
				PossessionId:   reward.PossessionId,
				Count:          reward.Count,
			})
		}
	}

	newlyClearedCount := 0
	totalNon9999 := 0
	for _, questMissionId := range e.missionIdsByQuestId[questId] {
		missionMaster, ok := e.missionById[questMissionId]
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
				e.missionRewardsByMissionId[missionMaster.QuestMissionRewardId],
			)
		}
	}

	alreadyClearedCount := totalNon9999 - newlyClearedCount
	allWillBeClear := totalNon9999 > 0 && (alreadyClearedCount+newlyClearedCount) == totalNon9999
	if allWillBeClear {
		for _, questMissionId := range e.missionIdsByQuestId[questId] {
			missionMaster, ok := e.missionById[questMissionId]
			if !ok || missionMaster.QuestMissionConditionType != model.QuestMissionConditionTypeComplete {
				continue
			}
			key := store.QuestMissionKey{QuestId: questId, QuestMissionId: questMissionId}
			if !user.QuestMissions[key].IsClear {
				outcome.MissionClearCompleteRewards = appendMissionRewards(
					outcome.MissionClearCompleteRewards,
					e.missionRewardsByMissionId[missionMaster.QuestMissionRewardId],
				)
				outcome.BigWinClearedQuestMissionIds = append(outcome.BigWinClearedQuestMissionIds, questMissionId)
			}
		}
		outcome.IsBigWin = len(outcome.BigWinClearedQuestMissionIds) > 0
	}

	if questMeta.QuestPickupRewardGroupId != 0 {
		for _, dropId := range e.pickupRewardIdsByGroupId[questMeta.QuestPickupRewardGroupId] {
			if bdr, ok := e.battleDropRewardById[dropId]; ok {
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

func levelFromExp(exp int32, thresholds []int32) int32 {
	level := int32(1)
	for lvl := 1; lvl < len(thresholds); lvl++ {
		if exp >= thresholds[lvl] {
			level = int32(lvl)
		} else {
			break
		}
	}
	return level
}

func (e *Engine) applyExpRewards(user *store.UserState, questId int32, nowMillis int64) {
	questMeta, ok := e.questById[questId]
	if !ok {
		return
	}

	oldLevel := user.Status.Level
	user.Status.Exp += questMeta.UserExp
	user.Status.Level = levelFromExp(user.Status.Exp, e.userExpThresholds)
	log.Printf("[applyExpRewards] questId=%d user: +%d exp -> total=%d level=%d", questId, questMeta.UserExp, user.Status.Exp, user.Status.Level)

	if user.Status.Level > oldLevel {
		if maxStamina, ok := e.maxStaminaByLevel[user.Status.Level]; ok {
			store.ReplenishStamina(user, maxStamina*1000, nowMillis)
		}
	}

	if e.rentalQuestIds[questId] {
		log.Printf("[applyExpRewards] questId=%d skipping character/costume exp (rental deck)", questId)
		return
	}

	deckCostumeUuids, deckCharacterIds := e.resolveDeckUnits(user, questId)
	if deckCostumeUuids == nil {
		log.Printf("[applyExpRewards] questId=%d skipping character/costume exp (deck not resolved)", questId)
		return
	}

	if questMeta.CharacterExp != 0 {
		for id := range deckCharacterIds {
			row := user.Characters[id]
			row.Exp += questMeta.CharacterExp
			row.Level = levelFromExp(row.Exp, e.characterExpThresholds)
			user.Characters[id] = row
			log.Printf("[applyExpRewards] questId=%d character=%d: +%d exp -> total=%d level=%d", questId, id, questMeta.CharacterExp, row.Exp, row.Level)
		}
	}

	if questMeta.CostumeExp != 0 {
		for key := range deckCostumeUuids {
			row := user.Costumes[key]
			row.Exp += questMeta.CostumeExp
			cm, ok := e.costumeById[row.CostumeId]
			if ok {
				if thresholds, ok := e.costumeExpByRarity[cm.RarityType]; ok {
					row.Level = levelFromExp(row.Exp, thresholds)
				}
			}
			user.Costumes[key] = row
			log.Printf("[applyExpRewards] questId=%d costume=%d (key=%s): +%d exp -> total=%d level=%d", questId, row.CostumeId, key, questMeta.CostumeExp, row.Exp, row.Level)
		}
	}
}

func (e *Engine) resolveDeckUnits(user *store.UserState, questId int32) (costumeUuids map[string]bool, characterIds map[int32]bool) {
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
			if cm, ok := e.costumeById[costume.CostumeId]; ok {
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

func (e *Engine) applyQuestRewards(user *store.UserState, questId int32, nowMillis int64) {
	questMeta, ok := e.questById[questId]
	if !ok {
		return
	}

	e.applyExpRewards(user, questId, nowMillis)

	if questMeta.Gold != 0 {
		user.ConsumableItems[goldConsumableItemId] += questMeta.Gold
		log.Printf("[applyQuestRewards] questId=%d gold: +%d -> total=%d", questId, questMeta.Gold, user.ConsumableItems[goldConsumableItemId])
	}

	rewardGroupId := e.firstClearRewardGroupId(user, questMeta)
	for _, reward := range e.firstClearRewardsByGroupId[rewardGroupId] {
		e.applyRewardPossession(user, reward.PossessionType, reward.PossessionId, reward.Count, nowMillis)
	}
}

func (e *Engine) applyRewardPossession(user *store.UserState, possType model.PossessionType, possId, count int32, nowMillis int64) {
	switch possType {
	case model.PossessionTypeFreeGem:
		user.Gem.FreeGem += count
	case model.PossessionTypePaidGem:
		user.Gem.PaidGem += count
	case model.PossessionTypeCostume:
		e.grantCostume(user, possId, nowMillis)
	case model.PossessionTypeWeapon:
		e.grantWeapon(user, possId, nowMillis)
	case model.PossessionTypeCompanion:
		e.grantCompanion(user, possId, nowMillis)
	case model.PossessionTypeParts:
		e.grantParts(user, possId, nowMillis)
	case model.PossessionTypeCostumeEnhanced:
		e.grantCostume(user, possId, nowMillis)
	case model.PossessionTypeMaterial, model.PossessionTypeConsumableItem, model.PossessionTypeImportantItem:
		store.GrantPossession(user, possType, possId, count)
	default:
		log.Printf("[Engine] unsupported reward possession: type=%d id=%d count=%d", possType, possId, count)
	}
}

func (e *Engine) grantCostume(user *store.UserState, costumeId int32, nowMillis int64) {
	for _, row := range user.Costumes {
		if row.CostumeId == costumeId {
			return
		}
	}
	if cm, ok := e.costumeById[costumeId]; ok {
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

func (e *Engine) grantWeapon(user *store.UserState, weaponId int32, nowMillis int64) {
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
	weapon, ok := e.weaponById[weaponId]
	if !ok {
		return
	}
	e.populateWeaponSkillsAbilities(user, key, weapon)
	if weapon.WeaponStoryReleaseConditionGroupId != 0 {
		for _, cond := range e.releaseConditionsByGroupId[weapon.WeaponStoryReleaseConditionGroupId] {
			if cond.WeaponStoryReleaseConditionType == model.WeaponStoryReleaseConditionTypeAcquisition {
				e.grantWeaponStoryUnlock(user, weaponId, cond.StoryIndex, nowMillis)
			}
		}
	}
}

func (e *Engine) populateWeaponSkillsAbilities(user *store.UserState, weaponUuid string, weapon weaponMaster) {
	if slots, ok := e.skillGroupSlots[weapon.WeaponSkillGroupId]; ok {
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
	if slots, ok := e.abilityGroupSlots[weapon.WeaponAbilityGroupId]; ok {
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

func (e *Engine) grantCompanion(user *store.UserState, companionId int32, nowMillis int64) {
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

func (e *Engine) grantParts(user *store.UserState, partsId int32, nowMillis int64) {
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

func (e *Engine) grantWeaponStoryUnlock(user *store.UserState, weaponId, storyIndex int32, nowMillis int64) {
	hasWeapon := false
	for _, row := range user.Weapons {
		if row.WeaponId == weaponId {
			hasWeapon = true
			break
		}
	}
	if !hasWeapon {
		log.Printf("[Engine] grantWeaponStoryUnlock: skipping weaponId=%d (weapon not in user.Weapons)", weaponId)
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

func (e *Engine) ApplyTutorialReward(user *store.UserState, tutorialType model.TutorialType, choiceId int32, nowMillis int64) []RewardGrant {
	switch tutorialType {
	case model.TutorialTypeCompanion:
		return e.applyCompanionTutorialReward(user, choiceId, nowMillis)
	default:
		return nil
	}
}

func (e *Engine) applyCompanionTutorialReward(user *store.UserState, choiceId int32, nowMillis int64) []RewardGrant {
	companionId, ok := tutorialCompanionChoices[choiceId]
	if !ok {
		log.Printf("[Engine] unknown companion tutorial choiceId=%d", choiceId)
		return nil
	}
	e.grantCompanion(user, companionId, nowMillis)
	return []RewardGrant{{
		PossessionType: model.PossessionTypeCompanion,
		PossessionId:   companionId,
		Count:          1,
	}}
}

func (e *Engine) BattleDropRewards(questId int32) []BattleDropInfo {
	return e.battleDropsByQuestId[questId]
}

func (e *Engine) grantWeaponStoryUnlocksForQuestScene(user *store.UserState, questId int32, resultType model.QuestResultType, nowMillis int64) {
	if resultType == model.QuestResultTypeHalfResult {
		questMeta, ok := e.questById[questId]
		if !ok {
			return
		}
		rewardGroupId := e.firstClearRewardGroupId(user, questMeta)
		for _, reward := range e.firstClearRewardsByGroupId[rewardGroupId] {
			if reward.PossessionType != model.PossessionTypeWeapon {
				continue
			}
			weaponId := reward.PossessionId
			weapon, ok := e.weaponById[weaponId]
			if !ok || weapon.WeaponStoryReleaseConditionGroupId == 0 {
				continue
			}
			groupId := weapon.WeaponStoryReleaseConditionGroupId
			for _, cond := range e.releaseConditionsByGroupId[groupId] {
				if cond.WeaponStoryReleaseConditionType == model.WeaponStoryReleaseConditionTypeAcquisition && cond.ConditionValue == 0 {
					e.grantWeaponStoryUnlock(user, weaponId, cond.StoryIndex, nowMillis)
				}
			}
		}
		return
	}
	if resultType == model.QuestResultTypeFullResult {
		for groupId, conditions := range e.releaseConditionsByGroupId {
			for _, cond := range conditions {
				if cond.WeaponStoryReleaseConditionType == model.WeaponStoryReleaseConditionTypeQuestClear && cond.ConditionValue == questId {
					for _, weaponId := range e.weaponIdsByReleaseConditionGroupId[groupId] {
						e.grantWeaponStoryUnlock(user, weaponId, cond.StoryIndex, nowMillis)
					}
					break
				}
			}
		}
	}
}
