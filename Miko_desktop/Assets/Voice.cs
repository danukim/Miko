using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;
using System;
using System.Text;

[System.Serializable]
public class AudioStreamMessage
{
    public string type;
    public string audio_data;
    public int sample_rate;
    public float timestamp;
}

public class Voice : MonoBehaviour
{
    string serverURL;
    public string speech;
    public bool isAudioPlaying = false;
    private const string ServerUrlKey = "ServerURL";
    
    // Streaming audio variables
    private AudioSource audioSource;
    private Queue<float[]> audioChunkQueue = new Queue<float[]>();
    private bool isStreaming = false;
    private bool stopHasBeenInvoked = false;
    private bool shouldStopAudio = false;
    private int streamSampleRate = 22050;
    private AudioClip streamingClip;
    private const int clipLengthSeconds = 5;

    // Buffer for leftover audio data to ensure smooth playback
    private float[] leftoverChunk = null;
    private int leftoverChunkIndex = 0;
    
    // Grace period for audio ending - prevent premature cutoff
    private int silenceFrameCount = 0;
    private const int maxSilenceFrames = 7; // Reduced from 10 to 3 frames to minimize trailing noise
    private bool streamEndReceived = false; // Track when audio_end message is received
    
    // Audio analysis for lip sync
    private float[] spectrum = new float[256];
    private float volume = 0f;
    private float pitch = 0f;

    void Start()
    {
        audioSource = GetComponent<AudioSource>();
        if (audioSource == null)
        {
            audioSource = gameObject.AddComponent<AudioSource>();
        }
        
        // Set default serverURL to localhost:8000, but allow user override from PlayerPrefs
        serverURL = PlayerPrefs.GetString(ServerUrlKey, "http://localhost:8000");
        if (!string.IsNullOrEmpty(serverURL))
        {
            StartCoroutine(ConnectToAudioStream());
        }
    }

    void Update()
    {
        if (isStreaming && audioSource.isPlaying)
        {
            AnalyzeAudio();
        }

        // Handle audio stopping on main thread to avoid callback timing issues
        if (shouldStopAudio)
        {
            shouldStopAudio = false;
            StopAudio();
        }
    }

    public void ReadStringInput(string i)
    {
        serverURL = i;
        PlayerPrefs.SetString(ServerUrlKey, serverURL);
        PlayerPrefs.Save();
        // Debug.Log(serverURL);
        
        if (!string.IsNullOrEmpty(serverURL))
        {
            StopAllCoroutines();
            StartCoroutine(ConnectToAudioStream());
        }
    }

    IEnumerator ConnectToAudioStream()
    {
        string streamURL = serverURL + "/audio_stream";
        // Debug.Log("🎵 Connecting to audio stream: " + streamURL);
        
        while (true)
        {
            // Debug.Log("🎵 Starting new streaming connection...");
            
            using (UnityWebRequest streamRequest = UnityWebRequest.Get(streamURL))
            {
                streamRequest.downloadHandler = new StreamingDownloadHandler();
                streamRequest.SetRequestHeader("Connection", "keep-alive");
                streamRequest.timeout = 0;
                
                var operation = streamRequest.SendWebRequest();
                
                while (!operation.isDone)
                {
                    byte[] newData = (streamRequest.downloadHandler as StreamingDownloadHandler).GetReceivedData();
                    if (newData != null && newData.Length > 0)
                    {
                        ProcessIncomingStreamData(newData);
                        (streamRequest.downloadHandler as StreamingDownloadHandler).ClearBuffer();
                    }
                    yield return new WaitForSeconds(0.01f);
                }
                
                if (streamRequest.result != UnityWebRequest.Result.Success)
                {
                    // Debug.LogError("🎵 Stream connection failed: " + streamRequest.error);
                    yield return new WaitForSeconds(2f);
                }
            }
        }
    }
    
    private string messageBuffer = "";
    
    private void ProcessIncomingStreamData(byte[] data)
    {
        messageBuffer += System.Text.Encoding.UTF8.GetString(data);
        
        while (messageBuffer.Contains("\n"))
        {
            int newlineIndex = messageBuffer.IndexOf("\n");
            string completeLine = messageBuffer.Substring(0, newlineIndex);
            messageBuffer = messageBuffer.Substring(newlineIndex + 1);
            
            if (!string.IsNullOrEmpty(completeLine.Trim()) && completeLine.Trim() != "heartbeat")
            {
                try
                {
                    AudioStreamMessage message = JsonUtility.FromJson<AudioStreamMessage>(completeLine);
                    ProcessAudioMessage(message);
                }
                catch (System.Exception e)
                {
                    // Debug.LogError("🎵 JSON parse error: " + e.Message + " for line: " + completeLine);
                }
            }
        }
    }
    
    private void ProcessAudioMessage(AudioStreamMessage message)
    {
        switch (message.type)
        {
            case "audio_start":
                StartAudioStream(message.sample_rate);
                break;
                
            case "audio_chunk":
                if (!string.IsNullOrEmpty(message.audio_data))
                {
                    ProcessAudioChunk(message.audio_data);
                }
                break;
                
            case "audio_end":
                EndAudioStream();
                break;
                
            case "animation_command":
                ProcessAnimationCommand(message);
                break;
        }
    }
    
