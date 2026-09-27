using UnityEngine;
using VRM; // This namespace is still correct
using System.IO; // For reading the file from the path
using SFB; // For the Standalone File Browser
using System.Threading.Tasks; // For async operations
using UniGLTF; // For RuntimeGltfInstance
using VRMShaders; // For RuntimeOnlyAwaitCaller
using uLipSync; // For uLipSync components

public class VrmLoader : MonoBehaviour
{
    // Assign your default avatar in the Unity Inspector
    [Tooltip("The currently active avatar in the scene.")]
    public GameObject currentAvatar;
    
    [Header("Avatar Setup References")]
    [Tooltip("The animator controller to apply to new avatars")]
    public RuntimeAnimatorController animatorController;
    
    [Tooltip("The uLipSync profile to use for lip sync")]
    public uLipSync.Profile lipSyncProfile;
    
    [Tooltip("Reference to the Audio GameObject for uLipSync")]
    public GameObject audioObject;

    // This method is called by your UI button. It's the entry point.
    public void OpenVrmFilePicker()
    {
        var extensions = new[] {
            new ExtensionFilter("VRM Files", "vrm"),
        };

        // Open the file browser. Note this is not an async operation anymore.
        string[] paths = StandaloneFileBrowser.OpenFilePanel("Select VRM Avatar", "", extensions, false);

        if (paths.Length > 0 && !string.IsNullOrEmpty(paths[0]))
        {
            // We got a path, now load the VRM file.
            LoadVrm(paths[0]);
        }
    }

    // This method reads the file bytes and starts the import process.
    private async void LoadVrm(string path)
    {
        Debug.Log($"Starting to load VRM from: {path}");
        
        // Read all the bytes from the selected file.
        byte[] vrmBytes = File.ReadAllBytes(path);
        Debug.Log($"Read {vrmBytes.Length} bytes from file");

        try
        {
            // Use VrmUtility.LoadBytesAsync for proper VRM loading
            // RuntimeOnlyAwaitCaller is recommended for runtime loading
            var awaitCaller = new RuntimeOnlyAwaitCaller();
            Debug.Log("Starting VRM load async...");
            var instance = await VrmUtility.LoadBytesAsync(path, vrmBytes, awaitCaller);
            
            Debug.Log($"VRM loaded successfully. Root object: {instance.Root.name}");
            
            // Extract the GameObject from the RuntimeGltfInstance
            OnVrmLoadComplete(instance.Root);
        }
        catch (System.Exception ex)
        {
            Debug.LogError($"VRM loading failed: {ex.Message}\nStack trace: {ex.StackTrace}");
            OnVrmLoadComplete(null);
        }
    }

    // This is the "callback" method that runs after the model is loaded.
    private void OnVrmLoadComplete(GameObject newAvatar)
    {
        Debug.Log($"OnVrmLoadComplete called with avatar: {(newAvatar != null ? newAvatar.name : "null")}");
        
        // First, check if loading was successful.
        if (newAvatar == null)
        {
            Debug.LogError("VRM loading failed - newAvatar is null.");
            return;
        }

        // Store the old avatar's transform data before destroying it
        Vector3 oldPosition = Vector3.zero;
        Quaternion oldRotation = Quaternion.identity;
        Vector3 oldScale = Vector3.one;
        
        if (currentAvatar != null)
        {
            oldPosition = currentAvatar.transform.position;
            oldRotation = currentAvatar.transform.rotation;
            oldScale = currentAvatar.transform.localScale;
            
            Debug.Log($"Destroying old avatar: {currentAvatar.name} at position {oldPosition}");
            Destroy(currentAvatar);
        }

        // 2. The loaded model is our new avatar.
        currentAvatar = newAvatar;
        currentAvatar.name = "UserVRMAvatar";

        // 3. Ensure the new avatar is active and positioned correctly.
        currentAvatar.SetActive(true);
        
        // Force the avatar to be at the exact same position as the old one
        currentAvatar.transform.position = oldPosition;
        currentAvatar.transform.rotation = oldRotation;
        currentAvatar.transform.localScale = oldScale;
        
        // Check if the scale is reasonable, if too small make it bigger
        var bounds = GetModelBounds(currentAvatar);
        Debug.Log($"Model bounds: {bounds.size}");
        
        // Additional debugging info
        Debug.Log($"Avatar children count: {currentAvatar.transform.childCount}");
        Debug.Log($"Avatar has renderers: {currentAvatar.GetComponentsInChildren<Renderer>().Length}");
        Debug.Log($"Avatar layer: {currentAvatar.layer}");
        
        // Check if any renderers are disabled
        var renderers = currentAvatar.GetComponentsInChildren<Renderer>();
        foreach (var renderer in renderers)
        {
            Debug.Log($"Renderer {renderer.name}: enabled={renderer.enabled}, visible={renderer.isVisible}");
            // Force enable all renderers
            renderer.enabled = true;
        }
        
        // Ensure all child objects are active
        SetAllChildrenActive(currentAvatar, true);
        
        // If position is at origin and we had an old avatar, make sure we're at the right spot
        if (oldPosition != Vector3.zero)
        {
            currentAvatar.transform.position = oldPosition;
        }
        
        Debug.Log($"Avatar loaded successfully! Final Position: {currentAvatar.transform.position}, Scale: {currentAvatar.transform.localScale}");
        Debug.Log($"Avatar bounds after positioning: {GetModelBounds(currentAvatar)}");
        
        // Set up all the necessary components on the new avatar
        SetupAvatarComponents(currentAvatar);
        
        // Force a camera look at the model if possible
        var camera = Camera.main;
        if (camera != null)
        {
            Debug.Log($"Main camera position: {camera.transform.position}, looking at: {camera.transform.forward}");
        }
    }
    
