using UnityEngine;

[System.Serializable]
public class VisemeBlendShape
{
    public string name;
    public int blendShapeIndex;
    [Range(0f, 1f)]
    public float intensity = 1f;
}

public class LipSyncController : MonoBehaviour
{
    [Header("Audio Source")]
    public Voice voiceScript;
    
    [Header("Blend Shapes")]
    public SkinnedMeshRenderer faceMeshRenderer;
    public VisemeBlendShape[] visemes;
    
    [Header("Settings")]
    [Range(0f, 1f)]
    public float sensitivity = 1f;
    [Range(0f, 1f)]
    public float smoothing = 0.8f;
    public float volumeThreshold = 0.01f;
    
    [Header("Frequency Ranges for Visemes")]
    public float lowFreqMax = 500f;      // A, O sounds
    public float midFreqMax = 2000f;     // E, I sounds  
    public float highFreqMax = 4000f;    // consonants, S, T sounds
    
    private float[] currentBlendValues;
    private float[] targetBlendValues;
    
    void Start()
    {
        if (voiceScript == null)
            voiceScript = FindObjectOfType<Voice>();
            
        if (faceMeshRenderer == null)
            faceMeshRenderer = GetComponentInChildren<SkinnedMeshRenderer>();
            
        currentBlendValues = new float[visemes.Length];
        targetBlendValues = new float[visemes.Length];
    }
    
    void Update()
    {
        if (voiceScript == null || !voiceScript.IsStreamingAudio())
        {
            // Gradually close mouth when not speaking
            for (int i = 0; i < targetBlendValues.Length; i++)
            {
                targetBlendValues[i] = 0f;
            }
        }
        else
        {
            AnalyzeAudioForLipSync();
        }
        
        // Smooth blend shape transitions
        for (int i = 0; i < currentBlendValues.Length; i++)
        {
            currentBlendValues[i] = Mathf.Lerp(currentBlendValues[i], targetBlendValues[i], (1f - smoothing) * Time.deltaTime * 10f);
            
            if (i < visemes.Length && faceMeshRenderer != null)
            {
                int blendIndex = visemes[i].blendShapeIndex;
                if (blendIndex >= 0 && blendIndex < faceMeshRenderer.sharedMesh.blendShapeCount)
                {
                    faceMeshRenderer.SetBlendShapeWeight(blendIndex, currentBlendValues[i] * visemes[i].intensity * 100f);
                }
            }
        }
    }
    
    void AnalyzeAudioForLipSync()
    {
        float volume = voiceScript.GetVolume();
        float[] spectrum = voiceScript.GetSpectrum();
        
        if (volume < volumeThreshold)
        {
            // Not speaking, close mouth
            for (int i = 0; i < targetBlendValues.Length; i++)
            {
                targetBlendValues[i] = 0f;
            }
            return;
        }
        
        // Analyze frequency content to determine viseme
        float lowFreqEnergy = 0f;
        float midFreqEnergy = 0f;
        float highFreqEnergy = 0f;
        
        int sampleRate = 22050; // From your streaming setup
        float binWidth = sampleRate / 2f / spectrum.Length;
        
        for (int i = 0; i < spectrum.Length; i++)
        {
            float frequency = i * binWidth;
            float energy = spectrum[i];
            
            if (frequency <= lowFreqMax)
                lowFreqEnergy += energy;
            else if (frequency <= midFreqMax)
                midFreqEnergy += energy;
            else if (frequency <= highFreqMax)
                highFreqEnergy += energy;
        }
        
        // Normalize energies
        float totalEnergy = lowFreqEnergy + midFreqEnergy + highFreqEnergy;
        if (totalEnergy > 0f)
        {
            lowFreqEnergy /= totalEnergy;
            midFreqEnergy /= totalEnergy;
            highFreqEnergy /= totalEnergy;
        }
        
        // Map to visemes (adjust these mappings based on your blend shapes)
        if (visemes.Length >= 5)
        {
            // Example mapping - adjust based on your VRM's blend shapes
            targetBlendValues[0] = lowFreqEnergy * volume * sensitivity;    // A/O mouth shape
            targetBlendValues[1] = midFreqEnergy * volume * sensitivity;    // E/I mouth shape
            targetBlendValues[2] = highFreqEnergy * volume * sensitivity;   // consonant mouth shape
            targetBlendValues[3] = volume * 0.5f * sensitivity;            // general mouth opening
            targetBlendValues[4] = (lowFreqEnergy + midFreqEnergy) * volume * sensitivity * 0.3f; // smile/expression
        }
        else
        {
            // Simple volume-based mouth opening
            for (int i = 0; i < targetBlendValues.Length; i++)
            {
                targetBlendValues[i] = volume * sensitivity;
            }
        }
    }
    
    // Debug visualization
    void OnGUI()
    {
        if (voiceScript == null || !Application.isPlaying)
            return;
            
        GUILayout.BeginArea(new Rect(10, 10, 300, 200));
        GUILayout.Label("Lip Sync Debug");
        GUILayout.Label($"Volume: {voiceScript.GetVolume():F3}");
        GUILayout.Label($"Pitch: {voiceScript.GetPitch():F1} Hz");
        GUILayout.Label($"Streaming: {voiceScript.IsStreamingAudio()}");
        
        for (int i = 0; i < currentBlendValues.Length && i < visemes.Length; i++)
        {
            GUILayout.Label($"{visemes[i].name}: {currentBlendValues[i]:F3}");
        }
        GUILayout.EndArea();
    }
}