    private void ProcessAnimationCommand(AudioStreamMessage message)
    {
        string animationName = message.audio_data; // Using audio_data field for animation name
        // Debug.Log($"🎭 Received animation command: {animationName}");
        
        // Set the speech property to trigger the animation in animActivate.cs
        if (!string.IsNullOrEmpty(animationName))
        {
            speech = animationName + ".wav"; // Add .wav extension to match animActivate expectations
            // Debug.Log($"🎭 Set speech to: {speech}");
        }
    }
    
    // MODIFIED METHOD
    private void StartAudioStream(int sampleRate)
    {
        // Debug.Log("Starting audio stream with sample rate: " + sampleRate);

        stopHasBeenInvoked = false;
        shouldStopAudio = false;
        silenceFrameCount = 0; // Reset silence counter
        streamEndReceived = false; // Reset stream end flag
        
        streamSampleRate = sampleRate;
        isStreaming = true;

        // Clear any old data
        lock(audioChunkQueue)
        {
            audioChunkQueue.Clear();
        }
        leftoverChunk = null;
        leftoverChunkIndex = 0;
        
        // Create a streaming audio clip that uses OnAudioRead as a callback
        streamingClip = AudioClip.Create("StreamingAudio", streamSampleRate * clipLengthSeconds, 1, streamSampleRate, true, OnAudioRead);
        
        audioSource.clip = streamingClip;
        audioSource.loop = true; // Loop to continuously ask for new data
        audioSource.Play();
        
        isAudioPlaying = true;
    }
    
    private void ProcessAudioChunk(string base64AudioData)
    {
        try
        {
            byte[] audioBytes = Convert.FromBase64String(base64AudioData);
            float[] audioFloats = ConvertBytesToFloats(audioBytes);
            
            lock (audioChunkQueue)
            {
                audioChunkQueue.Enqueue(audioFloats);
            }
        }
        catch (Exception e)
        {
            // Debug.LogError("Failed to process audio chunk: " + e.Message);
        }
    }
    
    private float[] ConvertBytesToFloats(byte[] audioBytes)
    {
        // Revert to this safer, more explicit conversion method.
        int floatCount = audioBytes.Length / 4;
        float[] floats = new float[floatCount];
        
        for (int i = 0; i < floatCount; i++)
        {
            floats[i] = BitConverter.ToSingle(audioBytes, i * 4);
        }
        
        return floats;
    }
    
    // MODIFIED METHOD
    private void EndAudioStream()
    {
        // Debug.Log("Ending audio stream");
        streamEndReceived = true; // Mark that we received the end signal
        isStreaming = false; // This will signal OnAudioRead to stop queuing data
    }
    
    // DELETED the ProcessAudioQueue() coroutine entirely.

    // REPLACED OnAudioRead with this improved version
    void OnAudioRead(float[] data)
    {
        // If we've already determined the stream should stop, fill with silence and don't process more data
        if (stopHasBeenInvoked)
        {
            for (int i = 0; i < data.Length; i++)
            {
                data[i] = 0f;
            }
            return;
        }

        int dataIndex = 0;

        // First, use any leftover data from the previous read cycle.
        if (leftoverChunk != null)
        {
            int amountToCopy = Mathf.Min(data.Length, leftoverChunk.Length - leftoverChunkIndex);
            Array.Copy(leftoverChunk, leftoverChunkIndex, data, 0, amountToCopy);
            dataIndex += amountToCopy;
            leftoverChunkIndex += amountToCopy;

            if (leftoverChunkIndex >= leftoverChunk.Length)
            {
                leftoverChunk = null; // We've used up the leftover chunk.
                leftoverChunkIndex = 0;
            }
        }

        // Now, fill the rest of the buffer with new chunks from the queue.
        while (dataIndex < data.Length)
        {
            float[] newChunk = null;
            lock (audioChunkQueue)
            {
                if (audioChunkQueue.Count > 0)
                {
                    newChunk = audioChunkQueue.Dequeue();
                }
            }

            if (newChunk == null)
            {
                // No more chunks are available.
                break; 
            }

            // Copy data from the new chunk into the buffer.
            int amountToCopy = Mathf.Min(data.Length - dataIndex, newChunk.Length);
            Array.Copy(newChunk, 0, data, dataIndex, amountToCopy);
            dataIndex += amountToCopy;

            // If we didn't use the whole chunk, save the remainder for the next cycle.
            if (amountToCopy < newChunk.Length)
            {
                leftoverChunk = newChunk;
                leftoverChunkIndex = amountToCopy;
                break; // Buffer is full for this cycle.
            }
        }
        
        // If the buffer isn't full yet (e.g., end of stream), fill the rest with silence.
        bool hadSilence = false;
        while (dataIndex < data.Length)
        {
            data[dataIndex] = 0f;
            dataIndex++;
            hadSilence = true;
        }

        // Improved stopping logic with shorter grace period and cleaner ending
        if (!isStreaming && audioChunkQueue.Count == 0 && leftoverChunk == null && !stopHasBeenInvoked)
        {
            if (streamEndReceived && hadSilence)
            {
                silenceFrameCount++;
                // Much shorter grace period when we know the stream has officially ended
                if (silenceFrameCount >= maxSilenceFrames)
                {
                    stopHasBeenInvoked = true;
                    shouldStopAudio = true;
                }
            }
            else if (!streamEndReceived && hadSilence)
            {
                // If no end signal received yet, allow a bit more time for late chunks
                silenceFrameCount++;
                if (silenceFrameCount >= maxSilenceFrames * 2) // 6 frames max without end signal
                {
                    stopHasBeenInvoked = true;
                    shouldStopAudio = true;
                }
            }
            else
            {
                silenceFrameCount = 0; // Reset if we had actual audio data
            }
        }
        else
        {
            silenceFrameCount = 0; // Reset silence counter if still streaming or have data
        }
    }