    // Method to set up all necessary components on the newly loaded avatar
    private void SetupAvatarComponents(GameObject avatar)
    {
        Debug.Log("Setting up avatar components...");
        
        // 1. Set up Animator with MITSUHA controller
        SetupAnimator(avatar);
        
        // 2. Set up uLipSync components (including BlendShape)
        SetupLipSync(avatar);
        
        // 3. Set up animActivate script
        SetupAnimActivate(avatar);
        
        // 4. Set up Blinker script
        SetupBlinker(avatar);
        
        // 5. Set up VRM Look At components
        SetupVRMLookAt(avatar);
        
        // 6. Update Audio object's OnLipSyncUpdate to point to new avatar
        UpdateAudioLipSyncReference(avatar);
        
        Debug.Log("Avatar component setup complete!");
    }
    
    private void SetupAnimator(GameObject avatar)
    {
        // Check if avatar already has an Animator
        Animator animator = avatar.GetComponent<Animator>();
        if (animator == null)
        {
            Debug.Log("Adding Animator component to avatar");
            animator = avatar.AddComponent<Animator>();
        }
        
        // Try to find the MITSUHA controller if not assigned in inspector
        if (animatorController == null)
        {
            Debug.Log("Animator controller not assigned, searching for MITSUHA controller...");
            
            // First try Resources folder
            animatorController = Resources.Load<RuntimeAnimatorController>("MITSUHA");
            
            // If not found, try to find it in all loaded assets
            if (animatorController == null)
            {
                var controllers = Resources.FindObjectsOfTypeAll<RuntimeAnimatorController>();
                Debug.Log($"Found {controllers.Length} animator controllers in project");
                
                foreach (var controller in controllers)
                {
                    Debug.Log($"Found controller: {controller.name}");
                    if (controller.name == "MITSUHA" || controller.name.Contains("MITSUHA"))
                    {
                        animatorController = controller;
                        Debug.Log($"Selected controller: {controller.name}");
                        break;
                    }
                }
            }
            
            if (animatorController == null)
            {
                Debug.LogError("MITSUHA controller not found! Please assign it manually in the inspector.");
                Debug.LogError("Make sure the MITSUHA.controller file is in your project and try the 'Auto-Assign References' context menu option.");
                return;
            }
        }
        
        // Apply the controller
        if (animatorController != null)
        {
            animator.runtimeAnimatorController = animatorController;
            Debug.Log($"Successfully applied animator controller: {animatorController.name}");
            
            // Verify it was applied
            if (animator.runtimeAnimatorController != null)
            {
                Debug.Log($"Controller verification: {animator.runtimeAnimatorController.name} is now assigned");
            }
            else
            {
                Debug.LogError("Failed to assign controller - controller is null after assignment");
            }
        }
        else
        {
            Debug.LogError("Cannot apply null animator controller");
        }
    }
    
    private void SetupLipSync(GameObject avatar)
    {
        // Check if avatar already has uLipSyncBlendShape component (this is the main one we need)
        uLipSyncBlendShape lipSyncBlendShape = avatar.GetComponent<uLipSyncBlendShape>();
        if (lipSyncBlendShape == null)
        {
            Debug.Log("Adding uLipSyncBlendShape component to avatar");
            lipSyncBlendShape = avatar.AddComponent<uLipSyncBlendShape>();
        }
        
        // Set up VRM-specific blend shape mappings
        SetupVRMBlendShapeMapping(lipSyncBlendShape, avatar);
        
        Debug.Log("uLipSyncBlendShape setup complete");
    }
    
