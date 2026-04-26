using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace Aline.Editor
{
    // Vuelca a la Console las curvas de los AnimationClips de Aline_Anims.fbx
    // agrupadas por bone y propiedad. Sirve para detectar curvas de scale
    // que podrían explotar el rig al ser aplicadas por el Animator.
    public static class InspectAlineClips
    {
        private const string FbxPath = "Assets/Aline/Animations/Aline_Anims.fbx";

        [MenuItem("Tools/Aline/Inspect Clip Curves (Idle1)")]
        public static void InspectIdle1()
        {
            Inspect("Paintress_Idle1");
        }

        [MenuItem("Tools/Aline/Inspect Clip Curves (Summary all)")]
        public static void InspectAll()
        {
            var clips = AssetDatabase.LoadAllAssetsAtPath(FbxPath)
                .OfType<AnimationClip>()
                .Where(c => !c.name.StartsWith("__preview__"))
                .OrderBy(c => c.name)
                .ToArray();

            int totalScale = 0, totalPos = 0, totalRot = 0, totalOther = 0;
            foreach (var clip in clips)
            {
                int s, p, r, o;
                CountByType(clip, out s, out p, out r, out o);
                totalScale += s; totalPos += p; totalRot += r; totalOther += o;
                Debug.Log("[InspectClips] " + clip.name + " -> rot:" + r + " pos:" + p + " scale:" + s + " other:" + o);
            }
            Debug.Log("[InspectClips] TOTAL across " + clips.Length + " clips -> rot:" + totalRot + " pos:" + totalPos + " scale:" + totalScale + " other:" + totalOther);
        }

        private static void Inspect(string suffix)
        {
            var clip = AssetDatabase.LoadAllAssetsAtPath(FbxPath)
                .OfType<AnimationClip>()
                .FirstOrDefault(c => c.name.EndsWith("|" + suffix) || c.name == suffix);
            if (clip == null)
            {
                Debug.LogError("[InspectClips] Clip with suffix '" + suffix + "' no encontrado en " + FbxPath);
                return;
            }

            var bindings = AnimationUtility.GetCurveBindings(clip);
            var byPath = new Dictionary<string, List<EditorCurveBinding>>();
            foreach (var b in bindings)
            {
                if (!byPath.ContainsKey(b.path)) byPath[b.path] = new List<EditorCurveBinding>();
                byPath[b.path].Add(b);
            }

            Debug.Log("[InspectClips] " + clip.name + " — " + bindings.Length + " curves across " + byPath.Count + " bones");

            // Print bones near root (likely culprits) first
            var keyPaths = new[] { "", "root", "SK_Curator_Aline", "SK_Curator_Aline/root", "pelvis" };
            foreach (var path in keyPaths)
            {
                if (!byPath.ContainsKey(path)) continue;
                var props = byPath[path].Select(b => b.propertyName).OrderBy(n => n).ToArray();
                Debug.Log("[InspectClips]   path='" + (path == "" ? "<root>" : path) + "' (" + props.Length + " props): " + string.Join(", ", props));
            }

            // Property breakdown across the whole clip
            int sCount, pCount, rCount, oCount;
            CountByType(clip, out sCount, out pCount, out rCount, out oCount);
            Debug.Log("[InspectClips]   totals: rot=" + rCount + " pos=" + pCount + " scale=" + sCount + " other=" + oCount);

            // Sample any scale curves' first/last values to see magnitude
            int shown = 0;
            foreach (var b in bindings)
            {
                if (!b.propertyName.Contains("Scale")) continue;
                var curve = AnimationUtility.GetEditorCurve(clip, b);
                if (curve == null || curve.length == 0) continue;
                var first = curve.keys[0].value;
                var last = curve.keys[curve.length - 1].value;
                Debug.Log("[InspectClips]   scale curve at '" + b.path + "' prop=" + b.propertyName + " first=" + first + " last=" + last + " keys=" + curve.length);
                if (++shown >= 10) { Debug.Log("[InspectClips]   ... (truncated, more scale curves exist)"); break; }
            }
        }

        private static void CountByType(AnimationClip clip, out int scale, out int pos, out int rot, out int other)
        {
            scale = pos = rot = other = 0;
            foreach (var b in AnimationUtility.GetCurveBindings(clip))
            {
                var pn = b.propertyName;
                if (pn.Contains("Scale")) scale++;
                else if (pn.Contains("Position") || pn == "m_LocalPosition.x" || pn == "m_LocalPosition.y" || pn == "m_LocalPosition.z") pos++;
                else if (pn.Contains("Rotation") || pn.StartsWith("m_LocalRotation")) rot++;
                else other++;
            }
        }
    }
}