    private void StopAudio()
    {
        // Use a flag to prevent multiple calls
        if (!isAudioPlaying) return;
        
        isAudioPlaying = false;
        isStreaming = false;
        silenceFrameCount = 0; // Reset silence counter
        streamEndReceived = false; // Reset stream end flag

        if (audioSource != null && audioSource.isPlaying)
        {
            audioSource.Stop();
            // Debug.Log("AudioSource stopped.");
        }

        // THE FIX: Aggressively clear the clip from the audio source.
        // This ensures there is no data left to be looped.
        if (audioSource != null)
        {
            audioSource.clip = null;
        }
        
        // Clear any remaining data
        lock(audioChunkQueue)
        {
            audioChunkQueue.Clear();
        }
        leftoverChunk = null;
        leftoverChunkIndex = 0;
    }
    
    private void AnalyzeAudio()
    {
        audioSource.GetSpectrumData(spectrum, 0, FFTWindow.BlackmanHarris);
        
        volume = 0f;
        foreach (float sample in spectrum)
        {
            volume += sample * sample;
        }
        volume = Mathf.Sqrt(volume / spectrum.Length);
        
        // Calculate dominant frequency for pitch estimation
        float maxValue = 0f;
        int maxIndex = 0;
        for (int i = 0; i < spectrum.Length; i++)
        {
            if (spectrum[i] > maxValue)
            {
                maxValue = spectrum[i];
                maxIndex = i;
            }
        }
        
        // Convert index to frequency
        pitch = maxIndex * audioSource.clip.frequency / 2 / spectrum.Length;
    }
    
    // Public methods for accessing lip sync data
    public float GetVolume()
    {
        return volume;
    }
    
    public float GetPitch()
    {
        return pitch;
    }
    
    public float[] GetSpectrum()
    {
        return spectrum;
    }
    
    public bool IsStreamingAudio()
    {
        return isStreaming && audioSource.isPlaying;
    }

    IEnumerator CheckForWavFiles()
    {
        // WAV file checking disabled - using audio streaming instead
        // Debug.Log("🎵 WAV file checking disabled. Using audio streaming only.");
        yield break;
    }

    IEnumerator DeleteFileOnServer(string wavURL)
    {
        while (isAudioPlaying)
        {
            yield return null; // Wait until the audio finishes playing
        }

        UnityWebRequest deleteRequest = UnityWebRequest.Delete(wavURL);
        yield return deleteRequest.SendWebRequest();

        if (deleteRequest.result == UnityWebRequest.Result.Success)
        {
            // Debug.Log("File deleted on server.");
            isAudioPlaying = false;
        }
        else
        {
            // Debug.LogError("Failed to delete file on server. Error: " + deleteRequest.error);
        }
    }

    static string DeleteAfterAndIncluding(string input, string searchString)
    {
        int index = input.IndexOf(searchString);
        if (index != -1)
        {
            return input.Substring(0, index);
        }
        else
        {
            return input;
        }
    }

    static string DeleteBeforeAndIncluding(string input, string searchString)
    {
        int index = input.IndexOf(searchString);
        if (index != -1)
        {
            return input.Substring(index + searchString.Length);
        }
        else
        {
            return input;
        }
    }
}

// Make sure your StreamingDownloadHandler is outside the Voice class if it isn't already.
public class StreamingDownloadHandler : DownloadHandlerScript
{
    private List<byte> receivedData = new List<byte>();
    
    protected override bool ReceiveData(byte[] data, int dataLength)
    {
        if (data == null || dataLength == 0)
            return false;
            
        receivedData.AddRange(new ArraySegment<byte>(data, 0, dataLength));
        return true;
    }
    
    public byte[] GetReceivedData()
    {
        if (receivedData.Count == 0)
            return null;
            
        byte[] result = receivedData.ToArray();
        return result;
    }
    
    public void ClearBuffer()
    {
        receivedData.Clear();
    }
}