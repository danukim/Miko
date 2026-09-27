using UnityEngine;
using UnityEngine.UI;

public class ShowInputOnButtonClick : MonoBehaviour
{
    [Header("UI Components")]
    [SerializeField] private Button toggleButton;
    [SerializeField] private Button hideButton;
    [SerializeField] private GameObject inputField;
    
    private void Start()
    {
        // Make sure the input field is initially hidden
        if (inputField != null)
        {
            inputField.SetActive(false);
        }
        
        // Add button click listeners
        if (toggleButton != null)
        {
            toggleButton.onClick.AddListener(ToggleInputField);
        }
        
        if (hideButton != null)
        {
            hideButton.onClick.AddListener(HideInputField);
        }
    }
    
    private void ToggleInputField()
    {
        if (inputField != null)
        {
            inputField.SetActive(!inputField.activeSelf);
        }
    }
    
    private void HideInputField()
    {
        if (inputField != null)
        {
            inputField.SetActive(false);
        }
    }
    
    private void OnDestroy()
    {
        // Clean up the listeners when the object is destroyed
        if (toggleButton != null)
        {
            toggleButton.onClick.RemoveListener(ToggleInputField);
        }
        
        if (hideButton != null)
        {
            hideButton.onClick.RemoveListener(HideInputField);
        }
    }
}
