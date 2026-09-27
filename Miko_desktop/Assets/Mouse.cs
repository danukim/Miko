using UnityEngine;

public class FollowMouse : MonoBehaviour
{
    [Header("Movement Settings")]
    public float smoothSpeed = 5f; // How fast to move to target position
    public bool followMouseDuringSpeech = true; // Toggle: follow mouse even during speech
    
    [Header("Default Position")]
    public Vector3 defaultPosition = new Vector3(0, 0, -10.8f);
    
    private bool isAudioPlaying;
    private Vector3 targetPosition;
    
    void Start()
    {
        // Initialize target position
        targetPosition = transform.position;
    }
    
    // Update is called once per frame
    void Update()
    {
        GameObject voiceGameObject = GameObject.Find("Audio");
        if (voiceGameObject != null)
        {
            Voice voiceComponent = voiceGameObject.GetComponent<Voice>();
            if (voiceComponent != null)
            {
                isAudioPlaying = voiceComponent.isAudioPlaying;
                
                // Determine target position based on audio state and settings
                if (!isAudioPlaying || followMouseDuringSpeech)
                {
                    // Follow mouse position
                    Vector3 mousePos = Input.mousePosition;
                    mousePos.z = 1.8f; // Set the distance from the camera
                    Vector3 worldPos = Camera.main.ScreenToWorldPoint(mousePos);
                    worldPos.z = -10.8f;
                    targetPosition = worldPos;
                }
                else
                {
                    // Move to default position during speech (only if followMouseDuringSpeech is false)
                    targetPosition = defaultPosition;
                }
                
                // Smoothly move to target position
                transform.position = Vector3.Lerp(transform.position, targetPosition, smoothSpeed * Time.deltaTime);
            }
        }
    }
}
