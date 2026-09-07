#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Havenline.Editor
{
    /// <summary>
    /// Hard production guard for HAVENLINE.
    ///
    /// This is intentionally strict: a shipping Android build must not silently
    /// regress to prototype/placeholder visuals or generic character fallbacks.
    /// Review/staging GLBs remain valid for the V7 review workflow, but they do
    /// not satisfy the production-character contract.
    /// </summary>
    public sealed class HavenlineProductionArtGate : IPreprocessBuildWithReport
    {
        private const string MenuPath = "HAVENLINE/Quality/Validate Production Art Gate";
        private const string ProductionCharacterRoot = "Assets/Havenline/Art/Characters/Production";
        private const string InternalErrorShader = "Hidden/InternalErrorShader";

        private static readonly string[] ForbiddenNameFragments =
        {
            "placeholder",
            "prototype",
            "blocky",
            "genericplayer",
            "generic player",
            "fallbackplayer",
            "fallback player",
            "tempplayer",
            "temp player",
            "dummyplayer",
            "dummy player",
            "graybox",
            "greybox",
        };

        private static readonly string[] ForbiddenAssetPathFragments =
        {
            "/Placeholder/",
            "/Placeholders/",
            "/Prototype/",
            "/Prototypes/",
            "/Greybox/",
            "/Graybox/",
            "/Blockout/",
            "/Blockouts/",
        };

        private static readonly HashSet<string> BuiltInPrimitiveMeshNames =
            new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            {
                "Cube",
                "Sphere",
                "Capsule",
                "Cylinder",
                "Plane",
                "Quad",
            };

        private static readonly string[] ForbiddenSceneFileNames =
        {
            "SampleScene.unity",
        };

        public int callbackOrder => -10000;

        [MenuItem(MenuPath)]
        public static void ValidateFromMenu()
        {
            var result = ValidateProductionContract();
            if (!result.Passed)
            {
                var message = result.FormatForConsole();
                Debug.LogError(message);
                EditorUtility.DisplayDialog(
                    "HAVENLINE Production Art Gate — BLOCKED",
                    "Shipping-quality validation failed. The Console contains the exact blockers.",
                    "OK");
                return;
            }

            Debug.Log(result.FormatForConsole());
            EditorUtility.DisplayDialog(
                "HAVENLINE Production Art Gate — PASS",
                "No prototype/placeholder blockers were found in enabled shipping scenes, and all four production character contracts are present.",
                "OK");
        }

        public void OnPreprocessBuild(BuildReport report)
        {
            if (report == null || report.summary.platform != BuildTarget.Android)
                return;

            var result = ValidateProductionContract();
            if (!result.Passed)
                throw new BuildFailedException(result.FormatForConsole());
        }

        internal static GateResult ValidateProductionContract()
        {
            var errors = new List<string>();
            var warnings = new List<string>();

            ValidateShippingScenes(errors, warnings);
            ValidateProductionCharacters(errors);
            ValidateAndroidPresentation(errors);

            return new GateResult(errors, warnings);
        }

        private static void ValidateShippingScenes(List<string> errors, List<string> warnings)
        {
            var enabledScenes = EditorBuildSettings.scenes
                .Where(scene => scene.enabled)
                .Select(scene => scene.path)
                .Where(path => !string.IsNullOrWhiteSpace(path))
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .ToArray();

            if (enabledScenes.Length == 0)
            {
                errors.Add("No enabled scenes exist in Build Settings.");
                return;
            }

            foreach (var scenePath in enabledScenes)
            {
                var fileName = Path.GetFileName(scenePath);
                if (ForbiddenSceneFileNames.Any(forbidden =>
                        string.Equals(fileName, forbidden, StringComparison.OrdinalIgnoreCase)))
                {
                    errors.Add($"Prototype/default scene is enabled for shipping: {scenePath}");
                }

                ValidateSceneDependencies(scenePath, errors);
                ScanScene(scenePath, errors, warnings);
            }
        }

        private static void ValidateSceneDependencies(string scenePath, List<string> errors)
        {
            foreach (var dependency in AssetDatabase.GetDependencies(scenePath, true))
            {
                if (string.Equals(dependency, scenePath, StringComparison.OrdinalIgnoreCase))
                    continue;

                var normalized = dependency.Replace('\\', '/');
                foreach (var fragment in ForbiddenAssetPathFragments)
                {
                    if (normalized.IndexOf(fragment, StringComparison.OrdinalIgnoreCase) < 0)
                        continue;

                    errors.Add($"Shipping scene '{scenePath}' still depends on prototype/placeholder asset: {dependency}");
                    break;
                }
            }
        }

        private static void ScanScene(string scenePath, List<string> errors, List<string> warnings)
        {
            var scene = SceneManager.GetSceneByPath(scenePath);
            var openedForScan = !scene.IsValid() || !scene.isLoaded;

            try
            {
                if (openedForScan)
                    scene = EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Additive);

                if (!scene.IsValid() || !scene.isLoaded)
                {
                    errors.Add($"Could not load enabled build scene for production-art validation: {scenePath}");
                    return;
                }

                foreach (var root in scene.GetRootGameObjects())
                {
                    foreach (var transform in root.GetComponentsInChildren<Transform>(true))
                    {
                        var gameObject = transform.gameObject;
                        ValidateObjectName(scenePath, gameObject, errors);

                        if (!gameObject.activeInHierarchy)
                            continue;

                        ValidateVisibleMesh(scenePath, gameObject, errors);
                        ValidateRendererMaterials(scenePath, gameObject, errors);
                    }
                }

                var cameras = scene.GetRootGameObjects()
                    .SelectMany(root => root.GetComponentsInChildren<Camera>(true))
                    .Where(camera => camera != null && camera.enabled && camera.gameObject.activeInHierarchy)
                    .ToArray();

                if (cameras.Length == 0)
                    warnings.Add($"Enabled scene has no active Camera at edit time: {scenePath}. If the camera is spawned at runtime, verify the r29 landscape gameplay proof still covers this scene.");
            }
            catch (Exception ex)
            {
                errors.Add($"Scene scan failed for {scenePath}: {ex.GetType().Name}: {ex.Message}");
            }
            finally
            {
                if (openedForScan && scene.IsValid() && scene.isLoaded)
                    EditorSceneManager.CloseScene(scene, true);
            }
        }

        private static void ValidateObjectName(string scenePath, GameObject gameObject, List<string> errors)
        {
            var normalized = gameObject.name ?? string.Empty;
            foreach (var fragment in ForbiddenNameFragments)
            {
                if (normalized.IndexOf(fragment, StringComparison.OrdinalIgnoreCase) < 0)
                    continue;

                errors.Add($"Prototype/placeholder object is present in shipping scene '{scenePath}': {GetHierarchyPath(gameObject.transform)}");
                return;
            }
        }

        private static void ValidateVisibleMesh(string scenePath, GameObject gameObject, List<string> errors)
        {
            var renderer = gameObject.GetComponent<MeshRenderer>();
            var filter = gameObject.GetComponent<MeshFilter>();
            if (renderer == null || filter == null || !renderer.enabled || filter.sharedMesh == null)
                return;

            var mesh = filter.sharedMesh;
            var meshAssetPath = AssetDatabase.GetAssetPath(mesh) ?? string.Empty;
            var builtInMesh = string.IsNullOrEmpty(meshAssetPath) ||
                              meshAssetPath.IndexOf("unity default resources", StringComparison.OrdinalIgnoreCase) >= 0 ||
                              meshAssetPath.IndexOf("unity_builtin_extra", StringComparison.OrdinalIgnoreCase) >= 0;

            if (builtInMesh && BuiltInPrimitiveMeshNames.Contains(mesh.name))
            {
                errors.Add(
                    $"Visible Unity primitive '{mesh.name}' is still rendering in shipping scene '{scenePath}' at {GetHierarchyPath(gameObject.transform)}. " +
                    "Replace visible greybox/blockout geometry with authored production art.");
            }
        }

        private static void ValidateRendererMaterials(string scenePath, GameObject gameObject, List<string> errors)
        {
            var renderer = gameObject.GetComponent<Renderer>();
            if (renderer == null || !renderer.enabled)
                return;

            var materials = renderer.sharedMaterials;
            for (var index = 0; index < materials.Length; index++)
            {
                var material = materials[index];
                if (material == null)
                {
                    errors.Add($"Missing material slot {index} in shipping scene '{scenePath}' at {GetHierarchyPath(gameObject.transform)}.");
                    continue;
                }

                var shader = material.shader;
                if (shader == null ||
                    string.Equals(shader.name, InternalErrorShader, StringComparison.OrdinalIgnoreCase) ||
                    shader.name.IndexOf("InternalErrorShader", StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    errors.Add($"Error/missing shader on '{material.name}' in shipping scene '{scenePath}' at {GetHierarchyPath(gameObject.transform)}.");
                }

                if (string.Equals(material.name, "Default-Material", StringComparison.OrdinalIgnoreCase) ||
                    string.Equals(material.name, "Default Material", StringComparison.OrdinalIgnoreCase))
                {
                    errors.Add($"Default material is still visible in shipping scene '{scenePath}' at {GetHierarchyPath(gameObject.transform)}.");
                }
            }
        }

        private static void ValidateProductionCharacters(List<string> errors)
        {
            for (var character = 1; character <= 4; character++)
            {
                var path = $"{ProductionCharacterRoot}/Character{character}/Character{character}_production.fbx";
                if (!File.Exists(ToAbsoluteProjectPath(path)))
                {
                    errors.Add(
                        $"Character {character} production asset is missing: {path}. " +
                        "V7 staging GLBs may be reviewed, but a shipping build may not substitute a generic/placeholder character.");
                    continue;
                }

                var importer = AssetImporter.GetAtPath(path) as ModelImporter;
                if (importer == null)
                {
                    errors.Add($"Character {character} production asset is not imported by Unity as a ModelImporter: {path}");
                    continue;
                }

                if (importer.animationType != ModelImporterAnimationType.Human)
                {
                    errors.Add(
                        $"Character {character} production asset is not configured as Humanoid: {path} " +
                        $"(current animationType={importer.animationType}).");
                }

                var model = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                if (model == null)
                {
                    errors.Add($"Character {character} production model cannot be loaded as a GameObject: {path}");
                    continue;
                }

                var renderers = model.GetComponentsInChildren<SkinnedMeshRenderer>(true);
                if (renderers.Length == 0)
                {
                    errors.Add($"Character {character} production model has no SkinnedMeshRenderer: {path}");
                    continue;
                }

                var missingMaterialSlots = renderers.Sum(renderer =>
                    renderer.sharedMaterials.Count(material => material == null));

                if (missingMaterialSlots > 0)
                    errors.Add($"Character {character} production model has {missingMaterialSlots} missing material slot(s): {path}");
            }
        }

        private static void ValidateAndroidPresentation(List<string> errors)
        {
            var orientation = PlayerSettings.defaultInterfaceOrientation;
            if (orientation == UIOrientation.Portrait ||
                orientation == UIOrientation.PortraitUpsideDown)
            {
                errors.Add(
                    $"Shipping gameplay is landscape-only, but PlayerSettings.defaultInterfaceOrientation is {orientation}.");
            }

            if (orientation == UIOrientation.AutoRotation)
            {
                var landscapeEnabled =
                    PlayerSettings.allowedAutorotateToLandscapeLeft ||
                    PlayerSettings.allowedAutorotateToLandscapeRight;
                var portraitEnabled =
                    PlayerSettings.allowedAutorotateToPortrait ||
                    PlayerSettings.allowedAutorotateToPortraitUpsideDown;

                if (!landscapeEnabled || portraitEnabled)
                {
                    errors.Add(
                        "Shipping gameplay is landscape-only. Auto Rotation must enable landscape and disable both portrait orientations.");
                }
            }

            if (PlayerSettings.colorSpace != ColorSpace.Linear)
                errors.Add($"Production Android rendering must use Linear color space; current setting is {PlayerSettings.colorSpace}.");

            var scriptingBackend = PlayerSettings.GetScriptingBackend(NamedBuildTarget.Android);
            if (scriptingBackend != ScriptingImplementation.IL2CPP)
                errors.Add($"Production Android builds must use IL2CPP; current scripting backend is {scriptingBackend}.");

            var architectures = PlayerSettings.Android.targetArchitectures;
            if ((architectures & AndroidArchitecture.ARM64) == 0)
                errors.Add($"Android ARM64 support is required; current targetArchitectures={architectures}.");
        }

        private static string ToAbsoluteProjectPath(string assetPath)
        {
            var projectRoot = Directory.GetParent(Application.dataPath)?.FullName;
            if (string.IsNullOrEmpty(projectRoot))
                return Path.GetFullPath(assetPath);

            return Path.GetFullPath(Path.Combine(projectRoot, assetPath.Replace('/', Path.DirectorySeparatorChar)));
        }

        private static string GetHierarchyPath(Transform transform)
        {
            if (transform == null)
                return "<null>";

            var names = new Stack<string>();
            for (var current = transform; current != null; current = current.parent)
                names.Push(current.name);

            return string.Join("/", names);
        }

        internal sealed class GateResult
        {
            public GateResult(List<string> errors, List<string> warnings)
            {
                Errors = errors ?? new List<string>();
                Warnings = warnings ?? new List<string>();
            }

            public IReadOnlyList<string> Errors { get; }
            public IReadOnlyList<string> Warnings { get; }
            public bool Passed => Errors.Count == 0;

            public string FormatForConsole()
            {
                var lines = new List<string>
                {
                    Passed
                        ? "HAVENLINE production art gate: PASS"
                        : $"HAVENLINE production art gate: BLOCKED ({Errors.Count} error(s))",
                };

                foreach (var error in Errors)
                    lines.Add($"ERROR: {error}");
                foreach (var warning in Warnings)
                    lines.Add($"WARN: {warning}");

                return string.Join(Environment.NewLine, lines);
            }
        }
    }
}
#endif
