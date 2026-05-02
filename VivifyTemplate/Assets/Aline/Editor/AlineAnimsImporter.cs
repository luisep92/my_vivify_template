using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

namespace Aline.Editor
{
    // Setea loopTime=true en los clips que deben loopear al importar
    // Aline_Anims.fbx, evitando el clásico bug del Inspector de 2019.4
    // (toggles que se pierden al cambiar de clip sin pulsar Apply).
    //
    // Lista LoopingClips explícita: idles puros + Skill2_Loop. Los DashIn-IdleN,
    // *_to_idle*_transition no loopean (son transiciones one-shot).
    public class AlineAnimsImporter : AssetPostprocessor
    {
        private const string TargetPath = "Assets/Aline/Animations/Aline_Anims.fbx";

        // Match contra el sufijo posterior al "|" (formato Unity: <root>|<action>).
        // Ej: clip.name = "SK_Curator_Aline|Paintress_Idle1" -> sufijo "Paintress_Idle1".
        private static readonly HashSet<string> LoopingSuffixes = new HashSet<string>
        {
            "Paintress_Idle1",
            "Paintress_Idle2",
            "Paintress_Idle3",
            "Paintress_Idle2_Stun",
            "Paintress_Idle_Countered",
            "Paintress_Skill2_Loop",
        };

        // Clips que tienen motion horizontal real (root del rig se mueve en XZ).
        // Para estos forzamos extracción de root motion: el GO traslada de
        // verdad (Apply Root Motion ON en el Animator) y la mesh no salta de
        // vuelta al origen al terminar el clip. Los demás clips bakean motion
        // en bones (default), aceptable para idles y poses estáticas.
        // Y rotación se quedan baked (Aline no flota via root, no spinea via root).
        private static readonly HashSet<string> XzRootMotionSuffixes = new HashSet<string>
        {
            "Paintress_DashIn-Idle1",
            "Paintress_DashIn-Idle2",
            "Paintress_DashOut-Idle1",
            "Paintress_DashOut-Idle2",
            "DefaultSlot",
            "DefaultSlot (1)",
        };

        private static string ActionSuffix(string clipName)
        {
            int pipe = clipName.IndexOf('|');
            return pipe >= 0 ? clipName.Substring(pipe + 1) : clipName;
        }

        // Unity colapsa por defecto nodos transform de un solo hijo en la raíz
        // del FBX. Blender exporta el armature object 'SK_Curator_Aline' como
        // Null node con 'root' (la pose root bone) como único hijo, así que
        // el GO 'SK_Curator_Aline' desaparece en el import → clip paths salen
        // como 'root/...' sin prefijo, y la preview del FBX rompe cuando usa
        // Aline.fbx como modelo (que sí tiene 'SK_Curator_Aline' en jerarquía).
        // preserveHierarchy=true le dice al importer que no colapse.
        void OnPreprocessModel()
        {
            var normalized = assetPath.Replace('\\', '/');
            if (normalized != TargetPath) return;

            var importer = assetImporter as ModelImporter;
            if (importer == null) return;
            if (!importer.preserveHierarchy) importer.preserveHierarchy = true;
        }

        void OnPreprocessAnimation()
        {
            var normalized = assetPath.Replace('\\', '/');
            if (normalized != TargetPath) return;

            var importer = assetImporter as ModelImporter;
            if (importer == null) return;

            // El motion forward de DashIn/DashOut vive en location del armature
            // object (synthesized en Blender via scripts/blender/synthesize_root_motion.py;
            // los .psa originales lo bakean en pose.bones["root"].location, que
            // Unity 2019.4 con Generic + Copy From Other Avatar no extrae). En Unity
            // ese armature object aparece como GO 'SK_Curator_Aline' (child del
            // prefab root). motionNodeName apuntando a ese nombre hace que Unity
            // calcule averageSpeed != 0 y lo traduzca como root motion al prefab
            // (con Apply Root Motion = ON en el Animator).
            const string MotionNode = "SK_Curator_Aline";
            if (importer.motionNodeName != MotionNode) importer.motionNodeName = MotionNode;

            // Siempre arrancar desde defaultClipAnimations (snapshot vivo del
            // FBX). Si arrancáramos desde clipAnimations, takes nuevos
            // añadidos en Blender no entrarían hasta el siguiente reset manual
            // del importer (síntoma: action 'Paintress_DashIn-Idle2' existe en
            // el FBX pero el AnimatorController no la ve como clip). Los
            // settings per-clip que aplicamos abajo (loopTime, lockRootPositionXZ,
            // etc.) son deterministas según el suffix, así que reset cada
            // import es seguro y garantiza coherencia.
            var clips = importer.defaultClipAnimations;

            int looped = 0;
            int xzExtracted = 0;
            for (int i = 0; i < clips.Length; i++)
            {
                var actionSuffix = ActionSuffix(clips[i].name);

                bool shouldLoop = LoopingSuffixes.Contains(actionSuffix);
                if (clips[i].loopTime != shouldLoop)
                {
                    clips[i].loopTime = shouldLoop;
                }
                if (shouldLoop) looped++;

                // Para clips con motion horizontal (DashIn/DashOut/aliases),
                // desbakear XZ e Y para que Unity los extraiga como root motion.
                // El motion vive en location del armature object (synthetizado en
                // Blender via scripts/blender/synthesize_root_motion.py — los
                // .psa originales lo bakean en pose.bones["root"].location, que
                // Unity 2019.4 con Generic + Copy From Other Avatar no extrae aunque
                // el bone esté en transformPaths). Los toggles aquí solo aplican
                // si las curvas existen — clips estáticos (idles, skills sin
                // desplazamiento) no se ven afectados.
                bool extractXz = XzRootMotionSuffixes.Contains(actionSuffix);
                clips[i].lockRootPositionXZ = !extractXz;
                clips[i].keepOriginalPositionXZ = !extractXz;
                clips[i].keepOriginalPositionY = !extractXz;
                if (extractXz) xzExtracted++;
            }

            importer.clipAnimations = clips;
            Debug.Log("[AlineAnimsImporter] " + clips.Length + " clips procesados, " + looped + " marcados loopTime=true, " + xzExtracted + " con XZ root motion extraído.");
        }

    }
}
