def to_merge_format(string: str, replace_blank: bool = True):
    old = ('<', '>', 'lora:')
    for i in old:
        string = string.replace(i, '')
    if replace_blank:
        return string.replace(' ', ',')
    return string


if __name__ == '__main__':
    test_string = '<lora:submergedWater_1:0.2> <lora:shinyOiledSkin_v1:0.02> <lora:fashionGirl_v47:0.4> <lora:HinaIAmYoung22_zny10:0.003> <lora:breastinclassBetter_v141:0.3> <lora:lactation_v11:0.003> <lora:virginDestroyer_v10:0.02> <lora:reverseTranslucent_v10:0.02> <lora:munechiraLora_test004:0.02> <lora:downblouseForBoobs_v1:0.02> <lora:animeKisses_v1:0.02> <lora:povImminentPenetration_ipv1:0.02> <lora:ridingDildoSexActLora_v10:0.02> <lora:self_Breast_Suck:0.02> <lora:skirtliftTheAstonishing_skirtliftv1:0.02> <lora:beautifuleyeslikeness_halfBody:0.02> <lora:eulaHard:0.01> <lora:dishwasher1910Style_v10:0.02> <lora:artistKidmo_v10:0.02> <lora:styleJelly_v10:0.02> <lora:LoconLoraNardack_v10:0.02> <lora:stLouisLuxuriousWheels_v1:0.02> <lora:chilloutmixss_xss10:0.02> <lora:ArknightsSurtr_20:0.02> <lora:CostumeBondageOutfit_v1Beta:0.02> <lora:assOnGlassLora_v10:0.02> <lora:betterBodyBetterFace_mayukiV1:0.02> <lora:conceptPaintedClothes_v10:0.02> <lora:feetPoseAnime_v11:0.02> <lora:formidableAzurLaneSwimsuit_v104:0.02> <lora:gobinSlayerPriestess_priestess:0.02> <lora:guidedPenetrationTest_v10:0.02> <lora:incomingHug_v10:0.02> <lora:kashinoAzurLaneSwimsuit_kashinov108:0.02> <lora:murkysAfterSexLying_1:0.02> <lora:pecorine_v1:0.02> <lora:povSquattingCowgirlLora_pscowgirl:0.02> <lora:povWaistGrabConcept_v09:0.02> <lora:shirtTugPoseLORA_shirtTug:0.02> <lora:sideboob_v10:0.02> <lora:celestineLucullus_v15:0.02>'
    print(to_merge_format(test_string))
