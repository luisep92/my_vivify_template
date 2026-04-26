using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace Aline.Editor
{
    // Genera Aline_AC.controller a partir de los AnimationClips importados
    // del FBX Aline_Anims.fbx. Patrón: Idle1 default; Any State -> X via trigger
    // (nombre del clip sin el prefijo "Paintress_"); estados no-loop vuelven
    // a Idle1 con Has Exit Time. Idempotente: borra y recrea el .controller.
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
            int returnCount = 0;
            foreach (var kv in states)
            {
                var state = kv.Value;
                var triggerName = TriggerName(kv.Key);

                // Any State -> state via trigger (immediate, sin exit time).
                var anyTrans = sm.AddAnyStateTransition(state);
                anyTrans.AddCondition(AnimatorConditionMode.If, 0f, triggerName);
                anyTrans.duration = 0.1f;
                anyTrans.hasExitTime = false;
                anyTrans.canTransitionToSelf = false;
                triggerCount++;

                // No-loop & no-default: auto-return a default al final del clip.
                var clip = state.motion as AnimationClip;
                if (clip != null && !clip.isLooping && state != defaultState)
                {
                    var ret = state.AddTransition(defaultState);
                    ret.hasExitTime = true;
                    ret.exitTime = 0.95f;
                    ret.duration = 0.15f;
                    returnCount++;
                }
            }

            EditorUtility.SetDirty(controller);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            Debug.Log(
                "[BuildAlineAnimator] OK. " + ControllerPath + " — " +
                clips.Length + " states, " + triggerCount + " trigger transitions, " +
                returnCount + " return-to-default. Default: " + defaultState.name);

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
 
