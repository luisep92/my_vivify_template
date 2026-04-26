using System;
using System.Diagnostics;
using System.IO;
using UnityEditor;
using UnityEngine;
using Debug = UnityEngine.Debug;

namespace Aline.Editor
{
    // Vigila beatsaber-map/bundleinfo.json. Cada vez que Vivify lo escribe
    // (tras F5 o Build Configuration Window), invoca scripts/sync-crcs.ps1
    // para sincronizar los CRCs en Info.dat.
    //
    // Toggleable desde Tools/Aline/Auto-sync CRCs after Vivify build.
    [InitializeOnLoad]
    public static class PostBuildSyncCRCs
    {
        private const string PrefKey = "Aline.AutoSyncCRCs";
        private const string MenuPath = "Tools/Aline/Auto-sync CRCs after Vivify build";
        private const int DebounceMs = 500;

        private static FileSystemWatcher _watcher;
        private static DateTime _lastTrigger = DateTime.MinValue;
        private static readonly object _lock = new object();

        private static string RepoRoot =>
            Path.GetFullPath(Path.Combine(Application.dataPath, "..", ".."));
        private static string MapDir =>
            Path.Combine(RepoRoot, "beatsaber-map");
        private static string ScriptPath =>
            Path.Combine(RepoRoot, "scripts", "sync-crcs.ps1");

        static PostBuildSyncCRCs()
        {
            EditorApplication.delayCall += Initialize;
            AssemblyReloadEvents.beforeAssemblyReload += DisposeWatcher;
        }

        private static void Initialize()
        {
            if (!EditorPrefs.GetBool(PrefKey, true))
            {
                Debug.Log($"[sync-crcs] Auto-sync deshabilitado. Activar en {MenuPath}.");
                return;
            }
            SetupWatcher();
        }

        private static void SetupWatcher()
        {
            DisposeWatcher();

            if (!Directory.Exists(MapDir))
            {
                Debug.LogWarning($"[sync-crcs] {MapDir} no existe. Watcher no iniciado.");
                return;
            }

            _watcher = new FileSystemWatcher(MapDir, "bundleinfo.json")
            {
                NotifyFilter = NotifyFilters.LastWrite | NotifyFilters.CreationTime,
                EnableRaisingEvents = true
            };
            _watcher.Changed += OnBundleInfoChanged;
            _watcher.Created += OnBundleInfoChanged;

            Debug.Log($"[sync-crcs] Watching {Path.Combine(MapDir, "bundleinfo.json")}");
        }

        private static void DisposeWatcher()
        {
            if (_watcher == null) return;
            _watcher.EnableRaisingEvents = false;
            _watcher.Changed -= OnBundleInfoChanged;
            _watcher.Created -= OnBundleInfoChanged;
            _watcher.Dispose();
            _watcher = null;
        }

        private static void OnBundleInfoChanged(object sender, FileSystemEventArgs e)
        {
            // Debounce: el FileSystemWatcher de Windows dispara varias veces por
            // un solo File.WriteAllText. Consolidamos en una sola sync.
            lock (_lock)
            {
                if ((DateTime.UtcNow - _lastTrigger).TotalMilliseconds < DebounceMs) return;
                _lastTrigger = DateTime.UtcNow;
            }

            // El callback corre fuera del main thread de Unity. Diferimos para
            // poder llamar a Debug.Log limpiamente y dar margen a Vivify por si
            // aún esta cerrando otros archivos del build.
            EditorApplication.delayCall += RunSyncScript;
        }

        private static void RunSyncScript()
        {
            if (!File.Exists(ScriptPath))
            {
                Debug.LogError($"[sync-crcs] Script no encontrado: {ScriptPath}");
                return;
            }

            try
            {
                var psi = new ProcessStartInfo
                {
                    FileName = "powershell.exe",
                    Arguments = $"-ExecutionPolicy Bypass -NoProfile -File \"{ScriptPath}\"",
                    WorkingDirectory = RepoRoot,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                };

                using (var proc = Process.Start(psi))
                {
                    string stdout = proc.StandardOutput.ReadToEnd();
                    string stderr = proc.StandardError.ReadToEnd();
                    proc.WaitForExit();

                    if (proc.ExitCode == 0)
                    {
                        if (!string.IsNullOrWhiteSpace(stdout))
                            Debug.Log("[sync-crcs] " + stdout.Trim());
                    }
                    else
                    {
                        Debug.LogError(
                            $"[sync-crcs] Exit {proc.ExitCode}\nstdout: {stdout}\nstderr: {stderr}");
                    }
                }
            }
            catch (Exception ex)
            {
                Debug.LogError("[sync-crcs] Excepcion: " + ex.Message);
            }
        }

        [MenuItem(MenuPath)]
        private static void ToggleAutoSync()
        {
            bool current = EditorPrefs.GetBool(PrefKey, true);
            EditorPrefs.SetBool(PrefKey, !current);

            if (!current)
            {
                SetupWatcher();
                Debug.Log("[sync-crcs] Auto-sync activado.");
            }
            else
            {
                DisposeWatcher();
                Debug.Log("[sync-crcs] Auto-sync desactivado.");
            }
        }

        [MenuItem(MenuPath, validate = true)]
        private static bool ToggleAutoSyncValidate()
        {
            Menu.SetChecked(MenuPath, EditorPrefs.GetBool(PrefKey, true));
            return true;
        }
    }
}
