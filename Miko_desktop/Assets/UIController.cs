using UnityEngine;
using UnityEngine.UI; // Required for UI components like Button
using TMPro; // Required for TextMeshPro components

public class UIController : MonoBehaviour
{
    [Header("UI Elements")]
    public Button primaryButton; // The button that is always visible
    public Button IPButton; // The input field to show/hide
    public Button changeAvatarButton; // The other button to show/hide

    void Start()
    {
        // --- Initial Setup ---
        // Hide the input field and secondary button when the scene starts.
        IPButton.gameObject.SetActive(false);
        changeAvatarButton.gameObject.SetActive(false);

        // --- Add a Listener ---
        // Tell the primary button to call our 'ToggleVisibility' function when clicked.
        primaryButton.onClick.AddListener(ToggleVisibility);
    }

    // This function will be called when the primaryButton is clicked.
    public void ToggleVisibility()
    {
        // Check the current visibility of the input field.
        bool isVisible = IPButton.gameObject.activeSelf;

        // Set the input field and secondary button to the opposite of their current state.
        IPButton.gameObject.SetActive(!isVisible);
        changeAvatarButton.gameObject.SetActive(!isVisible);
    }
}