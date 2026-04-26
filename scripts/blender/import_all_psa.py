"""
Batch-import every .psa in PSA_DIR onto ARMATURE_NAME as a separate action.

Run from Blender:
  - Open Aline_project.blend
  - Open Scripting workspace, paste/open this file, click Run Script
  - Or via Blender's CLI:  blender --background file.blend --python this_file.py

The Befzz / DarklightGames PSK/PSA addon must be enabled (extension id
io_scene_psk_psa). The addon doesn't link the imported action to the
armature's animation_data; that has to be done manually if you want one
of them as the active action. fake_user is set on every action so they
survive .blend save without a slot.
"""

import os
import bpy

PSA_DIR = r"D:\vivify_repo\my_vivify_template\Sandfall\Content\Characters\Enemies\HumanEnnemies\Aline\Animation"
ARMATURE_NAME = "SK_Curator_Aline"
SKIP_EXISTING = True   # if action with the sequence's name already exists, skip the .psa
BONE_MAPPING = "CASE_INSENSITIVE"


def _resolve_addon():
    candidates = [
        "bl_ext.user_default.io_scene_psk_psa",
        "io_scene_psk_psa",
    ]
    for name in candidates:
        try:
            mod = __import__(name, fromlist=["psa"])
            return mod
        except ImportError:
            continue
    raise RuntimeError("io_scene_psk_psa addon not found. Enable it in Preferences > Extensions.")


def import_all():
    addon = _resolve_addon()
    PsaReader = addon.psa.reader.PsaReader
    PsaImportOptions = addon.psa.importer.PsaImportOptions
    import_psa = addon.psa.importer.import_psa

    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature '{ARMATURE_NAME}' not found in scene.")

    psa_files = sorted(
        os.path.join(PSA_DIR, f)
        for f in os.listdir(PSA_DIR)
        if f.lower().endswith(".psa")
    )
    print(f"[psa-batch] {len(psa_files)} .psa files in {PSA_DIR}")

    imported, skipped, failed = [], [], []
    all_warnings = []

    for psa_path in psa_files:
        fname = os.path.basename(psa_path)
        try:
            reader = PsaReader(psa_path)
            seq_names = list(reader.sequences.keys())
        except Exception as e:
            failed.append((fname, f"reader error: {e}"))
            print(f"[psa-batch] FAIL {fname}: {e}")
            continue

        if SKIP_EXISTING and all(name in bpy.data.actions for name in seq_names):
            skipped.append(fname)
            print(f"[psa-batch] skip {fname} (actions exist: {seq_names})")
            continue

        opts = PsaImportOptions()
        opts.sequence_names = seq_names
        opts.bone_mapping_mode = BONE_MAPPING
        opts.should_use_fake_user = True
        opts.should_overwrite = False
        opts.should_write_keyframes = True
        opts.should_write_metadata = True

        try:
            result = import_psa(bpy.context, reader, arm, opts)
        except Exception as e:
            failed.append((fname, f"import error: {e}"))
            print(f"[psa-batch] FAIL {fname}: {e}")
            continue

        imported.append((fname, seq_names))
        if result.warnings:
            all_warnings.append((fname, result.warnings))
        print(f"[psa-batch] ok   {fname} -> {seq_names} ({len(result.warnings)} warn)")

    print("\n[psa-batch] === SUMMARY ===")
    print(f"  imported: {len(imported)}")
    print(f"  skipped : {len(skipped)}")
    print(f"  failed  : {len(failed)}")
    if failed:
        for f, msg in failed:
            print(f"    - {f}: {msg}")
    if all_warnings:
        print(f"  files with warnings: {len(all_warnings)}")
        for f, ws in all_warnings[:3]:
            print(f"    - {f}: {len(ws)} warning(s); first: {ws[0][:200]}")
    return imported, skipped, failed


if __name__ == "__main__":
    import_all()
