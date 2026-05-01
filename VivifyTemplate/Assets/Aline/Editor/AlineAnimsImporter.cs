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

            // Si el usuario aún no ha tocado clipAnimations, parten de los defaults
            // del FBX. defaultClipAnimations ya contiene una entry por take.
            var clips = importer.clipAnimations;
            if (clips == null || clips.Length == 0)
                clips = importer.defaultClipAnimations;

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

                // Por defecto Generic baked motion en bones. Para clips con
                // motion horizontal real, desbloquear y normalizar XZ para que
                // Unity extraiga el delta como root motion.
                bool extractXz = XzRootMotionSuffixes.Contains(actionSuffix);
                clips[i].lockRootPositionXZ = !extractXz;
                clips[i].keepOriginalPositionXZ = !extractXz;
                if (extractXz) xzExtracted++;
            }

            importer.clipAnimations = clips;
            Debug.Log("[AlineAnimsImporter] " + clips.Length + " clips procesados, " + looped + " marcados loopTime=true, " + xzExtracted + " con XZ root motion extraído.");
        }

    }
}
