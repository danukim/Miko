using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;
using System.Text;
using System.IO;

[System.Serializable]
public class AudioMessage
{
    public string type;
    public string audio_data;
    public int sample_rate;
    public float timestamp;
}

public class MikoAudioReceiver : MonoBehaviour
{
    [Header("Server Configuration")]
    public string serverUrl = "http://localhost:8000";
    
    [Header("Audio Configuration")]
    public AudioSource audioSource;
    public int bufferSizeSeconds = 5;
    
    [Header("Lip Sync")]
    public AudioLipSync lipSyncComponent; // Your existing lip sync component
    
    private bool isConnected = false;
    private Queue<float[]> audioChunks = new Queue<float[]>();
    private List<float> audioBuffer = new List<float>();
    private int currentSampleRate = 22050;
    private bool isPlaying = false;
    
    // For real-time audio streaming
    private AudioClip streamingClip;
    private int audioPosition = 0;
    private const int STREAMING_BUFFER_SIZE = 44100 * 2; // 2 seconds buffer
    
    void Start()
    {
        if (audioSource == null)
        {
            audioSource = GetComponent<AudioSource>();
            if (audioSource == null)
            {
                audioSource = gameObject.AddComponent<AudioSource>();
            }
        }
        
        // Create streaming audio clip
        streamingClip = AudioClip.Create("StreamingAudio", STREAMING_BUFFER_SIZE, 1, currentSampleRate, true, OnAudioRead);
        audioSource.clip = streamingClip;
        audioSource.loop = true;
        audioSource.Play();
        
        // Start connection to server
        StartCoroutine(ConnectToAudioStream());
    }
    
    void OnAudioRead(float[] data)
    {
        // This is called by Unity's audio system to fill the audio buffer
        lock (audioBuffer)
        {
            for (int i = 0; i < data.Length; i++)
            {
                if (audioBuffer.Count > 0)
                {
                    data[i] = audioBuffer[0];
                    audioBuffer.RemoveAt(0);
                }
                else
                {
                    data[i] = 0f; // Silence if no data available
                }
            }
        }
    }
    
    IEnumerator ConnectToAudioStream()
    {
        string streamUrl = serverUrl + "/audio_stream";
        
        using (UnityWebRequest request = UnityWebRequest.Get(streamUrl))
        {
            request.downloadHandler = new AudioStreamDownloadHandler(this);
            
            Debug.Log($"🎵 Connecting to audio stream: {streamUrl}");
            
            var operation = request.SendWebRequest();
            
            while (!operation.isDone)
            {
                yield return null;
            }
            
            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError($"❌ Failed to connect to audio stream: {request.error}");
                // Retry connection after 5 seconds
                yield return new WaitForSeconds(5f);
                StartCoroutine(ConnectToAudioStream());
            }
        }
    }
    
    public void OnAudioMessageReceived(string jsonMessage)
    {
        try
        {
            AudioMessage message = JsonUtility.FromJson<AudioMessage>(jsonMessage);
            
            switch (message.type)
            {
                case "audio_start":
                    OnAudioStreamStart(message.sample_rate);
                    break;
                    
                case "audio_chunk":
                    OnAudioChunkReceived(message.audio_data, message.sample_rate);
                    break;
                    
                case "audio_end":
                    OnAudioStreamEnd();
                    break;
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"❌ Error parsing audio message: {e.Message}");
        }
    }
    
    void OnAudioStreamStart(int sampleRate)
    {
        Debug.Log($"✨ Audio stream started (Sample rate: {sampleRate}Hz)");
        
        currentSampleRate = sampleRate;
        isPlaying = true;
        
        // Clear existing audio buffer
        lock (audioBuffer)
        {
            audioBuffer.Clear();
        }
        
        // Trigger lip sync start if available
        if (lipSyncComponent != null)
        {
            lipSyncComponent.OnSpeechStart();
        }
    }
    
    void OnAudioChunkReceived(string audioDataBase64, int sampleRate)
    {
        try
        {
            // Decode base64 audio data
            byte[] audioBytes = Convert.FromBase64String(audioDataBase64);
            
            // Convert bytes to float array
            float[] audioFloats = new float[audioBytes.Length / 4]; // 4 bytes per float
            Buffer.BlockCopy(audioBytes, 0, audioFloats, 0, audioBytes.Length);
            
            // Add to audio buffer for playback
            lock (audioBuffer)
            {
                audioBuffer.AddRange(audioFloats);
                
                // Limit buffer size to prevent memory issues
                int maxBufferSize = currentSampleRate * bufferSizeSeconds;
                while (audioBuffer.Count > maxBufferSize)
                {
                    audioBuffer.RemoveAt(0);
                }
            }
            
            // Update lip sync if available
            if (lipSyncComponent != null && audioFloats.Length > 0)
            {
                float volume = CalculateVolume(audioFloats);
                lipSyncComponent.OnAudioData(audioFloats, volume);
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"❌ Error processing audio chunk: {e.Message}");
        }
    }
    
    void OnAudioStreamEnd()
    {
        Debug.Log("✨ Audio stream ended");
        
        isPlaying = false;
        
        // Trigger lip sync end if available
        if (lipSyncComponent != null)
        {
            lipSyncComponent.OnSpeechEnd();
        }
    }
    
    float CalculateVolume(float[] audioData)
    {
        float sum = 0f;
        for (int i = 0; i < audioData.Length; i++)
        {
            sum += Mathf.Abs(audioData[i]);
        }
        return sum / audioData.Length;
    }
    
    void OnDestroy()
    {
        if (streamingClip != null)
        {
            DestroyImmediate(streamingClip);
        }
    }
}

