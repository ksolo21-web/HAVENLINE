#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Havenline.Editor
{
    /// <summary>
    /// Deterministic V7 character import/review gate.
    /// Source GLBs remain staging assets. Passing this check never marks a character as human-approved
    /// and never claims the legacy CharacterN_production.fbx contract has been satisfied.
    /// </summary>
    public static class HavenlineV7CharacterReview
    {
        private const string CandidateVersion = "V7";
        private const string StagingRoot = "Assets/Havenline/Art/Characters/Staging/V7";
        private const string ArtifactRoot = "Artifacts/HavenlineCharacterReview/V7";
        private const int ExpectedJointCount = 52;
        private const int CaptureSize = 1024;

        private static readonly SourceSpec[] Sources =
        {
            new SourceSpec(1, "Havenline_Character_1_Rigged_Refined_V7.glb", "a14352ab6fb483609c91712dceab6a3be8ae35ae6c3733e431df49de3f9c55db", 9149476),
            new SourceSpec(2, "Havenline_Character_2_Rigged_Refined_V7.glb", "6252680d0fd990f8d6819b6255e1d9b13c7ff77c34eacb84551efcad6d1dc839", 9799036),
            new SourceSpec(3, "Havenline_Character_3_Rigged_Refined_V7.glb", "88ecef677472ed63fce98f0e75e60507555dd9d8becfb75aa02f59f59eb4d360", 10931132),
            new SourceSpec(4, "Havenline_Character_4_Rigged_Refined_V7.glb", "bea67fe847c2c1f05bd0a0822cbca4b16b95f6e844a1d9aba66f56b2dc374a6e", 10884332),
        };

        [MenuItem("HAVENLINE/Characters/V7/Validate + Capture Review Proof")]
        public static void ValidateAndCaptureFromMenu()
        {
            var report = RunReview();
            var message = report.machineGatePassed
                ? "V7 Unity import gate passed. Review captures were generated. Human visual/gameplay approval is still required."
                : "V7 Unity import gate failed. Open the generated JSON report and Console for the exact blockers.";
            EditorUtility.DisplayDialog("HAVENLINE V7 Character Review", message, "OK");
        }

        /// <summary>
        /// Batch-mode entry point:
        /// Unity -batchmode -quit -projectPath <project> -executeMethod Havenline.Editor.HavenlineV7CharacterReview.RunBatchMode
        /// </summary>
        public static void RunBatchMode()
        {
            var report = RunReview();
            if (!report.machineGatePassed)
                throw new InvalidOperationException("HAVENLINE V7 character Unity import gate failed. See Artifacts/HavenlineCharacterReview/V7/review.json");
        }

        private static ReviewReport RunReview()
        {
            Directory.CreateDirectory(GetArtifactDirectory());
            var report = new ReviewReport
            {
                candidateVersion = CandidateVersion,
                generatedUtc = DateTime.UtcNow.ToString("O"),
                status = "running",
                productionPromotionAllowed = false,
                humanVisualApprovalRequired = true,
                gameplayScaleApprovalRequired = true,
                legacyProductionFbxContractSatisfied = false,
                characters = new List<CharacterReport>(),
                remainingGates = new[]
                {
                    "human side-by-side review against approved turnaround art",
                    "animated pose/clipping review using shipping animation set",
                    "gameplay-scale readability in the shipping landscape camera",
                    "legacy production FBX contract only if/when a real FBX is produced"
                }
            };

            foreach (var source in Sources)
            {
                CharacterReport character;
                try { character = ReviewCharacter(source); }
                catch (Exception ex)
                {
                    character = new CharacterReport
                    {
                        character = source.character,
                        sourceFile = source.fileName,
                        expectedSha256 = source.sha256,
                        expectedBytes = source.bytes,
                        machineGatePassed = false,
                        errors = new List<string> { ex.ToString() },
                        warnings = new List<string>(),
                        captureFiles = new List<string>()
                    };
                    Debug.LogException(ex);
                }
                report.characters.Add(character);
            }

            report.machineGatePassed = report.characters.Count == Sources.Length && report.characters.All(x => x.machineGatePassed);
            report.status = report.machineGatePassed
                ? "unity_editor_import_machine_gate_passed_pending_human_and_gameplay_review"
                : "unity_editor_import_machine_gate_failed";
            WriteReport(report);
            Debug.Log($"HAVENLINE V7 character review complete: {report.status}");
            return report;
        }

        private static CharacterReport ReviewCharacter(SourceSpec source)
        {
            var assetPath = $"{StagingRoot}/{source.fileName}";
            var absolutePath = Path.GetFullPath(assetPath);
            var result = new CharacterReport
            {
                character = source.character,
                sourceFile = source.fileName,
                assetPath = assetPath,
                expectedSha256 = source.sha256,
                expectedBytes = source.bytes,
                errors = new List<string>(),
                warnings = new List<string>(),
                captureFiles = new List<string>()
            };

            if (!File.Exists(absolutePath))
            {
                result.errors.Add($"Missing V7 staging source: {assetPath}");
                return result;
            }

            result.actualBytes = new FileInfo(absolutePath).Length;
            result.actualSha256 = ComputeSha256(absolutePath);
            if (result.actualBytes != source.bytes)
                result.errors.Add($"Byte-count mismatch. Expected {source.bytes}, got {result.actualBytes}.");
            if (!string.Equals(result.actualSha256, source.sha256, StringComparison.OrdinalIgnoreCase))
                result.errors.Add($"SHA-256 mismatch. Expected {source.sha256}, got {result.actualSha256}.");

            AssetDatabase.ImportAsset(assetPath, ImportAssetOptions.ForceSynchronousImport | ImportAssetOptions.ForceUpdate);
            var imported = AssetDatabase.LoadAssetAtPath<GameObject>(assetPath);
            if (imported == null)
            {
                result.errors.Add("Unity did not import the GLB as a GameObject. Confirm com.unity.cloud.gltfast is resolved and inspect the Unity Console.");
                return result;
            }

            var previousActiveScene = SceneManager.GetActiveScene();
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Additive);
            SceneManager.SetActiveScene(scene);
            var instance = UnityEngine.Object.Instantiate(imported);
            instance.name = $"Character{source.character}_V7_ReviewInstance";
            SceneManager.MoveGameObjectToScene(instance, scene);
            instance.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            instance.transform.localScale = Vector3.one;

            try
            {
                var renderers = instance.GetComponentsInChildren<Renderer>(true);
                var skinned = instance.GetComponentsInChildren<SkinnedMeshRenderer>(true);
                result.rendererCount = renderers.Length;
                result.skinnedMeshRendererCount = skinned.Length;
                if (renderers.Length == 0) result.errors.Add("Imported character has no renderers.");
                if (skinned.Length == 0) result.errors.Add("Imported character has no SkinnedMeshRenderer; rigged skin was not preserved.");

                var uniqueBones = new HashSet<Transform>();
                var uniqueMaterials = new HashSet<Material>();
                var totalVertices = 0;
                var totalSubMeshes = 0;
                var missingMaterials = 0;
                var errorShaderMaterials = 0;

                foreach (var smr in skinned)
                {
                    smr.updateWhenOffscreen = true;
                    if (smr.sharedMesh != null)
                    {
                        totalVertices += smr.sharedMesh.vertexCount;
                        totalSubMeshes += smr.sharedMesh.subMeshCount;
                    }
                    foreach (var bone in smr.bones) if (bone != null) uniqueBones.Add(bone);
                }

                foreach (var renderer in renderers)
                {
                    foreach (var material in renderer.sharedMaterials)
                    {
                        if (material == null) { missingMaterials++; continue; }
                        uniqueMaterials.Add(material);
                        if (material.shader == null || material.shader.name.IndexOf("InternalErrorShader", StringComparison.OrdinalIgnoreCase) >= 0)
                            errorShaderMaterials++;
                    }
                }

                result.uniqueReferencedBones = uniqueBones.Count;
                result.uniqueMaterialCount = uniqueMaterials.Count;
                result.totalSkinnedVertices = totalVertices;
                result.totalSubMeshes = totalSubMeshes;
                result.missingMaterialSlots = missingMaterials;
                result.errorShaderMaterials = errorShaderMaterials;

                if (uniqueBones.Count != ExpectedJointCount)
                    result.errors.Add($"Rig joint reference count is {uniqueBones.Count}; expected {ExpectedJointCount}.");
                if (totalVertices <= 0) result.errors.Add("Imported skinned meshes contain no vertices.");
                if (missingMaterials > 0) result.errors.Add($"Imported character has {missingMaterials} missing material slot(s).");
                if (errorShaderMaterials > 0) result.errors.Add($"Imported character has {errorShaderMaterials} material(s) using Unity's internal error shader.");

                if (renderers.Length > 0)
                {
                    var bounds = CalculateBounds(renderers);
                    result.boundsCenter = SerializableVector3.From(bounds.center);
                    result.boundsSize = SerializableVector3.From(bounds.size);
                    SetupReviewLighting(bounds);
                    foreach (var view in ViewSpec.NeutralViews)
                        result.captureFiles.Add(Capture(bounds, source.character, view, false));

                    result.stressPoseBonesFound = ApplyCombinedStressPose(instance.transform, result.warnings);
                    if (result.stressPoseBonesFound < 9)
                        result.warnings.Add($"Only {result.stressPoseBonesFound}/9 stress-pose bones were found. Neutral import proof remains valid, but posed visual proof is incomplete.");
                    foreach (var view in ViewSpec.StressViews)
                        result.captureFiles.Add(Capture(bounds, source.character, view, true));
                }

                result.machineGatePassed = result.errors.Count == 0;
                return result;
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(instance);
                EditorSceneManager.CloseScene(scene, true);
                if (previousActiveScene.IsValid() && previousActiveScene.isLoaded)
                    SceneManager.SetActiveScene(previousActiveScene);
            }
        }

        private static Bounds CalculateBounds(IReadOnlyList<Renderer> renderers)
        {
            var initialized = false;
            var bounds = new Bounds(Vector3.zero, Vector3.one);
            foreach (var renderer in renderers)
            {
                if (!initialized) { bounds = renderer.bounds; initialized = true; }
                else bounds.Encapsulate(renderer.bounds);
            }
            return bounds;
        }

        private static void SetupReviewLighting(Bounds bounds)
        {
            var key = new GameObject("Review Key Light").AddComponent<Light>();
            key.type = LightType.Directional;
            key.intensity = 1.6f;
            key.shadows = LightShadows.Soft;
            key.transform.rotation = Quaternion.Euler(48f, -32f, 0f);

            var fill = new GameObject("Review Fill Light").AddComponent<Light>();
            fill.type = LightType.Directional;
            fill.intensity = 0.65f;
            fill.shadows = LightShadows.None;
            fill.transform.rotation = Quaternion.Euler(320f, 145f, 0f);

            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
            ground.name = "Review Ground";
            ground.transform.position = new Vector3(bounds.center.x, bounds.min.y - 0.01f, bounds.center.z);
            var diameter = Mathf.Max(1f, bounds.extents.magnitude * 2.5f);
            ground.transform.localScale = new Vector3(diameter / 10f, 1f, diameter / 10f);
            var collider = ground.GetComponent<Collider>();
            if (collider != null) UnityEngine.Object.DestroyImmediate(collider);
            var shader = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
            if (shader != null)
            {
                var material = new Material(shader) { name = "ReviewGroundMaterial" };
                material.color = new Color(0.16f, 0.18f, 0.21f, 1f);
                ground.GetComponent<Renderer>().sharedMaterial = material;
            }
        }

        private static string Capture(Bounds neutralBounds, int character, ViewSpec view, bool stressPose)
        {
            var cameraObject = new GameObject($"Review Camera {view.name}");
            var camera = cameraObject.AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.055f, 0.065f, 0.08f, 1f);
            camera.orthographic = true;
            camera.nearClipPlane = 0.01f;
            camera.farClipPlane = 1000f;
            camera.allowHDR = true;

            var center = neutralBounds.center;
            var radius = Mathf.Max(0.5f, neutralBounds.extents.magnitude);
            var direction = view.cameraDirection.normalized;
            camera.transform.position = center + direction * (radius * 4f + 1f);
            camera.transform.LookAt(center, Vector3.up);

            var framingMargin = stressPose ? 1.32f : 1.15f;
            var maxUp = 0f;
            var maxRight = 0f;
            foreach (var corner in GetBoundsCorners(neutralBounds))
            {
                var offset = corner - center;
                maxUp = Mathf.Max(maxUp, Mathf.Abs(Vector3.Dot(offset, camera.transform.up)));
                maxRight = Mathf.Max(maxRight, Mathf.Abs(Vector3.Dot(offset, camera.transform.right)));
            }
            camera.orthographicSize = Mathf.Max(0.25f, Mathf.Max(maxUp, maxRight) * framingMargin);

            var renderTexture = new RenderTexture(CaptureSize, CaptureSize, 24, RenderTextureFormat.ARGB32) { antiAliasing = 1 };
            var texture = new Texture2D(CaptureSize, CaptureSize, TextureFormat.RGBA32, false, false);
            var previous = RenderTexture.active;
            try
            {
                camera.targetTexture = renderTexture;
                RenderTexture.active = renderTexture;
                camera.Render();
                texture.ReadPixels(new Rect(0, 0, CaptureSize, CaptureSize), 0, 0, false);
                texture.Apply(false, false);
                var characterDirectory = Path.Combine(GetArtifactDirectory(), $"Character{character}");
                Directory.CreateDirectory(characterDirectory);
                var output = Path.Combine(characterDirectory, $"Character{character}_{(stressPose ? "stress" : "neutral")}_{view.name}.png");
                File.WriteAllBytes(output, texture.EncodeToPNG());
                return NormalizeProjectRelativePath(output);
            }
            finally
            {
                camera.targetTexture = null;
                RenderTexture.active = previous;
                UnityEngine.Object.DestroyImmediate(texture);
                renderTexture.Release();
                UnityEngine.Object.DestroyImmediate(renderTexture);
                UnityEngine.Object.DestroyImmediate(cameraObject);
            }
        }

        private static int ApplyCombinedStressPose(Transform root, ICollection<string> warnings)
        {
            var applied = 0;
            applied += ApplyLocalAxisRotation(root, "mixamorigSpine", Vector3.right, 8f, warnings);
            applied += ApplyLocalAxisRotation(root, "mixamorigSpine1", Vector3.right, 10f, warnings);
            applied += ApplyLocalAxisRotation(root, "mixamorigSpine2", Vector3.right, 12f, warnings);
            applied += ApplyLocalAxisRotation(root, "mixamorigLeftShoulder", Vector3.forward, 25f, warnings);
            applied += ApplyLocalAxisRotation(root, "mixamorigRightShoulder", Vector3.forward, -25f, warnings);
            applied += ApplyLocalAxisRotation(root, "mixamorigLeftArm", Vector3.forward, 30f, warnings);
            applied += ApplyLocalAxisRotation(root, "mixamorigRightArm", Vector3.forward, -30f, warnings);
            applied += ApplyLocalAxisRotation(root, "mixamorigNeck", Vector3.up, 30f, warnings);
            applied += ApplyLocalAxisRotation(root, "mixamorigHead", Vector3.up, 15f, warnings);
            return applied;
        }

        private static int ApplyLocalAxisRotation(Transform root, string boneName, Vector3 axis, float degrees, ICollection<string> warnings)
        {
            var bone = FindTransform(root, boneName);
            if (bone == null) { warnings.Add($"Stress-pose bone not found: {boneName}"); return 0; }
            bone.localRotation = bone.localRotation * Quaternion.AngleAxis(degrees, axis);
            return 1;
        }

        private static Transform FindTransform(Transform root, string name)
        {
            foreach (var transform in root.GetComponentsInChildren<Transform>(true))
                if (string.Equals(transform.name, name, StringComparison.Ordinal)) return transform;
            return null;
        }

        private static Vector3[] GetBoundsCorners(Bounds bounds)
        {
            var min = bounds.min;
            var max = bounds.max;
            return new[]
            {
                new Vector3(min.x, min.y, min.z), new Vector3(max.x, min.y, min.z),
                new Vector3(min.x, max.y, min.z), new Vector3(max.x, max.y, min.z),
                new Vector3(min.x, min.y, max.z), new Vector3(max.x, min.y, max.z),
                new Vector3(min.x, max.y, max.z), new Vector3(max.x, max.y, max.z),
            };
        }

        private static string ComputeSha256(string path)
        {
            using var stream = File.OpenRead(path);
            using var sha = SHA256.Create();
            return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", string.Empty).ToLowerInvariant();
        }

        private static string GetArtifactDirectory() => Path.Combine(Directory.GetCurrentDirectory(), ArtifactRoot);

        private static string NormalizeProjectRelativePath(string absolutePath)
        {
            var root = Directory.GetCurrentDirectory().TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar) + Path.DirectorySeparatorChar;
            var normalized = Path.GetFullPath(absolutePath);
            return normalized.StartsWith(root, StringComparison.OrdinalIgnoreCase)
                ? normalized.Substring(root.Length).Replace('\\', '/')
                : normalized.Replace('\\', '/');
        }

        private static void WriteReport(ReviewReport report)
        {
            File.WriteAllText(Path.Combine(GetArtifactDirectory(), "review.json"), JsonUtility.ToJson(report, true));
        }

        private readonly struct SourceSpec
        {
            public SourceSpec(int character, string fileName, string sha256, long bytes)
            { this.character = character; this.fileName = fileName; this.sha256 = sha256; this.bytes = bytes; }
            public readonly int character;
            public readonly string fileName;
            public readonly string sha256;
            public readonly long bytes;
        }

        private readonly struct ViewSpec
        {
            public ViewSpec(string name, Vector3 cameraDirection)
            { this.name = name; this.cameraDirection = cameraDirection; }
            public readonly string name;
            public readonly Vector3 cameraDirection;
            public static readonly ViewSpec[] NeutralViews =
            {
                new ViewSpec("front", Vector3.forward),
                new ViewSpec("threeQuarter", new Vector3(1f, 0f, 1f).normalized),
                new ViewSpec("side", Vector3.right),
                new ViewSpec("back", Vector3.back),
            };
            public static readonly ViewSpec[] StressViews =
            {
                new ViewSpec("front", Vector3.forward),
                new ViewSpec("threeQuarter", new Vector3(1f, 0f, 1f).normalized),
            };
        }

        [Serializable]
        private sealed class ReviewReport
        {
            public string candidateVersion;
            public string generatedUtc;
            public string status;
            public bool machineGatePassed;
            public bool productionPromotionAllowed;
            public bool humanVisualApprovalRequired;
            public bool gameplayScaleApprovalRequired;
            public bool legacyProductionFbxContractSatisfied;
            public List<CharacterReport> characters;
            public string[] remainingGates;
        }

        [Serializable]
        private sealed class CharacterReport
        {
            public int character;
            public string sourceFile;
            public string assetPath;
            public string expectedSha256;
            public string actualSha256;
            public long expectedBytes;
            public long actualBytes;
            public bool machineGatePassed;
            public int rendererCount;
            public int skinnedMeshRendererCount;
            public int uniqueReferencedBones;
            public int uniqueMaterialCount;
            public int totalSkinnedVertices;
            public int totalSubMeshes;
            public int missingMaterialSlots;
            public int errorShaderMaterials;
            public int stressPoseBonesFound;
            public SerializableVector3 boundsCenter;
            public SerializableVector3 boundsSize;
            public List<string> captureFiles;
            public List<string> warnings;
            public List<string> errors;
        }

        [Serializable]
        private struct SerializableVector3
        {
            public float x;
            public float y;
            public float z;
            public static SerializableVector3 From(Vector3 value) => new SerializableVector3 { x = value.x, y = value.y, z = value.z };
        }
    }
}
#endif
