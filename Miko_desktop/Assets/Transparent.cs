using System;
using System.Runtime.InteropServices;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;
using SatorImaging.AppWindowUtility;

public class MyTest : MonoBehaviour
{
    [DllImport("user32.dll")]
    public static extern short GetAsyncKeyState(int vKey);

    [DllImport("user32.dll")]
    private static extern bool GetCursorPos(out POINT lpPoint);

    [DllImport("user32.dll")]
    private static extern bool ScreenToClient(IntPtr hWnd, ref POINT lpPoint);

    [DllImport("user32.dll")]
    private static extern IntPtr GetActiveWindow();

    [StructLayout(LayoutKind.Sequential)]
    public struct POINT
    {
        public int X;
        public int Y;
    }

    const int VK_LCONTROL = 0xA2;
    const int VK_LMENU = 0xA4; // Left Alt key
    const int VK_B = 0x42; // B key

    [Header("UI Detection")]
    [Tooltip("UI elements to check for hover")]
    public List<RectTransform> uiElements = new List<RectTransform>();
    [Tooltip("Expand the hover detection area by this many pixels")]
    public float hoverPadding = 20f;

    private bool isTransparent = true;
    private Camera mainCamera;
    private bool bKeyWasPressed = false;
    private IntPtr windowHandle;
    private Canvas mainCanvas;

    void Start()
    {
        mainCamera = Camera.main;
        if (mainCamera == null)
        {
            mainCamera = FindObjectOfType<Camera>();
        }

        windowHandle = GetActiveWindow();
        mainCanvas = FindObjectOfType<Canvas>();

        // Auto-find UI elements if none assigned
        if (uiElements.Count == 0)
        {
            // Find all Buttons in the scene
            Button[] buttons = FindObjectsOfType<Button>(true);
            foreach (Button btn in buttons)
            {
                RectTransform rt = btn.GetComponent<RectTransform>();
                if (rt != null)
                {
                    uiElements.Add(rt);
                }
            }
        }

        //AppWindowUtility.SetKeyingColor(0, 0, 0);
        SetTransparentMode(true);
        UnityEngine.Screen.fullScreen = false;
        AppWindowUtility.FullScreen = false;
        AppWindowUtility.ClickThrough = true;
        AppWindowUtility.AlwaysOnTop = true;
    }

    void Update()
    {
        // Check for Alt+Ctrl+B to toggle background mode
        bool ctrlPressed = (GetAsyncKeyState(VK_LCONTROL) & 0x8000) != 0;
        bool altPressed = (GetAsyncKeyState(VK_LMENU) & 0x8000) != 0;
        bool bPressed = (GetAsyncKeyState(VK_B) & 0x8000) != 0;

        if (ctrlPressed && altPressed && bPressed && !bKeyWasPressed)
        {
            // Toggle between transparent and black background
            isTransparent = !isTransparent;
            SetTransparentMode(isTransparent);
            bKeyWasPressed = true;
        }
        else if (!bPressed)
        {
            bKeyWasPressed = false;
        }

        // Check if mouse is over any UI element using native mouse position
        bool isMouseOverUI = IsMouseOverUIElements();

        // Handle click-through toggle
        // Disable click-through when: Ctrl+Alt pressed OR mouse is over UI
        if (ctrlPressed && altPressed)
        {
            AppWindowUtility.ClickThrough = false;
            AppWindowUtility.AlwaysOnTop = false;
        }
        else if (isMouseOverUI)
        {
            // Mouse is over UI - disable click-through so UI can receive events
            AppWindowUtility.ClickThrough = false;
            AppWindowUtility.AlwaysOnTop = true;
        }
        else
        {
            AppWindowUtility.ClickThrough = true;
            AppWindowUtility.AlwaysOnTop = true;
        }
    }

    // Check if mouse is over any registered UI element using native Windows API
    private bool IsMouseOverUIElements()
    {
        // Get cursor position in screen coordinates
        POINT cursorPos;
        if (!GetCursorPos(out cursorPos))
        {
            return false;
        }

        // Convert to client (window) coordinates
        POINT clientPos = cursorPos;
        if (!ScreenToClient(windowHandle, ref clientPos))
        {
            return false;
        }

        // Convert to Unity screen coordinates (Y is flipped)
        Vector2 mousePos = new Vector2(clientPos.X, Screen.height - clientPos.Y);

        // Check each UI element
        foreach (RectTransform rt in uiElements)
        {
            if (rt == null || !rt.gameObject.activeInHierarchy)
                continue;

            // Get the screen rect of the UI element
            Vector3[] corners = new Vector3[4];
            rt.GetWorldCorners(corners);

            // Convert world corners to screen space
            if (mainCanvas != null && mainCanvas.renderMode == RenderMode.ScreenSpaceOverlay)
            {
                // For overlay canvas, world corners are already in screen space
            }
            else if (mainCamera != null)
            {
                for (int i = 0; i < 4; i++)
                {
                    corners[i] = mainCamera.WorldToScreenPoint(corners[i]);
                }
            }

            // Create a rect from corners (with padding)
            float minX = Mathf.Min(corners[0].x, corners[1].x, corners[2].x, corners[3].x) - hoverPadding;
            float maxX = Mathf.Max(corners[0].x, corners[1].x, corners[2].x, corners[3].x) + hoverPadding;
            float minY = Mathf.Min(corners[0].y, corners[1].y, corners[2].y, corners[3].y) - hoverPadding;
            float maxY = Mathf.Max(corners[0].y, corners[1].y, corners[2].y, corners[3].y) + hoverPadding;

            // Check if mouse is inside the rect
            if (mousePos.x >= minX && mousePos.x <= maxX && mousePos.y >= minY && mousePos.y <= maxY)
            {
                return true;
            }
        }

        return false;
    }

    private void SetTransparentMode(bool transparent)
    {
        if (transparent)
        {
            // Transparent mode
            AppWindowUtility.Transparent = true;
            if (mainCamera != null)
            {
                mainCamera.clearFlags = CameraClearFlags.SolidColor;
                mainCamera.backgroundColor = new Color(0, 0, 0, 0); // Fully transparent
            }
        }
        else
        {
            // Black background mode
            AppWindowUtility.Transparent = false;
            if (mainCamera != null)
            {
                mainCamera.clearFlags = CameraClearFlags.SolidColor;
                mainCamera.backgroundColor = Color.black; // Pure black
            }
        }
    }
}