// Custom download handler for streaming audio data
public class AudioStreamDownloadHandler : DownloadHandlerScript
{
    private MikoAudioReceiver audioReceiver;
    private StringBuilder messageBuffer = new StringBuilder();
    
    public AudioStreamDownloadHandler(MikoAudioReceiver receiver) : base()
    {
        audioReceiver = receiver;
    }
    
    protected override bool ReceiveData(byte[] data, int dataLength)
    {
        try
        {
            string receivedText = Encoding.UTF8.GetString(data, 0, dataLength);
            messageBuffer.Append(receivedText);
            
            // Process complete messages (separated by newlines)
            string bufferContent = messageBuffer.ToString();
            string[] messages = bufferContent.Split('\n');
            
            // Process all complete messages except the last one
            for (int i = 0; i < messages.Length - 1; i++)
            {
                string message = messages[i].Trim();
                if (!string.IsNullOrEmpty(message) && message != "heartbeat")
                {
                    audioReceiver.OnAudioMessageReceived(message);
                }
            }
            
            // Keep the last (potentially incomplete) message in buffer
            messageBuffer.Clear();
            if (messages.Length > 0)
            {
                messageBuffer.Append(messages[messages.Length - 1]);
            }
            
            return true;
        }
        catch (Exception e)
        {
            Debug.LogError($"❌ Error receiving audio stream data: {e.Message}");
            return false;
        }
    }
}

// Example lip sync interface - adapt this to your existing lip sync system
public abstract class AudioLipSync : MonoBehaviour
{
    public abstract void OnSpeechStart();
    public abstract void OnSpeechEnd();
    public abstract void OnAudioData(float[] audioData, float volume);
}

// Example implementation of lip sync
public class SimpleLipSync : AudioLipSync
{
    [Header("Lip Sync Configuration")]
    public SkinnedMeshRenderer mouthRenderer;
    public int mouthOpenBlendShapeIndex = 0;
    public float volumeMultiplier = 10f;
    public float smoothing = 5f;
    
    private float currentMouthOpen = 0f;
    private float targetMouthOpen = 0f;
    
    public override void OnSpeechStart()
    {
        Debug.Log("🎤 Speech started - lip sync activated");
    }
    
    public override void OnSpeechEnd()
    {
        Debug.Log("🎤 Speech ended - lip sync deactivated");
        targetMouthOpen = 0f;
    }
    
    public override void OnAudioData(float[] audioData, float volume)
    {
        // Map volume to mouth opening
        targetMouthOpen = Mathf.Clamp01(volume * volumeMultiplier);
    }
    
    void Update()
    {
        if (mouthRenderer != null)
        {
            // Smooth interpolation to target mouth opening
            currentMouthOpen = Mathf.Lerp(currentMouthOpen, targetMouthOpen, smoothing * Time.deltaTime);
            
            // Apply to blend shape
            mouthRenderer.SetBlendShapeWeight(mouthOpenBlendShapeIndex, currentMouthOpen * 100f);
        }
    }
}
