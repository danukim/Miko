using System;
using System.Runtime.InteropServices;
using UnityEngine;
using SatorImaging.AppWindowUtility;

public class WindowResizer : MonoBehaviour
{
    [DllImport("user32.dll")]
    public static extern short GetAsyncKeyState(int vKey);

    [DllImport("user32.dll")]
    private static extern IntPtr GetActiveWindow();

    [DllImport("user32.dll")]
    private static extern bool GetWindowRect(IntPtr hwnd, out RECT lpRect);

    [DllImport("user32.dll")]
    private static extern bool SetWindowPos(IntPtr hWnd, int hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);

    [DllImport("user32.dll")]
    private static extern bool MoveWindow(IntPtr hWnd, int X, int Y, int nWidth, int nHeight, bool bRepaint);

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT
    {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    const int VK_LMENU = 0xA4; // Left Alt key
    const int VK_LCONTROL = 0xA2; // Left Ctrl key
    const int HWND_TOPMOST = -1; // Keep window always on top
    const uint SWP_NOACTIVATE = 0x0010;
    const uint SWP_SHOWWINDOW = 0x0040;

    [Header("Resize Settings")]
    [SerializeField] private float scrollSensitivity = 50f;
    [SerializeField] private int minWidth = 400;
    [SerializeField] private int minHeight = 300;
    [SerializeField] private int maxWidth = 3840;
    [SerializeField] private int maxHeight = 2160;
    [SerializeField] private bool maintainAspectRatio = false;

    private IntPtr windowHandle;
    private float aspectRatio;
    private bool isLeftAltPressed = false;
    private bool isLeftCtrlPressed = false;
    private Camera mainCamera;

    void Start()
    {
        windowHandle = GetActiveWindow();
        mainCamera = Camera.main;
        if (mainCamera == null)
        {
            mainCamera = FindObjectOfType<Camera>();
        }
        
        // Calculate initial aspect ratio
        if (maintainAspectRatio)
        {
            aspectRatio = (float)Screen.width / Screen.height;
        }
    }

    void Update()
    {
        // Check if Left Alt and Left Ctrl are pressed
        isLeftAltPressed = (GetAsyncKeyState(VK_LMENU) & 0x8000) != 0;
        isLeftCtrlPressed = (GetAsyncKeyState(VK_LCONTROL) & 0x8000) != 0;

        // Only allow resizing when Left Alt + Left Ctrl are held
        if (isLeftAltPressed && isLeftCtrlPressed)
        {
            // Get mouse scroll input
            float scroll = Input.mouseScrollDelta.y;

            if (Mathf.Abs(scroll) > 0.01f)
            {
                ResizeWindow(scroll);
            }
        }
    }

    private void ResizeWindow(float scrollDelta)
    {
        RECT rect;
        if (!GetWindowRect(windowHandle, out rect))
        {
            Debug.LogWarning("Failed to get window rect");
            return;
        }

        int currentWidth = rect.Right - rect.Left;
        int currentHeight = rect.Bottom - rect.Top;

        // Calculate new size based on scroll
        int widthChange = (int)(scrollDelta * scrollSensitivity);
        int heightChange = widthChange;

        if (maintainAspectRatio)
        {
            heightChange = (int)(widthChange / aspectRatio);
        }

        int newWidth = Mathf.Clamp(currentWidth + widthChange, minWidth, maxWidth);
        int newHeight = Mathf.Clamp(currentHeight + heightChange, minHeight, maxHeight);

        // Calculate center position to resize from center
        int centerX = rect.Left + currentWidth / 2;
        int centerY = rect.Top + currentHeight / 2;

        int newLeft = centerX - newWidth / 2;
        int newTop = centerY - newHeight / 2;

        // Set new window position and size, keeping it always on top
        // We do NOT call Screen.SetResolution as it destroys transparency
        SetWindowPos(windowHandle, HWND_TOPMOST, newLeft, newTop, newWidth, newHeight, SWP_NOACTIVATE | SWP_SHOWWINDOW);
    }
}