    private void SetupVRMBlendShapeMapping(uLipSyncBlendShape lipSyncBlendShape, GameObject avatar)
    {
        Debug.Log("Setting up VRM blend shape mapping...");
        
        // Get all SkinnedMeshRenderers in the avatar
        var skinnedMeshRenderers = avatar.GetComponentsInChildren<SkinnedMeshRenderer>();
        
        if (skinnedMeshRenderers.Length == 0)
        {
            Debug.LogWarning("No SkinnedMeshRenderer found on avatar - cannot set up lip sync");
            return;
        }
        
        // Find the main face mesh (usually the one with the most blend shapes)
        SkinnedMeshRenderer faceMesh = null;
        int maxBlendShapes = 0;
        
        foreach (var renderer in skinnedMeshRenderers)
        {
            if (renderer.sharedMesh != null && renderer.sharedMesh.blendShapeCount > maxBlendShapes)
            {
                maxBlendShapes = renderer.sharedMesh.blendShapeCount;
                faceMesh = renderer;
            }
        }
        
        if (faceMesh == null)
        {
            Debug.LogWarning("No mesh with blend shapes found - cannot set up lip sync");
            return;
        }
        
        Debug.Log($"Found face mesh: {faceMesh.name} with {faceMesh.sharedMesh.blendShapeCount} blend shapes");
        
        // Set the skinned mesh renderer
        lipSyncBlendShape.skinnedMeshRenderer = faceMesh;
        
        // Map VRM blend shapes to phonemes
        // VRM standard blend shape names and their phoneme mappings
        var vrmBlendShapeMap = new System.Collections.Generic.Dictionary<string, string>
        {
            // VRM standard mouth shapes
            {"A", "A"},
            {"I", "I"}, 
            {"U", "U"},
            {"E", "E"},
            {"O", "O"},
            // Alternative names that might be used
            {"a", "A"},
            {"i", "I"},
            {"u", "U"},
            {"e", "E"},
            {"o", "O"},
            // Sometimes with prefixes
            {"mouth_a", "A"},
            {"mouth_i", "I"},
            {"mouth_u", "U"},
            {"mouth_e", "E"},
            {"mouth_o", "O"},
            {"Mouth_A", "A"},
            {"Mouth_I", "I"},
            {"Mouth_U", "U"},
            {"Mouth_E", "E"},
            {"Mouth_O", "O"},
            // Common VRM phoneme patterns (like blendShape1.Mouth_aa)
            {"Mouth_aa", "A"},  // Double vowel for A sound
            {"Mouth_ih", "I"},  // ih sound for I
            {"Mouth_ou", "U"},  // ou sound for U  
            {"Mouth_ee", "E"},  // ee sound for E
            {"Mouth_oh", "O"},  // oh sound for O
            // Alternative phoneme patterns
            {"mouth_aa", "A"},
            {"mouth_ih", "I"},
            {"mouth_ou", "U"},
            {"mouth_ee", "E"},
            {"mouth_oh", "O"}
        };
        
        // Get available blend shapes from the mesh
        var mesh = faceMesh.sharedMesh;
        var availableBlendShapes = new System.Collections.Generic.List<string>();
        
        for (int i = 0; i < mesh.blendShapeCount; i++)
        {
            string blendShapeName = mesh.GetBlendShapeName(i);
            availableBlendShapes.Add(blendShapeName);
            Debug.Log($"Available blend shape: {blendShapeName}");
        }
        
        // Create phoneme mappings for found blend shapes
        var phonemeMappings = new System.Collections.Generic.List<uLipSyncBlendShape.BlendShapeInfo>();
        
        // First, try exact matches
        foreach (var kvp in vrmBlendShapeMap)
        {
            string vrmBlendShapeName = kvp.Key;
            string phoneme = kvp.Value;
            
            // Check if this blend shape exists
            int blendShapeIndex = -1;
            for (int i = 0; i < mesh.blendShapeCount; i++)
            {
                if (mesh.GetBlendShapeName(i) == vrmBlendShapeName)
                {
                    blendShapeIndex = i;
                    break;
                }
            }
            
            if (blendShapeIndex >= 0)
            {
                var blendShapeInfo = new uLipSyncBlendShape.BlendShapeInfo();
                blendShapeInfo.phoneme = phoneme;
                blendShapeInfo.index = blendShapeIndex;
                blendShapeInfo.maxWeight = 1.0f;
                
                phonemeMappings.Add(blendShapeInfo);
                Debug.Log($"Mapped phoneme '{phoneme}' to blend shape '{vrmBlendShapeName}' (index {blendShapeIndex})");
            }
        }
        
        // If no exact matches found, try pattern matching (e.g., blendShape1.Mouth_aa)
        if (phonemeMappings.Count == 0)
        {
            Debug.Log("No exact matches found, trying pattern matching...");
            
            for (int i = 0; i < mesh.blendShapeCount; i++)
            {
                string blendShapeName = mesh.GetBlendShapeName(i);
                string phoneme = null;
                
                // Check for patterns like "blendShape1.Mouth_aa" or ending with phoneme patterns
                if (blendShapeName.EndsWith("Mouth_aa") || blendShapeName.EndsWith("mouth_aa") || 
                    blendShapeName.EndsWith("_aa") || blendShapeName.EndsWith("_a") || blendShapeName.EndsWith("_A"))
                {
                    phoneme = "A";
                }
                else if (blendShapeName.EndsWith("Mouth_ih") || blendShapeName.EndsWith("mouth_ih") || 
                         blendShapeName.EndsWith("_ih") || blendShapeName.EndsWith("_i") || blendShapeName.EndsWith("_I"))
                {
                    phoneme = "I";
                }
                else if (blendShapeName.EndsWith("Mouth_ou") || blendShapeName.EndsWith("mouth_ou") || 
                         blendShapeName.EndsWith("_ou") || blendShapeName.EndsWith("_u") || blendShapeName.EndsWith("_U"))
                {
                    phoneme = "U";
                }
                else if (blendShapeName.EndsWith("Mouth_ee") || blendShapeName.EndsWith("mouth_ee") || 
                         blendShapeName.EndsWith("_ee") || blendShapeName.EndsWith("_e") || blendShapeName.EndsWith("_E"))
                {
                    phoneme = "E";
                }
                else if (blendShapeName.EndsWith("Mouth_oh") || blendShapeName.EndsWith("mouth_oh") || 
                         blendShapeName.EndsWith("_oh") || blendShapeName.EndsWith("_o") || blendShapeName.EndsWith("_O"))
                {
                    phoneme = "O";
                }
                
                if (phoneme != null)
                {
                    var blendShapeInfo = new uLipSyncBlendShape.BlendShapeInfo();
                    blendShapeInfo.phoneme = phoneme;
                    blendShapeInfo.index = i;
                    blendShapeInfo.maxWeight = 1.0f;
                    
                    phonemeMappings.Add(blendShapeInfo);
                    Debug.Log($"Pattern-matched phoneme '{phoneme}' to blend shape '{blendShapeName}' (index {i})");
                }
            }
        }
        
        if (phonemeMappings.Count == 0)
        {
            Debug.LogWarning("No VRM standard blend shapes found. Available blend shapes:");
            foreach (var name in availableBlendShapes)
            {
                Debug.LogWarning($"  - {name}");
            }
            Debug.LogWarning("You may need to manually configure the blend shape mappings in the uLipSyncBlendShape component.");
        }
        else
        {
            // Apply the mappings to the component
            lipSyncBlendShape.blendShapes = phonemeMappings;
            Debug.Log($"Successfully mapped {phonemeMappings.Count} phonemes to VRM blend shapes");
        }
    }
    
