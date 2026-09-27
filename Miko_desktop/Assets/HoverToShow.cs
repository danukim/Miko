using System.Collections;
using UnityEngine;
using UnityEngine.EventSystems; // Required for hover and click events

public class AdvancedHoverButton : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler, IPointerClickHandler
{
    [Tooltip("How fast the button fades in and out.")]
    public float fadeDuration = 0.4f;

    [Tooltip("If true, the button starts visible. If false, it starts invisible and fades in on hover.")]
    public bool startVisible = false;

    [Tooltip("If true, clicking locks the button visible until clicked again.")]
    public bool enableClickLock = true;

    private CanvasGroup canvasGroup;
    private bool isLocked = false;
    private Coroutine currentFadeCoroutine;

    void Start()
    {
        // Get or add the CanvasGroup component
        canvasGroup = GetComponent<CanvasGroup>();
        if (canvasGroup == null)
        {
            canvasGroup = gameObject.AddComponent<CanvasGroup>();
        }

        // Set initial visibility based on setting
        if (startVisible)
        {
            canvasGroup.alpha = 1f;
            isLocked = true; // Start locked visible
        }
        else
        {
            canvasGroup.alpha = 0f;
        }
    }

    // Called when the mouse pointer enters the button's area
    public void OnPointerEnter(PointerEventData eventData)
    {
        // Always fade in on hover (regardless of lock state)
        StartFade(1f); // Target alpha is 1 (visible)
    }

    // Called when the mouse pointer exits the button's area
    public void OnPointerExit(PointerEventData eventData)
    {
        // Only fade out if the button is not locked
        if (!isLocked)
        {
            StartFade(0f); // Target alpha is 0 (invisible)
        }
    }

    // Called when the button is clicked
    public void OnPointerClick(PointerEventData eventData)
    {
        if (!enableClickLock)
            return;

        // Toggle the locked state
        isLocked = !isLocked;

        // If we just unlocked and mouse is not over, fade out
        // (otherwise keep visible)
    }

    // A helper method to start a new fade, stopping any previous one
    private void StartFade(float targetAlpha)
    {
        // Stop the currently running fade routine, if there is one
        if (currentFadeCoroutine != null)
        {
            StopCoroutine(currentFadeCoroutine);
        }
        // Start a new fade routine
        currentFadeCoroutine = StartCoroutine(FadeTo(targetAlpha));
    }

    // The coroutine that handles the actual fading animation
    private IEnumerator FadeTo(float targetAlpha)
    {
        float elapsedTime = 0f;
        float startAlpha = canvasGroup.alpha;

        while (elapsedTime < fadeDuration)
        {
            // Calculate the new alpha value
            float newAlpha = Mathf.Lerp(startAlpha, targetAlpha, elapsedTime / fadeDuration);
            canvasGroup.alpha = newAlpha;

            // Wait for the next frame
            elapsedTime += Time.deltaTime;
            yield return null;
        }

        // Ensure the final alpha is set correctly
        canvasGroup.alpha = targetAlpha;
    }

    // Public method to lock visibility (can be called by other scripts)
    public void SetLocked(bool locked)
    {
        isLocked = locked;
        if (locked)
        {
            StartFade(1f);
        }
    }
}
