// Generated from the checked-in aloha/Scene.h API and scene.sym offsets for Groove 1.0.0.
// DO NOT equate a command invocation with a confirmed input or judgement.
// A callback logs the observed invocation and forwards the exact typed parameters to the original.
// Pointer arguments are recorded as null/non-null markers, never memory addresses.

HkTrampoline gameplayHook1 = [](TrampolineStatic(), SceneBacteria* scene, SeqThread* thread, int a0, bool a1) -> void {
    recordGameplay(1, 0, a0, a1);
    orig(scene, thread, a0, a1);
};

HkTrampoline gameplayHook2 = [](TrampolineStatic(), SceneBacteria* scene, SeqThread* thread, int a0, bool a1) -> void {
    recordGameplay(2, 0, a0, a1);
    orig(scene, thread, a0, a1);
};

HkTrampoline gameplayHook3 = [](TrampolineStatic(), SceneBacteria* scene, SeqThread* thread) -> void {
    recordGameplay(3, 0);
    orig(scene, thread);
};

HkTrampoline gameplayHook4 = [](TrampolineStatic(), SceneBacteria* scene, SeqThread* thread, int a0) -> void {
    recordGameplay(4, 0, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook5 = [](TrampolineStatic(), SceneBirds* scene, SeqThread* thread, const char* a0) -> void {
    recordGameplay(5, 1, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook6 = [](TrampolineStatic(), SceneBrush* scene, SeqThread* thread, int a0, bool a1, bool a2, bool a3) -> void {
    recordGameplay(6, 2, a0, a1, a2, a3);
    orig(scene, thread, a0, a1, a2, a3);
};

HkTrampoline gameplayHook7 = [](TrampolineStatic(), SceneBrush* scene, SeqThread* thread, bool a0) -> void {
    recordGameplay(7, 2, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook8 = [](TrampolineStatic(), SceneBrush* scene, SeqThread* thread) -> void {
    recordGameplay(8, 2);
    orig(scene, thread);
};

HkTrampoline gameplayHook9 = [](TrampolineStatic(), SceneBrush* scene, SeqThread* thread) -> void {
    recordGameplay(9, 2);
    orig(scene, thread);
};

HkTrampoline gameplayHook10 = [](TrampolineStatic(), SceneCars* scene, SeqThread* thread, bool a0, bool a1) -> void {
    recordGameplay(10, 3, a0, a1);
    orig(scene, thread, a0, a1);
};

HkTrampoline gameplayHook11 = [](TrampolineStatic(), SceneCars* scene, SeqThread* thread, long a0, long a1, bool a2) -> void {
    recordGameplay(11, 3, a0, a1, a2);
    orig(scene, thread, a0, a1, a2);
};

HkTrampoline gameplayHook12 = [](TrampolineStatic(), SceneClap* scene, SeqThread* thread) -> void {
    recordGameplay(12, 4);
    orig(scene, thread);
};

HkTrampoline gameplayHook13 = [](TrampolineStatic(), SceneClap* scene, SeqThread* thread) -> void {
    recordGameplay(13, 4);
    orig(scene, thread);
};

HkTrampoline gameplayHook14 = [](TrampolineStatic(), SceneClap* scene, SeqThread* thread, int a0) -> void {
    recordGameplay(14, 4, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook15 = [](TrampolineStatic(), SceneClap* scene, SeqThread* thread) -> void {
    recordGameplay(15, 4);
    orig(scene, thread);
};

HkTrampoline gameplayHook16 = [](TrampolineStatic(), SceneClap* scene, SeqThread* thread) -> void {
    recordGameplay(16, 4);
    orig(scene, thread);
};

HkTrampoline gameplayHook17 = [](TrampolineStatic(), SceneClap* scene, SeqThread* thread) -> void {
    recordGameplay(17, 4);
    orig(scene, thread);
};

HkTrampoline gameplayHook18 = [](TrampolineStatic(), SceneClap* scene, SeqThread* thread) -> void {
    recordGameplay(18, 4);
    orig(scene, thread);
};

HkTrampoline gameplayHook19 = [](TrampolineStatic(), SceneCooking* scene, SeqThread* thread, int a0, int a1) -> void {
    recordGameplay(19, 5, a0, a1);
    orig(scene, thread, a0, a1);
};

HkTrampoline gameplayHook20 = [](TrampolineStatic(), SceneCooking* scene, SeqThread* thread, int a0, int a1, int a2, int a3) -> void {
    recordGameplay(20, 5, a0, a1, a2, a3);
    orig(scene, thread, a0, a1, a2, a3);
};

HkTrampoline gameplayHook21 = [](TrampolineStatic(), SceneCrab* scene, SeqThread* thread, int a0, int a1, int a2) -> void {
    recordGameplay(21, 6, a0, a1, a2);
    orig(scene, thread, a0, a1, a2);
};

HkTrampoline gameplayHook22 = [](TrampolineStatic(), SceneCrab* scene, SeqThread* thread, int a0, int a1, int a2) -> void {
    recordGameplay(22, 6, a0, a1, a2);
    orig(scene, thread, a0, a1, a2);
};

HkTrampoline gameplayHook23 = [](TrampolineStatic(), SceneCrab* scene, SeqThread* thread, int a0, int a1, int a2) -> void {
    recordGameplay(23, 6, a0, a1, a2);
    orig(scene, thread, a0, a1, a2);
};

HkTrampoline gameplayHook24 = [](TrampolineStatic(), SceneDancer* scene, SeqThread* thread, int a0, int a1, bool a2, bool a3) -> void {
    recordGameplay(24, 7, a0, a1, a2, a3);
    orig(scene, thread, a0, a1, a2, a3);
};

HkTrampoline gameplayHook25 = [](TrampolineStatic(), SceneDancer* scene, SeqThread* thread, int a0, int a1, bool a2) -> void {
    recordGameplay(25, 7, a0, a1, a2);
    orig(scene, thread, a0, a1, a2);
};

HkTrampoline gameplayHook26 = [](TrampolineStatic(), SceneDancer* scene, SeqThread* thread, bool a0) -> void {
    recordGameplay(26, 7, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook27 = [](TrampolineStatic(), SceneFlydisc* scene, SeqThread* thread, int a0, int a1, int a2, bool a3) -> void {
    recordGameplay(27, 8, a0, a1, a2, a3);
    orig(scene, thread, a0, a1, a2, a3);
};

HkTrampoline gameplayHook28 = [](TrampolineStatic(), SceneGrasp* scene, SeqThread* thread, int a0, bool a1) -> void {
    recordGameplay(28, 9, a0, a1);
    orig(scene, thread, a0, a1);
};

HkTrampoline gameplayHook29 = [](TrampolineStatic(), SceneGrasp* scene, SeqThread* thread) -> void {
    recordGameplay(29, 9);
    orig(scene, thread);
};

HkTrampoline gameplayHook30 = [](TrampolineStatic(), SceneGrasp* scene, SeqThread* thread, bool a0) -> void {
    recordGameplay(30, 9, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook31 = [](TrampolineStatic(), SceneGuardian* scene, SeqThread* thread, int a0, int a1) -> void {
    recordGameplay(31, 10, a0, a1);
    orig(scene, thread, a0, a1);
};

HkTrampoline gameplayHook32 = [](TrampolineStatic(), SceneGuardian* scene, SeqThread* thread, int a0, int a1) -> void {
    recordGameplay(32, 10, a0, a1);
    orig(scene, thread, a0, a1);
};

HkTrampoline gameplayHook33 = [](TrampolineStatic(), SceneGuardian* scene, SeqThread* thread, int a0, int a1) -> void {
    recordGameplay(33, 10, a0, a1);
    orig(scene, thread, a0, a1);
};

HkTrampoline gameplayHook34 = [](TrampolineStatic(), SceneHammer* scene, SeqThread* thread, int a0, bool a1, int a2) -> void {
    recordGameplay(34, 11, a0, a1, a2);
    orig(scene, thread, a0, a1, a2);
};

HkTrampoline gameplayHook35 = [](TrampolineStatic(), SceneHammer* scene, SeqThread* thread, int a0, bool a1, int a2) -> void {
    recordGameplay(35, 11, a0, a1, a2);
    orig(scene, thread, a0, a1, a2);
};

HkTrampoline gameplayHook36 = [](TrampolineStatic(), SceneHungry* scene, SeqThread* thread, int a0) -> void {
    recordGameplay(36, 12, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook37 = [](TrampolineStatic(), SceneHurdle* scene, SeqThread* thread, bool a0) -> void {
    recordGameplay(37, 13, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook38 = [](TrampolineStatic(), SceneHurdle* scene, SeqThread* thread) -> void {
    recordGameplay(38, 13);
    orig(scene, thread);
};

HkTrampoline gameplayHook39 = [](TrampolineStatic(), SceneInsect* scene, SeqThread* thread, int a0, int a1, int a2) -> void {
    recordGameplay(39, 14, a0, a1, a2);
    orig(scene, thread, a0, a1, a2);
};

HkTrampoline gameplayHook40 = [](TrampolineStatic(), SceneInsect* scene, SeqThread* thread, int a0, int a1, int a2) -> void {
    recordGameplay(40, 14, a0, a1, a2);
    orig(scene, thread, a0, a1, a2);
};

HkTrampoline gameplayHook41 = [](TrampolineStatic(), SceneInsect* scene, SeqThread* thread, int a0, int a1, int a2) -> void {
    recordGameplay(41, 14, a0, a1, a2);
    orig(scene, thread, a0, a1, a2);
};

HkTrampoline gameplayHook42 = [](TrampolineStatic(), SceneKaeru* scene, SeqThread* thread, int a0) -> void {
    recordGameplay(42, 15, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook43 = [](TrampolineStatic(), SceneKaeru* scene, SeqThread* thread, int a0) -> void {
    recordGameplay(43, 15, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook44 = [](TrampolineStatic(), SceneMoon* scene, SeqThread* thread, bool a0) -> void {
    recordGameplay(44, 16, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook45 = [](TrampolineStatic(), SceneMoon* scene, SeqThread* thread) -> void {
    recordGameplay(45, 16);
    orig(scene, thread);
};

HkTrampoline gameplayHook46 = [](TrampolineStatic(), SceneMoon* scene, SeqThread* thread, bool a0) -> void {
    recordGameplay(46, 16, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook47 = [](TrampolineStatic(), SceneParasol* scene, SeqThread* thread, int a0, int a1, int a2, int a3) -> void {
    recordGameplay(47, 17, a0, a1, a2, a3);
    orig(scene, thread, a0, a1, a2, a3);
};

HkTrampoline gameplayHook48 = [](TrampolineStatic(), SceneParasol* scene, SeqThread* thread, int a0, int a1) -> void {
    recordGameplay(48, 17, a0, a1);
    orig(scene, thread, a0, a1);
};

HkTrampoline gameplayHook49 = [](TrampolineStatic(), SceneParasol* scene, SeqThread* thread, int a0) -> void {
    recordGameplay(49, 17, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook50 = [](TrampolineStatic(), ScenePumpup* scene, SeqThread* thread, int a0, int a1) -> void {
    recordGameplay(50, 18, a0, a1);
    orig(scene, thread, a0, a1);
};

HkTrampoline gameplayHook51 = [](TrampolineStatic(), ScenePumpup* scene, SeqThread* thread, int a0, int a1) -> void {
    recordGameplay(51, 18, a0, a1);
    orig(scene, thread, a0, a1);
};

HkTrampoline gameplayHook52 = [](TrampolineStatic(), ScenePutilabo* scene, SeqThread* thread, int a0) -> void {
    recordGameplay(52, 19, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook53 = [](TrampolineStatic(), ScenePutilabo* scene, SeqThread* thread, int a0, int a1) -> void {
    recordGameplay(53, 19, a0, a1);
    orig(scene, thread, a0, a1);
};

HkTrampoline gameplayHook54 = [](TrampolineStatic(), SceneRing* scene, SeqThread* thread, int a0) -> void {
    record(HoopCalled, a0);
    recordGameplay(54, 20, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook55 = [](TrampolineStatic(), SceneRolling* scene, SeqThread* thread, int a0) -> void {
    recordGameplay(55, 21, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook56 = [](TrampolineStatic(), SceneRolling* scene, SeqThread* thread, int a0) -> void {
    recordGameplay(56, 21, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook57 = [](TrampolineStatic(), SceneRope* scene, SeqThread* thread, int a0, bool a1) -> void {
    recordGameplay(57, 22, a0, a1);
    orig(scene, thread, a0, a1);
};

HkTrampoline gameplayHook58 = [](TrampolineStatic(), SceneRope* scene, SeqThread* thread, int a0, bool a1, bool a2) -> void {
    recordGameplay(58, 22, a0, a1, a2);
    orig(scene, thread, a0, a1, a2);
};

HkTrampoline gameplayHook59 = [](TrampolineStatic(), SceneSamurai* scene, SeqThread* thread, long a0, long a1) -> void {
    recordGameplay(59, 23, a0, a1);
    orig(scene, thread, a0, a1);
};

HkTrampoline gameplayHook60 = [](TrampolineStatic(), SceneSamurai* scene, SeqThread* thread, long a0, long a1) -> void {
    recordGameplay(60, 23, a0, a1);
    orig(scene, thread, a0, a1);
};

HkTrampoline gameplayHook61 = [](TrampolineStatic(), SceneShinkai* scene, SeqThread* thread, long a0, const char* a1, const char* a2) -> void {
    recordGameplay(61, 30, a0, a1, a2);
    orig(scene, thread, a0, a1, a2);
};

HkTrampoline gameplayHook62 = [](TrampolineStatic(), SceneShinkai* scene, SeqThread* thread, long a0, const char* a1, const char* a2) -> void {
    recordGameplay(62, 30, a0, a1, a2);
    orig(scene, thread, a0, a1, a2);
};

HkTrampoline gameplayHook63 = [](TrampolineStatic(), SceneSoccer* scene, SeqThread* thread, int a0) -> void {
    recordGameplay(63, 24, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook64 = [](TrampolineStatic(), SceneSoccer* scene, SeqThread* thread, int a0) -> void {
    recordGameplay(64, 24, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook65 = [](TrampolineStatic(), SceneSoccer* scene, SeqThread* thread, int a0) -> void {
    recordGameplay(65, 24, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook66 = [](TrampolineStatic(), SceneSoftcatch* scene, SeqThread* thread, long a0, int a1) -> void {
    recordGameplay(66, 25, a0, a1);
    orig(scene, thread, a0, a1);
};

HkTrampoline gameplayHook67 = [](TrampolineStatic(), SceneTalk* scene, SeqThread* thread) -> void {
    recordGameplay(67, 26);
    orig(scene, thread);
};

HkTrampoline gameplayHook68 = [](TrampolineStatic(), SceneTalk* scene, SeqThread* thread) -> void {
    recordGameplay(68, 26);
    orig(scene, thread);
};

HkTrampoline gameplayHook69 = [](TrampolineStatic(), SceneTalk* scene, SeqThread* thread) -> void {
    recordGameplay(69, 26);
    orig(scene, thread);
};

HkTrampoline gameplayHook70 = [](TrampolineStatic(), SceneTheA* scene, SeqThread* thread, const char* a0, float a1, void* a2, const char* a3) -> void {
    recordGameplay(70, 27, a0, a1, a2, a3);
    orig(scene, thread, a0, a1, a2, a3);
};

HkTrampoline gameplayHook71 = [](TrampolineStatic(), SceneThunder* scene, SeqThread* thread, int a0, long a1) -> void {
    recordGameplay(71, 28, a0, a1);
    orig(scene, thread, a0, a1);
};

HkTrampoline gameplayHook72 = [](TrampolineStatic(), SceneThunder* scene, SeqThread* thread, long a0) -> void {
    recordGameplay(72, 28, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook73 = [](TrampolineStatic(), SceneThunder* scene, SeqThread* thread, int a0, long a1) -> void {
    recordGameplay(73, 28, a0, a1);
    orig(scene, thread, a0, a1);
};

HkTrampoline gameplayHook74 = [](TrampolineStatic(), SceneThunder* scene, SeqThread* thread, long a0) -> void {
    recordGameplay(74, 28, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook75 = [](TrampolineStatic(), SceneWiper* scene, SeqThread* thread) -> void {
    recordGameplay(75, 29);
    orig(scene, thread);
};

HkTrampoline gameplayHook76 = [](TrampolineStatic(), SceneWiper* scene, SeqThread* thread) -> void {
    recordGameplay(76, 29);
    orig(scene, thread);
};

HkTrampoline gameplayHook77 = [](TrampolineStatic(), SceneWiper* scene, SeqThread* thread) -> void {
    recordGameplay(77, 29);
    orig(scene, thread);
};

HkTrampoline gameplayHook78 = [](TrampolineStatic(), SceneWiper* scene, SeqThread* thread) -> void {
    recordGameplay(78, 29);
    orig(scene, thread);
};

HkTrampoline gameplayHook79 = [](TrampolineStatic(), SceneWiper* scene, SeqThread* thread, int a0) -> void {
    recordGameplay(79, 29, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook80 = [](TrampolineStatic(), SceneWiper* scene, SeqThread* thread, int a0) -> void {
    recordGameplay(80, 29, a0);
    orig(scene, thread, a0);
};

HkTrampoline gameplayHook81 = [](TrampolineStatic(), SceneSkater* scene, SeqThread* thread, int a0, int a1, char a2) -> void {
    recordGameplay(81, -1, a0, a1, a2);
    orig(scene, thread, a0, a1, a2);
};

HkTrampoline gameplayHook82 = [](TrampolineStatic(), SceneSkater* scene, SeqThread* thread, int a0, int a1) -> void {
    recordGameplay(82, -1, a0, a1);
    orig(scene, thread, a0, a1);
};

HkTrampoline gameplayHook83 = [](TrampolineStatic(), SceneSkater* scene, SeqThread* thread, int a0, int a1) -> void {
    recordGameplay(83, -1, a0, a1);
    orig(scene, thread, a0, a1);
};

HkTrampoline gameplayHook84 = [](TrampolineStatic(), SceneSkater* scene, SeqThread* thread, int a0, int a1) -> void {
    recordGameplay(84, -1, a0, a1);
    orig(scene, thread, a0, a1);
};

unsigned installGameplayHooks(const hk::ro::RoModule* module, unsigned& hoop) {
    unsigned count = 0;
    const auto attempt = [&](auto& hook, ptr offset, u32 word) {
        const bool installed = installChecked(module, hook, offset, word);
        count += installed;
        return installed;
    };
    attempt(gameplayHook1, 0x146120, 0xd10343ff);
    attempt(gameplayHook2, 0x146b50, 0xd10343ff);
    attempt(gameplayHook3, 0x147cd0, 0xd10343ff);
    attempt(gameplayHook4, 0x1473a0, 0xd10343ff);
    attempt(gameplayHook5, 0x14a3e0, 0xd10343ff);
    attempt(gameplayHook6, 0x15a560, 0xd10343ff);
    attempt(gameplayHook7, 0x15af40, 0xd10343ff);
    attempt(gameplayHook8, 0x15b2e0, 0xd10343ff);
    attempt(gameplayHook9, 0x15ab00, 0xd10343ff);
    attempt(gameplayHook10, 0x1601d0, 0xd102c3ff);
    attempt(gameplayHook11, 0x1608f0, 0xd102c3ff);
    attempt(gameplayHook12, 0x1646f0, 0xd10343ff);
    attempt(gameplayHook13, 0x164b70, 0xd10343ff);
    attempt(gameplayHook14, 0x1632d0, 0xd10343ff);
    attempt(gameplayHook15, 0x1634d0, 0x5287dc88);
    attempt(gameplayHook16, 0x163b30, 0xd10343ff);
    attempt(gameplayHook17, 0x1634f0, 0x5287dca8);
    attempt(gameplayHook18, 0x1642f0, 0xd10343ff);
    attempt(gameplayHook19, 0x178880, 0xd10343ff);
    attempt(gameplayHook20, 0x178dc0, 0xd10343ff);
    attempt(gameplayHook21, 0x17bfc0, 0xd10303ff);
    attempt(gameplayHook22, 0x17c770, 0xd10303ff);
    attempt(gameplayHook23, 0x17d0d0, 0xd10303ff);
    attempt(gameplayHook24, 0x181c70, 0xd10343ff);
    attempt(gameplayHook25, 0x181210, 0xd10343ff);
    attempt(gameplayHook26, 0x182460, 0xd10343ff);
    attempt(gameplayHook27, 0x18d3f0, 0xd10343ff);
    attempt(gameplayHook28, 0x1a4070, 0xd10403ff);
    attempt(gameplayHook29, 0x1a48c0, 0xd10403ff);
    attempt(gameplayHook30, 0x1a50b0, 0xd10403ff);
    attempt(gameplayHook31, 0x1a89e0, 0xd10303ff);
    attempt(gameplayHook32, 0x1a82f0, 0xd10303ff);
    attempt(gameplayHook33, 0x1a9120, 0xd10303ff);
    attempt(gameplayHook34, 0x1ab410, 0xd10343ff);
    attempt(gameplayHook35, 0x1abcb0, 0xd10343ff);
    attempt(gameplayHook36, 0x1af800, 0xd102c3ff);
    attempt(gameplayHook37, 0x1b1fc0, 0xd102c3ff);
    attempt(gameplayHook38, 0x1b24d0, 0xa9bc7bfd);
    attempt(gameplayHook39, 0x1b54c0, 0xd10303ff);
    attempt(gameplayHook40, 0x1b5a60, 0xd10303ff);
    attempt(gameplayHook41, 0x1b60f0, 0xd10303ff);
    attempt(gameplayHook42, 0x1b8db0, 0xd103c3ff);
    attempt(gameplayHook43, 0x1b8f70, 0xd103c3ff);
    attempt(gameplayHook44, 0x1db630, 0xd10303ff);
    attempt(gameplayHook45, 0x1dc030, 0xd10303ff);
    attempt(gameplayHook46, 0x1dbbc0, 0xd10303ff);
    attempt(gameplayHook47, 0x204970, 0xd10343ff);
    attempt(gameplayHook48, 0x205030, 0xd10343ff);
    attempt(gameplayHook49, 0x2057d0, 0xd10343ff);
    attempt(gameplayHook50, 0x209b80, 0xd10303ff);
    attempt(gameplayHook51, 0x20a170, 0xd10303ff);
    attempt(gameplayHook52, 0x20bf90, 0xd10343ff);
    attempt(gameplayHook53, 0x20c190, 0xd10343ff);
    hoop = attempt(gameplayHook54, 0x217960, 0xd102c3ff);
    attempt(gameplayHook55, 0x223350, 0xd10303ff);
    attempt(gameplayHook56, 0x222fa0, 0xd10303ff);
    attempt(gameplayHook57, 0x226aa0, 0xd10303ff);
    attempt(gameplayHook58, 0x2276a0, 0xd10303ff);
    attempt(gameplayHook59, 0x22ad50, 0xfc1d0fe8);
    attempt(gameplayHook60, 0x22aff0, 0xfc1d0fe8);
    attempt(gameplayHook61, 0x22e330, 0xd10403ff);
    attempt(gameplayHook62, 0x22e6d0, 0xd10403ff);
    attempt(gameplayHook63, 0x246760, 0xd10303ff);
    attempt(gameplayHook64, 0x246b80, 0xd10303ff);
    attempt(gameplayHook65, 0x246ff0, 0xd10303ff);
    attempt(gameplayHook66, 0x248b70, 0xd10383ff);
    attempt(gameplayHook67, 0x255100, 0xd102c3ff);
    attempt(gameplayHook68, 0x254a70, 0xd102c3ff);
    attempt(gameplayHook69, 0x2556c0, 0xd102c3ff);
    attempt(gameplayHook70, 0x278fe0, 0xd10483ff);
    attempt(gameplayHook71, 0x27dba0, 0xd10303ff);
    attempt(gameplayHook72, 0x27e130, 0xd10303ff);
    attempt(gameplayHook73, 0x27e6c0, 0xd10303ff);
    attempt(gameplayHook74, 0x27ec00, 0xd10303ff);
    attempt(gameplayHook75, 0x2aa6f0, 0xd10303ff);
    attempt(gameplayHook76, 0x2aa4f0, 0xd10303ff);
    attempt(gameplayHook77, 0x2aa2f0, 0xd10303ff);
    attempt(gameplayHook78, 0x2a9b00, 0xd10303ff);
    attempt(gameplayHook79, 0x2a9900, 0xd10303ff);
    attempt(gameplayHook80, 0x2a9700, 0xd10303ff);
    attempt(gameplayHook81, 0x23db30, 0xa9bc7bfd);
    attempt(gameplayHook82, 0x23d600, 0xd102c3ff);
    attempt(gameplayHook83, 0x23d790, 0xd102c3ff);
    attempt(gameplayHook84, 0x23d920, 0xd102c3ff);
    return count;
}