    private void SetupAnimActivate(GameObject avatar)
    {
        // Check if avatar already has animActivate component
        animActivate animActivateScript = avatar.GetComponent<animActivate>();
        if (animActivateScript == null)
        {
            Debug.Log("Adding animActivate component to avatar");
            animActivateScript = avatar.AddComponent<animActivate>();
        }
        
        Debug.Log("animActivate setup complete");
    }
    
    private void SetupBlinker(GameObject avatar)
    {
        // Check if avatar already has Blinker component
        var blinker = avatar.GetComponent<Blinker>();
        if (blinker == null)
        {
            Debug.Log("Adding Blinker component to avatar");
            blinker = avatar.AddComponent<Blinker>();
        }
        
        Debug.Log("Blinker setup complete");
    }
    
    private void SetupVRMLookAt(GameObject avatar)
    {
        Debug.Log("Setting up VRM Look At components...");
        
        // First, set up VRM Look At Bone Applyer
        SetupVRMLookAtBoneApplyer(avatar);
        
        // Then, configure the existing VRM Look At Head component
        ConfigureVRMLookAtHead(avatar);
        
        Debug.Log("VRM Look At setup complete");
    }
    
    private void SetupVRMLookAtBoneApplyer(GameObject avatar)
    {
        // Check if avatar already has VRMLookAtBoneApplyer component
        var boneApplyerComponent = avatar.GetComponent("VRMLookAtBoneApplyer");
        if (boneApplyerComponent == null)
        {
            Debug.Log("Adding VRMLookAtBoneApplyer component to avatar");
            // Try to add the component using reflection to handle different VRM versions
            var vrmAssembly = System.Reflection.Assembly.GetAssembly(typeof(VRM.VRMLookAtHead));
            var boneApplyerType = vrmAssembly.GetType("VRM.VRMLookAtBoneApplyer");
            
            if (boneApplyerType != null)
            {
                boneApplyerComponent = avatar.AddComponent(boneApplyerType);
                Debug.Log("Successfully added VRMLookAtBoneApplyer component");
            }
            else
            {
                Debug.LogError("VRMLookAtBoneApplyer type not found in VRM assembly");
                return;
            }
        }
        
        // Find the head transform (should be the same as the one used in VRMLookAtHead)
        Transform headTransform = FindHeadTransform(avatar);
        if (headTransform != null)
        {
            // Try multiple possible property names for Head
            bool headSet = TrySetComponentTransform(boneApplyerComponent, headTransform, "Head", "head", "HeadTransform");
            if (headSet)
            {
                Debug.Log($"Set VRMLookAtBoneApplyer Head to: {headTransform.name}");
            }
            else
            {
                Debug.LogWarning($"Could not set Head transform on VRMLookAtBoneApplyer");
            }
        }
        else
        {
            Debug.LogWarning("Could not find head transform for VRMLookAtBoneApplyer");
        }
        
        // Find left and right eye transforms
        Transform leftEyeTransform = FindEyeTransform(avatar, true);  // true for left eye
        Transform rightEyeTransform = FindEyeTransform(avatar, false); // false for right eye
        
        if (leftEyeTransform != null)
        {
            // Try multiple possible property names for LeftEye
            bool leftEyeSet = TrySetComponentTransform(boneApplyerComponent, leftEyeTransform, "LeftEye", "leftEye", "LeftEyeTransform", "EyeLeft");
            if (leftEyeSet)
            {
                Debug.Log($"Set VRMLookAtBoneApplyer LeftEye to: {leftEyeTransform.name}");
            }
            else
            {
                Debug.LogWarning($"Could not set LeftEye transform on VRMLookAtBoneApplyer");
            }
        }
        else
        {
            Debug.LogWarning("Could not find left eye transform for VRMLookAtBoneApplyer");
        }
        
        if (rightEyeTransform != null)
        {
            // Try multiple possible property names for RightEye
            bool rightEyeSet = TrySetComponentTransform(boneApplyerComponent, rightEyeTransform, "RightEye", "rightEye", "RightEyeTransform", "EyeRight");
            if (rightEyeSet)
            {
                Debug.Log($"Set VRMLookAtBoneApplyer RightEye to: {rightEyeTransform.name}");
            }
            else
            {
                Debug.LogWarning($"Could not set RightEye transform on VRMLookAtBoneApplyer");
            }
        }
        else
        {
            Debug.LogWarning("Could not find right eye transform for VRMLookAtBoneApplyer");
        }
        
        Debug.Log("VRMLookAtBoneApplyer setup complete");
    }
    
    // Helper method to safely set component properties using reflection
    private void SetComponentProperty(UnityEngine.Component component, string propertyName, object value)
    {
        try
        {
            var componentType = component.GetType();
            var property = componentType.GetProperty(propertyName);
            
            if (property != null && property.CanWrite)
            {
                // Check if the property type matches what we're trying to assign
                if (property.PropertyType.IsAssignableFrom(value.GetType()))
                {
                    property.SetValue(component, value);
                    Debug.Log($"Successfully set {componentType.Name}.{propertyName} to {value}");
                }
                else
                {
                    Debug.LogWarning($"Property '{propertyName}' type mismatch. Expected: {property.PropertyType.Name}, Got: {value.GetType().Name}");
                }
            }
            else
            {
                // Try field instead of property
                var field = componentType.GetField(propertyName);
                if (field != null)
                {
                    // Check if the field type matches what we're trying to assign
                    if (field.FieldType.IsAssignableFrom(value.GetType()))
                    {
                        field.SetValue(component, value);
                        Debug.Log($"Successfully set {componentType.Name}.{propertyName} field to {value}");
                    }
                    else
                    {
                        Debug.LogWarning($"Field '{propertyName}' type mismatch. Expected: {field.FieldType.Name}, Got: {value.GetType().Name}");
                    }
                }
                else
                {
                    Debug.LogWarning($"Property/Field '{propertyName}' not found on {componentType.Name}");
                    
                    // List all available properties and fields for debugging
                    Debug.Log($"Available properties on {componentType.Name}:");
                    foreach (var prop in componentType.GetProperties())
                    {
                        Debug.Log($"  - {prop.Name} ({prop.PropertyType.Name}) - CanRead: {prop.CanRead}, CanWrite: {prop.CanWrite}");
                    }
                    
                    Debug.Log($"Available fields on {componentType.Name}:");
                    foreach (var fieldInfo in componentType.GetFields())
                    {
                        Debug.Log($"  - {fieldInfo.Name} ({fieldInfo.FieldType.Name})");
                    }
                }
            }
        }
        catch (System.Exception ex)
        {
            Debug.LogError($"Failed to set {propertyName} on {component.GetType().Name}: {ex.Message}");
        }
    }
    
