using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace Aline.Editor
{
    // Genera Aline_AC.controller a partir de los AnimationClips importados
    // del FBX Aline_Anims.fbx. Patrón: Idle1 default; Any State -> X via trigger
    // (nombre del clip sin el prefijo "Paintress_"). Por defecto los estados
    // no-loop vuelven a Idle1 con Has Exit Time, pero hay dos overrides para
    // evitar snaps visuales en transiciones de fase y dashes:
    //   - ChainOverrides: estado X chaina a estado Y concreto en vez de Idle1
    //     (p.ej. Idle1_to_idle2_transition -> Idle2).
    //   - NoFallback: estado se queda en última frame y NO chaina a nada
    //     (p.ej. DashIn-Idle1, espera al siguiente trigger explícito).
    // Idempotente: borra y recrea el .controller.
    //
    // Uso: Tools/Aline/Build Animator Controller. Requiere que Aline_Anims.fbx
    // ya esté importado con Rig=Generic y Avatar=Copy From Other Avatar
    // apuntando a Aline.fbx — si no, Unity no expone los clips como sub-assets.
    public static class BuildAlineAnimator
    {
        private const string FbxPath = "Assets/Aline/Animations/Aline_Anims.fbx";
        private const string ControllerPath = "Assets/Aline/Animations/Aline_AC.controller";
        // Match contra el sufijo tras "|" porque Unity nombra los takes como
        // "<root>|<action>", ej: "SK_Curator_Aline|Paintress_Idle1".
        private const string DefaultStateSuffix = "Paintress_Idle1";
        private const string ActionPrefix = "Paintress_"; // se quita para nombres de trigger

        // Estados no-loop que NO deben volver a Idle1 al terminar; chainan al
        // destino especificado. Por defecto cada estado vuelve a Idle1
        // (default state) al exit time, pero algunos clips terminan en pose
        // que no encaja con Idle1 (p.ej. fin de fase 2 → Idle2 flotando).
        // Las claves son ActionSuffix (lo que sale tras "|" del clip name).
        //
        // Decisión: DashIn-Idle1 también chainа a Idle1 por defecto (Aline
        // vuelve a su sitio tras el ataque mele). Si quieres mantener el chain
        // DashIn → DashOut sin pasar por Idle1, dispara DashOut mientras DashIn
        // está jugando — la transición de Any State interrumpe el chain al
        // exit time y Aline pasa directa a DashOut.
        private static readonly Dictionary<string, string> ChainOverrides = new Dictionary<string, string>
        {
            { "Paintress_Idle1_to_idle2_transition", "Paintress_Idle2" },
            { "Paintress_Idle2_to_idle3_transition", "Paintress_Idle3" },
            { "Paintress_DashOut-Idle2", "Paintress_Idle2" },
        };

        // Estados que se quedan en su última frame y NO chainan a ningún destino.
        // Útil cuando el clip termina en una pose que NO debería volver a idle
        // (p.ej. una pose final de impacto que se queda colgada hasta el siguiente
        // trigger). Vacío por defecto — añade aquí casos justificados.
        private static readonly HashSet<string> NoFallback = new HashSet<string>();

        [MenuItem("Tools/Aline/Build Animator Controller")]
        public static void Build()
        {
            var clips = AssetDatabase.LoadAllAssetsAtPath(FbxPath)
                .OfType<AnimationClip>()
                .Where(c => !c.name.StartsWith("__preview__"))
                .OrderBy(c => c.name)
                .ToArray();

            if (clips.Length == 0)
            {
                Debug.LogError(
                    "[BuildAlineAnimator] No AnimationClips encontrados en " + FbxPath +
                    ". Verifica que el FBX está importado con Rig=Generic y Avatar=Copy From Other Avatar.");
                return;
            }

            if (AssetDatabase.LoadAssetAtPath<AnimatorController>(ControllerPath) != null)
            {
                AssetDatabase.DeleteAsset(ControllerPath);
            }

            var controller = AnimatorController.CreateAnimatorControllerAtPath(ControllerPath);
            var sm = controller.layers[0].stateMachine;
            sm.entryPosition = new Vector3(-300, 0, 0);
            sm.exitPosition = new Vector3(900, 0, 0);
            sm.anyStatePosition = new Vector3(-300, 200, 0);

            // Trigger por clip (sin prefijo Paintress_).
            foreach (var clip in clips)
            {
                controller.AddParameter(TriggerName(clip.name), AnimatorControllerParameterType.Trigger);
            }

            // Estado por clip.
            var states = new Dictionary<string, AnimatorState>();
            for (int i = 0; i < clips.Length; i++)
            {
                var clip = clips[i];
                var state = sm.AddState(clip.name, new Vector3(300, i * 60, 0));
                state.motion = clip;
                states[clip.name] = state;
            }

            var defaultState = states.Values.FirstOrDefault(s => ActionSuffix(s.name) == DefaultStateSuffix);
            if (defaultState == null)
            {
                defaultState = states.Values.First();
                Debug.LogWarning(
                    "[BuildAlineAnimator] No encontré clip con sufijo '" + DefaultStateSuffix +
                    "'; usando '" + defaultState.name + "' como default.");
            }
            sm.defaultState = defaultState;

            // Transiciones.
            int triggerCount = 0;
            int returnDefaultCount = 0;
            int returnOverrideCount = 0;
            int noFallbackCount = 0;
            foreach (var kv in states)
            {
                var state = kv.Value;
                var triggerName = TriggerName(kv.Key);

                // Any State -> state via trigger (immediate, sin exit time).
                // Duration=0.1s blend para suavizar mismatches de pose entre clips
                // discretos. Hard cut (duration=0) deja saltos visibles cuando los
                // huesos no matchean exactamente entre clip anterior y nuevo;
                // 0.1s interpola y disimula el mismatch en ~3-4 frames.
                var anyTrans = sm.AddAnyStateTransition(state);
                anyTrans.AddCondition(AnimatorConditionMode.If, 0f, triggerName);
                anyTrans.duration = 0.1f;
                anyTrans.hasExitTime = false;
                anyTrans.canTransitionToSelf = false;
                triggerCount++;

                var clip = state.motion as AnimationClip;
                if (clip == null || clip.isLooping || state == defaultState) continue;

                var actionSuffix = ActionSuffix(kv.Key);
                if (NoFallback.Contains(actionSuffix))
                {
                    noFallbackCount++;
                    continue;
                }

                AnimatorState target = defaultState;
                if (ChainOverrides.TryGetValue(actionSuffix, out var chainSuffix))
                {
                    var matched = states.Values.FirstOrDefault(s => ActionSuffix(s.name) == chainSuffix);
                    if (matched != null)
                    {
                        target = matched;
                        returnOverrideCount++;
                    }
                    else
                    {
                        Debug.LogWarning(
                            "[BuildAlineAnimator] ChainOverride '" + actionSuffix + "' -> '" + chainSuffix +
                            "' pero el estado destino no existe; cae a defaultState.");
                        returnDefaultCount++;
                    }
                }
                else
                {
                    returnDefaultCount++;
                }

                var ret = state.AddTransition(target);
                ret.hasExitTime = true;
                ret.exitTime = 0.95f;
                ret.duration = 0.15f;
            }

            EditorUtility.SetDirty(controller);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            Debug.Log(
                "[BuildAlineAnimator] OK. " + ControllerPath + " — " +
                clips.Length + " states, " + triggerCount + " trigger transitions, " +
                returnDefaultCount + " return-to-default, " + returnOverrideCount + " chain-override, " +
                noFallbackCount + " no-fallback. Default: " + defaultState.name);

            EditorGUIUtility.PingObject(controller);
            Selection.activeObject = controller;
        }

        private static string ActionSuffix(string clipName)
        {
            int pipe = clipName.IndexOf('|');
            return pipe >= 0 ? clipName.Substring(pipe + 1) : clipName;
        }

        private static string TriggerName(string clipName)
        {
            var action = ActionSuffix(clipName);
            return action.StartsWith(ActionPrefix) ? action.Substring(ActionPrefix.Length) : action;
        }
    }
}
 
