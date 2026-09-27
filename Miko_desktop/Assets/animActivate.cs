using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class animActivate : MonoBehaviour
{
    // Start is called before the first frame update
    private Animator animator;
    string speech;
    bool isAudioPlaying;
    
    // Idle variation system
    [Header("Idle Variation Settings")]
    [Tooltip("List of idle variation trigger names in the Animator")]
    // Removed "Idle" because it is the default state and not a variation trigger
    public string[] idleVariations = {"Idle Look Left And Right", "Idle Stretch", "Idle Cute Arm Up", "Idle Look At Hands", "Idle Look At Feet", "Idle Waiting"}; 
    [Tooltip("Minimum time before transitioning to an idle variation")]
    public float minIdleTime = 10f; // Reduced for testing
    [Tooltip("Maximum time before transitioning to an idle variation")]
    public float maxIdleTime = 20f; // Reduced for testing
    [Tooltip("Duration of idle variation before returning to base idle")]
    public float idleVariationDuration = 3f;
    
    private bool isPlayingIdleVariation = false;
    private bool isPlayingActionAnimation = false;
    
    void Start()
    {
        animator = GetComponent<Animator>();
        StartCoroutine(UpdateCoroutine());
        StartCoroutine(IdleVariationCoroutine());
    }
    
    IEnumerator IdleVariationCoroutine()
    {
        while (true)
        {
            // Wait for random time between min and max idle time
            float waitTime = Random.Range(minIdleTime, maxIdleTime);
            // Debug.Log($"[animActivate] Waiting {waitTime} seconds for next variation...");
            yield return new WaitForSeconds(waitTime);
            
            // Only play idle variation if not playing an action animation
            if (!isPlayingActionAnimation && idleVariations.Length > 0)
            {
                isPlayingIdleVariation = true;
                
                // Select a random idle variation
                int randomIndex = Random.Range(0, (idleVariations.Length));
                string selectedVariation = idleVariations[randomIndex];
                
                Debug.Log($"[animActivate] Attempting to trigger variation: '{selectedVariation}'");
                
                // Trigger the idle variation
                animator.SetBool(selectedVariation, true);
                
                // Wait for the variation to play
                yield return new WaitForSeconds(idleVariationDuration);
                
                // Return to base idle
                Debug.Log($"[animActivate] Ending variation: '{selectedVariation}'");
                animator.SetBool(selectedVariation, false);
                
                isPlayingIdleVariation = false;
            }
            else
            {
                 Debug.Log($"[animActivate] Skipped variation. Playing Action? {isPlayingActionAnimation}. Variations count: {idleVariations.Length}");
            }
        }
    }

    IEnumerator UpdateCoroutine()
    {
        while (true)
        {
            GameObject voiceGameObject = GameObject.Find("Audio");

            if (voiceGameObject != null)
            {
                Voice voiceComponent = voiceGameObject.GetComponent<Voice>();

                if (voiceComponent != null)
                {
                    string speech = voiceComponent.speech;
                    bool isAudioPlaying = voiceComponent.isAudioPlaying;
                    // Debug.Log(speech);
                    if (speech == "wave.wav" || speech == "Wave.wav")
                    {
                        // Debug.Log(speech);
                        isPlayingActionAnimation = true;
                        animator.SetBool("Wave", true);
                        yield return new WaitForSeconds(2); // Add your delay here
                        animator.SetBool("Wave", false);
                        voiceComponent.speech = ""; // Clear the speech trigger
                        isPlayingActionAnimation = false;
                    }
                    else if (speech == "clap.wav" || speech == "Clap.wav")
                    {
                        // Debug.Log(speech);
                        isPlayingActionAnimation = true;
                        animator.SetBool("Clap", true);
                        yield return new WaitForSeconds(2); // Add your delay here
                        animator.SetBool("Clap", false);
                        voiceComponent.speech = ""; // Clear the speech trigger
                        isPlayingActionAnimation = false;
                    }
                    else if (speech == "nodding.wav" || speech == "Nodding.wav")
                    {
                        // Debug.Log(speech);
                        isPlayingActionAnimation = true;
                        animator.SetBool("Nodding", true);
                        yield return new WaitForSeconds(2); // Add your delay here
                        animator.SetBool("Nodding", false);
                        voiceComponent.speech = ""; // Clear the speech trigger
                        isPlayingActionAnimation = false;
                    }
                    else if (speech == "shaking head.wav" || speech == "Shaking head.wav")
                    {
                        // Debug.Log(speech);
                        isPlayingActionAnimation = true;
                        animator.SetBool("Shaking head", true);
                        yield return new WaitForSeconds(2); // Add your delay here
                        animator.SetBool("Shaking head", false);
                        voiceComponent.speech = ""; // Clear the speech trigger
                        isPlayingActionAnimation = false;
                    }
                    else if (speech == "thumbs-up.wav" || speech == "Thumbs-up.wav")
                    {
                        // Debug.Log(speech);
                        isPlayingActionAnimation = true;
                        animator.SetBool("Thumbs-up", true);
                        yield return new WaitForSeconds(2); // Add your delay here
                        animator.SetBool("Thumbs-up", false);
                        voiceComponent.speech = ""; // Clear the speech trigger
                        isPlayingActionAnimation = false;
                    }
                    else
                    {
                        animator.SetBool("Wave", false);
                        animator.SetBool("Clap", false);
                        animator.SetBool("Nodding", false);
                        animator.SetBool("Shaking head", false);
                        //animator.SetBool("Thumbs-up", false);
                    }
                }
                else
                {
                    // Debug.LogError("Voice GameObject not found.");
                }
                yield return null; // This is needed to avoid freezing the game
            }
        }
    }
}