    // Helper method to try setting a transform using multiple possible property names
    private bool TrySetComponentTransform(UnityEngine.Component component, Transform transform, params string[] propertyNames)
    {
        var componentType = component.GetType();
        
        foreach (string propertyName in propertyNames)
        {
            try
            {
                // Try property first
                var property = componentType.GetProperty(propertyName);
                if (property != null && property.CanWrite)
                {
                    if (property.PropertyType.IsAssignableFrom(typeof(Transform)))
                    {
                        property.SetValue(component, transform);
                        Debug.Log($"Successfully set {componentType.Name}.{propertyName} property to {transform.name}");
                        return true;
                    }
                    else
                    {
                        Debug.Log($"Property '{propertyName}' found but type mismatch: Expected {property.PropertyType.Name}, got Transform");
                    }
                }
                
                // Try field if property didn't work
                var field = componentType.GetField(propertyName);
                if (field != null)
                {
                    if (field.FieldType.IsAssignableFrom(typeof(Transform)))
                    {
                        field.SetValue(component, transform);
                        Debug.Log($"Successfully set {componentType.Name}.{propertyName} field to {transform.name}");
                        return true;
                    }
                    else
                    {
                        Debug.Log($"Field '{propertyName}' found but type mismatch: Expected {field.FieldType.Name}, got Transform");
                    }
                }
            }
            catch (System.Exception ex)
            {
                Debug.LogWarning($"Failed to set {propertyName}: {ex.Message}");
            }
        }
        
        return false;
    }
    
    private void ConfigureVRMLookAtHead(GameObject avatar)
    {
        // Find the existing VRMLookAtHead component
        VRM.VRMLookAtHead lookAtHead = avatar.GetComponent<VRM.VRMLookAtHead>();
        if (lookAtHead == null)
        {
            Debug.LogWarning("VRMLookAtHead component not found on avatar - this should exist by default on VRM models");
            return;
        }
        
        // Change Update Type to LateUpdate
        lookAtHead.UpdateType = VRM.UpdateType.LateUpdate;
        Debug.Log("Changed VRMLookAtHead UpdateType to LateUpdate");
        
        // Find and set the target to Square object
        GameObject squareTarget = GameObject.Find("Square");
        if (squareTarget != null)
        {
            lookAtHead.Target = squareTarget.transform;
            Debug.Log($"Set VRMLookAtHead Target to: {squareTarget.name}");
        }
        else
        {
            Debug.LogWarning("Could not find 'Square' GameObject to set as VRMLookAtHead target");
            
            // Try alternative names
            var alternativeTargets = new string[] { "square", "Square (Transform)", "LookTarget", "Target" };
            foreach (var targetName in alternativeTargets)
            {
                GameObject altTarget = GameObject.Find(targetName);
                if (altTarget != null)
                {
                    lookAtHead.Target = altTarget.transform;
                    Debug.Log($"Set VRMLookAtHead Target to alternative: {altTarget.name}");
                    break;
                }
            }
        }
        
        Debug.Log("VRMLookAtHead configuration complete");
    }
    
    private Transform FindHeadTransform(GameObject avatar)
    {
        // The head transform should be the same as what's already set in VRMLookAtHead
        VRM.VRMLookAtHead lookAtHead = avatar.GetComponent<VRM.VRMLookAtHead>();
        if (lookAtHead != null && lookAtHead.Head != null)
        {
            Debug.Log($"Using head transform from existing VRMLookAtHead: {lookAtHead.Head.name}");
            return lookAtHead.Head;
        }
        
        // If not found in VRMLookAtHead, search manually
        Debug.Log("Searching for head transform manually...");
        
        // Common head transform names in VRM models
        var headNames = new string[]
        {
            "Head", "head", "J_Bip_C_Head", "Bip_C_Head", "mixamorig:Head", 
            "Armature/Hips/Spine/Chest/Neck/Head", "Neck/Head"
        };
        
        foreach (var headName in headNames)
        {
            Transform headTransform = FindTransformByName(avatar.transform, headName);
            if (headTransform != null)
            {
                Debug.Log($"Found head transform: {headTransform.name}");
                return headTransform;
            }
        }
        
        Debug.LogWarning("Could not find head transform");
        return null;
    }
    
