def to_merge_format(string: str, replace_blank: bool = True):
    old = ('<', '>', 'lora:')
    for i in old:
        string = string.replace(i, '')
    if replace_blank:
        return string.replace(' ', ',')
    return string


if __name__ == '__main__':
    test_string = '<lora:yuiPrincessConnectCeremonial_v106:0.001> <lora:yorBriarRealistic_v10:0.001> <lora:uzakiTsukiUzakiChanWants_v10:0.001> <lora:upshirtUnderboob_v10:0.001> <lora:tweyenGranblue_v10:0.001> <lora:trueBuruma_v10:0.001> <lora:trappedInPhone_trappedInPhoneV1:0.001> <lora:traditionalMaidDress_traditionalMaidV1:0.001> <lora:teoshizuri_v2:0.001> <lora:sloppyFellatioLora_v10:0.001> <lora:signoraGenshinImpact_v25:0.001> <lora:shenheLoraCollection_shenheHard:0.001> <lora:seductressBodysuit_seductressv1:0.001> <lora:roundGlasses_v1a:0.001> <lora:oneBreastExposed_11:0.001> <lora:murkysButtjobLora_1:0.001> <lora:morganLeFayLora_v20:0.001> <lora:mix:0.001> <lora:inniesBetterVulva_v11:0.001> <lora:incomingHugKiss_v12:0.001> <lora:inPublic_v10:0.001> <lora:implacableAzurLane_v2:0.001> <lora:eyepatchBikini_v10:0.001> <lora:eulaRealisticGenshin_10:0.001> <lora:cosplayRevealing_v10:0.001> <lora:clothesSeeThrough_v10:0.001> <lora:bronyaZaychikHeartOfTheNight_v10:0.001> <lora:breastsOnTray_v10:0.001> <lora:bouncingBreasts_v1:0.001> <lora:bikiniJeans_v10:0.001> <lora:athenaGranblueFantasy_10:0.001> <lora:aliceNikke_v30:0.001> <lora:albionAzurLane_v2:0.001> <lora:accidentalExposure_v10:0.001> <lora:StandingDoggystyle_v11a:0.001> <lora:NIKKENIKKENIKKEHelm_v10:0.001> <lora:DDTiptoesStanding_ttfV3:0.001> <lora:DDDeepthroatFramesFor_4bjV1:0.001> <lora:CostumeStraitjacket_v1:0.001>'
    print(to_merge_format(test_string))