    private Transform FindEyeTransform(GameObject avatar, bool isLeftEye)
    {
        string eyeSide = isLeftEye ? "Left" : "Right";
        Debug.Log($"Searching for {eyeSide} eye transform...");
        
        // Common eye transform names based on the screenshots you provided
        var eyeNames = new string[]
        {
            // Standard patterns from your screenshots
            isLeftEye ? "LeftEye" : "RightEye",
            isLeftEye ? "Left_Eye" : "Right_Eye", 
            isLeftEye ? "J_Adj_L_FaceEye" : "J_Adj_R_FaceEye",
            isLeftEye ? "L_eye" : "R_eye",
            isLeftEye ? "l_eye" : "r_eye",
            isLeftEye ? "Eye_L" : "Eye_R",
            isLeftEye ? "eye_l" : "eye_r",
            isLeftEye ? "EyeLeft" : "EyeRight",
            isLeftEye ? "eyeLeft" : "eyeRight",
            
            // Mixamo patterns
            isLeftEye ? "mixamorig:LeftEye" : "mixamorig:RightEye",
            
            // VRM/MMD patterns  
            isLeftEye ? "左目" : "右目", // Japanese characters for left/right eye
            
            // Other common patterns
            isLeftEye ? "L.Eye" : "R.Eye",
            isLeftEye ? "L_Eye" : "R_Eye",
            isLeftEye ? "eye.L" : "eye.R",
            isLeftEye ? "Eye.L" : "Eye.R"
        };
        
        foreach (var eyeName in eyeNames)
        {
            Transform eyeTransform = FindTransformByName(avatar.transform, eyeName);
            if (eyeTransform != null)
            {
                Debug.Log($"Found {eyeSide} eye transform: {eyeTransform.name}");
                return eyeTransform;
            }
        }
        
        // If exact names don't work, try partial matching
        Debug.Log($"Trying partial matching for {eyeSide} eye...");
        Transform[] allTransforms = avatar.GetComponentsInChildren<Transform>();
        
        foreach (Transform t in allTransforms)
        {
            string transformName = t.name.ToLower();
            
            // Check for left eye patterns
            if (isLeftEye)
            {
                if ((transformName.Contains("left") || transformName.Contains("l_") || transformName.Contains("_l")) && 
                    transformName.Contains("eye"))
                {
                    Debug.Log($"Found {eyeSide} eye transform by partial match: {t.name}");
                    return t;
                }
            }
            // Check for right eye patterns
            else
            {
                if ((transformName.Contains("right") || transformName.Contains("r_") || transformName.Contains("_r")) && 
                    transformName.Contains("eye"))
                {
                    Debug.Log($"Found {eyeSide} eye transform by partial match: {t.name}");
                    return t;
                }
            }
        }
        
        Debug.LogWarning($"Could not find {eyeSide} eye transform");
        return null;
    }
    
    private Transform FindTransformByName(Transform parent, string name)
    {
        // Check if the parent itself matches
        if (parent.name == name)
            return parent;
        
        // Search all children recursively
        foreach (Transform child in parent)
        {
            Transform result = FindTransformByName(child, name);
            if (result != null)
                return result;
        }
        
        return null;
    }
    
    private void UpdateAudioLipSyncReference(GameObject newAvatar)
    {
        Debug.Log("Updating Audio object's lip sync reference...");
        
        // Find the Audio object if not assigned
        if (audioObject == null)
        {
            audioObject = GameObject.Find("Audio");
        }
        
        if (audioObject == null)
        {
            Debug.LogWarning("Audio object not found - cannot update lip sync reference");
            return;
        }
        
        // Get the uLipSync component on the Audio object
        uLipSync.uLipSync audioLipSync = audioObject.GetComponent<uLipSync.uLipSync>();
        if (audioLipSync == null)
        {
            Debug.LogWarning("uLipSync component not found on Audio object");
            return;
        }
        
        // Get the uLipSyncBlendShape component from the new avatar
        uLipSyncBlendShape avatarBlendShape = newAvatar.GetComponent<uLipSyncBlendShape>();
        if (avatarBlendShape == null)
        {
            Debug.LogWarning("uLipSyncBlendShape component not found on new avatar");
            return;
        }
        
        #if UNITY_EDITOR
        // Use SerializedObject to properly add a persistent listener that shows in the Inspector
        try
        {
            var serializedObject = new UnityEditor.SerializedObject(audioLipSync);
            var onLipSyncUpdateProperty = serializedObject.FindProperty("onLipSyncUpdate");
            var persistentCallsProperty = onLipSyncUpdateProperty.FindPropertyRelative("m_PersistentCalls");
            var callsArrayProperty = persistentCallsProperty.FindPropertyRelative("m_Calls");
            
            // Clear existing persistent calls
            callsArrayProperty.ClearArray();
            
            // Add a new persistent call
            callsArrayProperty.arraySize = 1;
            var call0 = callsArrayProperty.GetArrayElementAtIndex(0);
            
            // Set the target object (the avatar with uLipSyncBlendShape)
            var targetProperty = call0.FindPropertyRelative("m_Target");
            targetProperty.objectReferenceValue = avatarBlendShape;
            
            // Set the method name
            var methodNameProperty = call0.FindPropertyRelative("m_MethodName");
            methodNameProperty.stringValue = "OnLipSyncUpdate";
            
            // Set the call state (persistent, not runtime)
            var callStateProperty = call0.FindPropertyRelative("m_CallState");
            callStateProperty.enumValueIndex = 2; // UnityEventCallState.RuntimeOnly = 2
            
            // Set the mode (generic method call)
            var modeProperty = call0.FindPropertyRelative("m_Mode");
            modeProperty.enumValueIndex = 0; // PersistentListenerMode.EventDefined = 0
            
            // Apply the changes
            serializedObject.ApplyModifiedProperties();
            
            // Mark the audio object as dirty so Unity saves the changes
            UnityEditor.EditorUtility.SetDirty(audioObject);
            
            Debug.Log($"Successfully added persistent listener for {newAvatar.name} using SerializedObject");
            
            // Verify the connection
            int persistentCount = audioLipSync.onLipSyncUpdate.GetPersistentEventCount();
            Debug.Log($"Audio.onLipSyncUpdate now has {persistentCount} persistent listener(s)");
            
            if (persistentCount > 0)
            {
                var targetObj = audioLipSync.onLipSyncUpdate.GetPersistentTarget(0);
                var methodName = audioLipSync.onLipSyncUpdate.GetPersistentMethodName(0);
                Debug.Log($"Persistent listener 0: Target={targetObj?.name}, Method={methodName}");
            }
        }
        catch (System.Exception ex)
        {
            Debug.LogError($"Failed to set up persistent listener: {ex.Message}");
            
            // Fallback to runtime listener
            Debug.Log("Falling back to runtime listener...");
            audioLipSync.onLipSyncUpdate.RemoveAllListeners();
            audioLipSync.onLipSyncUpdate.AddListener(avatarBlendShape.OnLipSyncUpdate);
        }
        #else
        // In build, just use runtime listeners
        Debug.Log("In build mode - using runtime listener");
        audioLipSync.onLipSyncUpdate.RemoveAllListeners();
        audioLipSync.onLipSyncUpdate.AddListener(avatarBlendShape.OnLipSyncUpdate);
        #endif
        
        Debug.Log($"Successfully connected Audio lip sync to {newAvatar.name}");
    }
    
    // Helper method to ensure all children are active
    private void SetAllChildrenActive(GameObject parent, bool active)
    {
        foreach (Transform child in parent.transform)
        {
            child.gameObject.SetActive(active);
            SetAllChildrenActive(child.gameObject, active);
        }
    }
    
    // Helper method to calculate the bounds of the model
    private Bounds GetModelBounds(GameObject obj)
    {
        var renderers = obj.GetComponentsInChildren<Renderer>();
        if (renderers.Length == 0)
            return new Bounds(obj.transform.position, Vector3.zero);
            
        var bounds = renderers[0].bounds;
        foreach (var renderer in renderers)
        {
            bounds.Encapsulate(renderer.bounds);
        }
        return bounds;
    }
    
    // Debug method - call this to test if your current avatar is properly assigned
    [ContextMenu("Debug Current Avatar")]
    public void DebugCurrentAvatar()
    {
        if (currentAvatar == null)
        {
            Debug.Log("Current avatar is null!");
        }
        else
        {
            Debug.Log($"Current avatar: {currentAvatar.name}");
            Debug.Log($"Position: {currentAvatar.transform.position}");
            Debug.Log($"Scale: {currentAvatar.transform.localScale}");
            Debug.Log($"Active: {currentAvatar.activeInHierarchy}");
            Debug.Log($"Bounds: {GetModelBounds(currentAvatar).size}");
        }
    }
    
    // Emergency method to move avatar to camera view
    [ContextMenu("Move Avatar To Camera")]
    public void MoveAvatarToCamera()
    {
        if (currentAvatar == null)
        {
            Debug.LogError("No current avatar to move!");
            return;
        }
        
        var camera = Camera.main;
        if (camera == null)
        {
            Debug.LogError("No main camera found!");
            return;
        }
        
        // Position avatar 3 units in front of camera
        Vector3 newPosition = camera.transform.position + camera.transform.forward * 3f;
        currentAvatar.transform.position = newPosition;
        currentAvatar.transform.rotation = Quaternion.LookRotation(-camera.transform.forward);
        
        Debug.Log($"Moved avatar to position: {newPosition}");
    }
    
    // Method to reset avatar to origin
    [ContextMenu("Reset Avatar Position")]
    public void ResetAvatarPosition()
    {
        if (currentAvatar == null)
        {
            Debug.LogError("No current avatar to reset!");
            return;
        }
        
        currentAvatar.transform.position = Vector3.zero;
        currentAvatar.transform.rotation = Quaternion.identity;
        currentAvatar.transform.localScale = Vector3.one;
        
        Debug.Log("Reset avatar to origin");
    }
    
    // Helper method to automatically find and assign references
    [ContextMenu("Auto-Assign References")]
    public void AutoAssignReferences()
    {
        Debug.Log("Auto-assigning references...");
        
        // Try to find MITSUHA animator controller
        if (animatorController == null)
        {
            Debug.Log("Searching for MITSUHA animator controller...");
            
            // First try Resources folder
            animatorController = Resources.Load<RuntimeAnimatorController>("MITSUHA");
            
            // If not found, try to find it in all assets
            if (animatorController == null)
            {
                var controllers = Resources.FindObjectsOfTypeAll<RuntimeAnimatorController>();
                Debug.Log($"Found {controllers.Length} total animator controllers");
                
                foreach (var controller in controllers)
                {
                    Debug.Log($"Checking controller: {controller.name}");
                    if (controller.name == "MITSUHA" || controller.name.Contains("MITSUHA"))
                    {
                        animatorController = controller;
                        Debug.Log($"✓ Found and assigned animator controller: {controller.name}");
                        break;
                    }
                }
            }
            else
            {
                Debug.Log($"✓ Found MITSUHA controller in Resources: {animatorController.name}");
            }
            
            if (animatorController == null)
            {
                Debug.LogWarning("❌ MITSUHA animator controller not found. Please drag it manually from Assets to the Animator Controller field.");
            }
        }
        else
        {
            Debug.Log($"✓ Animator controller already assigned: {animatorController.name}");
        }
        
        // Try to find uLipSync profile
        if (lipSyncProfile == null)
        {
            Debug.Log("Searching for uLipSync profile...");
            var profiles = Resources.FindObjectsOfTypeAll<uLipSync.Profile>();
            Debug.Log($"Found {profiles.Length} uLipSync profiles");
            
            if (profiles.Length > 0)
            {
                lipSyncProfile = profiles[0];
                Debug.Log($"✓ Found uLipSync profile: {lipSyncProfile.name}");
            }
            else
            {
                Debug.LogWarning("❌ No uLipSync profile found");
            }
        }
        else
        {
            Debug.Log($"✓ uLipSync profile already assigned: {lipSyncProfile.name}");
        }
        
        // Try to find Audio object
        if (audioObject == null)
        {
            Debug.Log("Searching for Audio object...");
            audioObject = GameObject.Find("Audio");
            if (audioObject != null)
            {
                Debug.Log("✓ Found Audio object");
            }
            else
            {
                Debug.LogWarning("❌ Audio object not found");
            }
        }
        else
        {
            Debug.Log($"✓ Audio object already assigned: {audioObject.name}");
        }
        
        Debug.Log("Auto-assignment complete!");
    }
    
    // Manual method to fix Audio lip sync connection
    [ContextMenu("Fix Audio Lip Sync Connection")]
    public void FixAudioLipSyncConnection()
    {
        Debug.Log("Manually fixing Audio lip sync connection...");
        
        if (currentAvatar == null)
        {
            Debug.LogError("No current avatar found!");
            return;
        }
        
        UpdateAudioLipSyncReference(currentAvatar);
    }
    
    // Manual method to update Audio lip sync reference to current avatar
    [ContextMenu("Update Audio Lip Sync Reference")]
    public void UpdateAudioLipSyncReferenceManual()
    {
        if (currentAvatar == null)
        {
            Debug.LogError("No current avatar to connect to Audio lip sync");
            return;
        }
        
        UpdateAudioLipSyncReference(currentAvatar);
    }
    
    // Manual method to set up VRM blend shapes
    [ContextMenu("Setup VRM Blend Shapes")]
    public void SetupVRMBlendShapesManual()
    {
        if (currentAvatar == null)
        {
            Debug.LogError("No current avatar to set up blend shapes for");
            return;
        }
        
        var lipSyncBlendShape = currentAvatar.GetComponent<uLipSyncBlendShape>();
        if (lipSyncBlendShape == null)
        {
            Debug.LogError("No uLipSyncBlendShape component found on current avatar");
            return;
        }
        
        SetupVRMBlendShapeMapping(lipSyncBlendShape, currentAvatar);
    }
    
    // Debug method to list all blend shapes on current avatar
    [ContextMenu("List Avatar Blend Shapes")]
    public void ListAvatarBlendShapes()
    {
        if (currentAvatar == null)
        {
            Debug.LogError("No current avatar");
            return;
        }
        
        var skinnedMeshRenderers = currentAvatar.GetComponentsInChildren<SkinnedMeshRenderer>();
        Debug.Log($"Found {skinnedMeshRenderers.Length} SkinnedMeshRenderer(s) on {currentAvatar.name}:");
        
        foreach (var renderer in skinnedMeshRenderers)
        {
            if (renderer.sharedMesh != null)
            {
                Debug.Log($"\nMesh: {renderer.name} ({renderer.sharedMesh.blendShapeCount} blend shapes)");
                for (int i = 0; i < renderer.sharedMesh.blendShapeCount; i++)
                {
                    string blendShapeName = renderer.sharedMesh.GetBlendShapeName(i);
                    Debug.Log($"  [{i}] {blendShapeName}");
                }
            }
        }
    }
    
    // Manual method to setup VRM Look At components
    [ContextMenu("Setup VRM Look At")]
    public void SetupVRMLookAtManual()
    {
        if (currentAvatar == null)
        {
            Debug.LogError("No current avatar to setup VRM Look At for");
            return;
        }
        
        SetupVRMLookAt(currentAvatar);
    }
    
    // Debug method to list all transforms that contain "eye" in their name
    [ContextMenu("List Eye Transforms")]
    public void ListEyeTransforms()
    {
        if (currentAvatar == null)
        {
            Debug.LogError("No current avatar");
            return;
        }
        
        Transform[] allTransforms = currentAvatar.GetComponentsInChildren<Transform>();
        Debug.Log($"Searching for eye-related transforms in {currentAvatar.name}:");
        
        foreach (Transform t in allTransforms)
        {
            if (t.name.ToLower().Contains("eye"))
            {
                Debug.Log($"Found eye transform: {t.name} (full path: {GetTransformPath(t)})");
            }
        }
    }
    
    // Debug method to analyze VRMLookAtBoneApplyer component
    [ContextMenu("Debug VRMLookAtBoneApplyer")]
    public void DebugVRMLookAtBoneApplyer()
    {
        if (currentAvatar == null)
        {
            Debug.LogError("No current avatar");
            return;
        }
        
        var boneApplyerComponent = currentAvatar.GetComponent("VRMLookAtBoneApplyer");
        if (boneApplyerComponent == null)
        {
            Debug.LogError("VRMLookAtBoneApplyer component not found on current avatar");
            return;
        }
        
        var componentType = boneApplyerComponent.GetType();
        Debug.Log($"VRMLookAtBoneApplyer component found: {componentType.FullName}");
        
        Debug.Log("Available properties:");
        foreach (var prop in componentType.GetProperties())
        {
            Debug.Log($"  - {prop.Name} ({prop.PropertyType.Name}) - CanRead: {prop.CanRead}, CanWrite: {prop.CanWrite}");
        }
        
        Debug.Log("Available fields:");
        foreach (var field in componentType.GetFields())
        {
            Debug.Log($"  - {field.Name} ({field.FieldType.Name})");
        }
    }
    
    // Helper method to get full transform path
    private string GetTransformPath(Transform transform)
    {
        string path = transform.name;
        Transform parent = transform.parent;
        
        while (parent != null && parent != currentAvatar.transform)
        {
            path = parent.name + "/" + path;
            parent = parent.parent;
        }
        
        return path;
    }
}