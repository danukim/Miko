using System;
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Text;

/// <summary>
/// Orbits the camera around a target based on face tracking data from the Python server.
/// Includes parallax shift for instant depth perception and servo-based vertical orbit.
/// Attach to your Main Camera and assign the target transform (your 3D model).
/// </summary>
public class CameraOrbitController : MonoBehaviour
{
    [Header("Server Configuration")]
    public string serverUrl = "http://localhost:8000";

    [Header("Orbit Settings")]
    [Tooltip("The target to orbit around (your 3D model)")]
    public Transform target;

    [Tooltip("Distance from the target")]
    public float orbitRadius = 2f;

    [Tooltip("Height offset from target's position")]
    public float heightOffset = 1.2f;

    [Tooltip("How smoothly the camera follows (higher = faster)")]
    [Range(1f, 20f)]
    public float smoothSpeed = 5f;

    [Header("Orbit Range")]
    [Tooltip("Maximum horizontal orbit angle in degrees")]
    public float maxHorizontalAngle = 360f;

    [Tooltip("Maximum vertical angle in degrees")]
    public float maxVerticalAngle = 45f;

    [Tooltip("Additional vertical angle offset (positive = higher camera)")]
    public float verticalAngleOffset = 20f;

    [Tooltip("Initial horizontal rotation offset (to fix looking at back of model)")]
    public float rotationOffset = 180f;

    [Header("Vertical Orbit Settings")]
    [Tooltip("Enable vertical orbit based on servo angle")]
    public bool enableVerticalOrbit = true;

    [Tooltip("Servo angle that maps to looking straight ahead")]
    public float servoAngleCenter = 140f;

    [Tooltip("Servo angle range (degrees from center to max tilt)")]
    public float servoAngleRange = 40f;

    [Header("Parallax Settings")]
    [Tooltip("Enable instant parallax shift based on face position")]
    public bool enableParallax = true;

    [Tooltip("Strength of horizontal parallax shift")]
    public float parallaxStrengthX = 0.3f;

    [Tooltip("Strength of vertical parallax shift")]
    public float parallaxStrengthY = 0.2f;

    [Header("Motor Tracking")]
    [Tooltip("Speed multiplier for motor-based horizontal movement")]
    public float motorOrbitSpeed = 1f;

    [Header("Debug")]
    public bool showDebugInfo = false;

    // Current and target orbit angles
    private float targetHorizontalAngle = 0f;
    private float targetVerticalAngle = 0f;
    private float currentHorizontalAngle = 0f;
    private float currentVerticalAngle = 0f;

    // Tracking data from Python
    private float motorPosition = 0f;   // Cumulative motor position (degrees)
    private float faceX = 0.5f;         // Raw face X for parallax (0-1)
    private float faceY = 0.5f;         // Raw face Y for parallax (0-1)
    private float currentFaceX = 0.5f;  // Smoothed face X
    private float currentFaceY = 0.5f;  // Smoothed face Y
    private float servoAngle = 140f;    // Servo angle for vertical orbit
    private bool faceDetected = false;

    private bool isConnected = false;

    void Start()
    {
        if (target == null)
        {
            Debug.LogError("[CameraOrbitController] No target assigned! Please assign the model to orbit around.");
            enabled = false;
            return;
        }

        // Start connection to face tracking stream
        StartCoroutine(ConnectToFaceTrackingStream());
    }

    void LateUpdate()
    {
        if (target == null) return;

        if (faceDetected)
        {
            // Horizontal angle from motor position
            targetHorizontalAngle = (motorPosition * motorOrbitSpeed) + rotationOffset;

            // Clamp removed to allow infinite rotation
            // targetHorizontalAngle = Mathf.Clamp(targetHorizontalAngle, -maxHorizontalAngle, maxHorizontalAngle);

            // Vertical orbit from servo angle (not face Y, since servo centers the face)
            if (enableVerticalOrbit)
            {
                // Map servo angle to vertical orbit angle
                // servoAngleCenter = looking straight, lower = looking up, higher = looking down
                float servoOffset = servoAngle - servoAngleCenter;
                float normalizedServo = Mathf.Clamp(servoOffset / servoAngleRange, -1f, 1f);
                // Inverted again relative to previous to fix direction (positive servo = positive angle)
                targetVerticalAngle = normalizedServo * maxVerticalAngle + verticalAngleOffset;
            }
            else
            {
                // Keep camera at fixed vertical angle
                targetVerticalAngle = verticalAngleOffset;
            }
        }

        // Smooth interpolation to target angles
        currentHorizontalAngle = Mathf.Lerp(currentHorizontalAngle, targetHorizontalAngle, smoothSpeed * Time.deltaTime);
        currentVerticalAngle = Mathf.Lerp(currentVerticalAngle, targetVerticalAngle, smoothSpeed * Time.deltaTime);

        // Calculate camera position based on orbit angles
        float horizontalRad = currentHorizontalAngle * Mathf.Deg2Rad;
        float verticalRad = currentVerticalAngle * Mathf.Deg2Rad;

        Vector3 offset = new Vector3(
            Mathf.Sin(horizontalRad) * orbitRadius * Mathf.Cos(verticalRad),
            Mathf.Sin(verticalRad) * orbitRadius + heightOffset,
            -Mathf.Cos(horizontalRad) * orbitRadius * Mathf.Cos(verticalRad)
        );

        Vector3 orbitPosition = target.position + offset;

        // Apply parallax shift (smoothed)
        if (enableParallax && faceDetected)
        {
            // Smoothly interpolate face position
            currentFaceX = Mathf.Lerp(currentFaceX, faceX, smoothSpeed * Time.deltaTime);
            currentFaceY = Mathf.Lerp(currentFaceY, faceY, smoothSpeed * Time.deltaTime);

            // Calculate camera's right and up vectors for local offset
            Vector3 toTarget = (target.position + Vector3.up * heightOffset) - orbitPosition;
            Vector3 forward = toTarget.normalized;
            Vector3 right = Vector3.Cross(Vector3.up, forward).normalized;
            Vector3 up = Vector3.Cross(forward, right).normalized;

            // Apply parallax offset based on face position
            // REVERSED X direction as requested: -(faceX - 0.5)
            float parallaxOffsetX = -(currentFaceX - 0.5f) * parallaxStrengthX;
            float parallaxOffsetY = (currentFaceY - 0.5f) * parallaxStrengthY;

            orbitPosition += right * parallaxOffsetX;
            orbitPosition += up * -parallaxOffsetY; // Invert Y: face up = camera offset down
        }

        transform.position = orbitPosition;
        transform.LookAt(target.position + Vector3.up * heightOffset);
    }

    IEnumerator ConnectToFaceTrackingStream()
    {
        string streamUrl = serverUrl + "/audio_stream"; // Uses existing stream endpoint

        using (UnityWebRequest request = UnityWebRequest.Get(streamUrl))
        {
            request.downloadHandler = new FaceTrackingDownloadHandler(this);

            Debug.Log($"📷 Connecting to face tracking stream: {streamUrl}");

            var operation = request.SendWebRequest();

            while (!operation.isDone)
            {
                yield return null;
            }

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError($"❌ Failed to connect to face tracking stream: {request.error}");
                // Retry connection after 5 seconds
                yield return new WaitForSeconds(5f);
                StartCoroutine(ConnectToFaceTrackingStream());
            }
        }
    }

    /// <summary>
    /// Called by the download handler when face position data is received
    /// </summary>
    public void OnFacePositionReceived(float motorPos, float x, float y, float servo, bool detected)
    {
        motorPosition = motorPos;
        faceX = x;
        faceY = y;
        servoAngle = servo;
        faceDetected = detected;

        if (showDebugInfo)
        {
            Debug.Log($"📷 Motor={motorPosition:F1}°, FaceX={x:F2}, FaceY={y:F2}, Servo={servo:F1}°, Detected={detected}");
        }
    }

    /// <summary>
    /// Resets the motor position to center (call when you want to re-center)
    /// </summary>
    public void ResetMotorPosition()
    {
        motorPosition = 0f;
        currentHorizontalAngle = 0f;
        targetHorizontalAngle = 0f;
    }

    void OnGUI()
    {
        if (showDebugInfo)
        {
            GUILayout.BeginArea(new Rect(10, 10, 300, 200));
            GUILayout.Label($"Motor Position: {motorPosition:F1}°");
            GUILayout.Label($"Face X: {faceX:F2}");
            GUILayout.Label($"Face Y: {faceY:F2}");
            GUILayout.Label($"Servo Angle: {servoAngle:F1}°");
            GUILayout.Label($"Face Detected: {faceDetected}");
            GUILayout.Label($"H Angle: {currentHorizontalAngle:F1}°");
            GUILayout.Label($"V Angle: {currentVerticalAngle:F1}°");
            GUILayout.Label($"Parallax: {enableParallax}, V-Orbit: {enableVerticalOrbit}");
            GUILayout.EndArea();
        }
    }
}

/// <summary>
/// Custom download handler for streaming face tracking data
/// </summary>
public class FaceTrackingDownloadHandler : DownloadHandlerScript
{
    private CameraOrbitController controller;
    private StringBuilder messageBuffer = new StringBuilder();

    [Serializable]
    private class FaceMessage
    {
        public string type;
        public float motor_position;  // Cumulative motor angle in degrees
        public float x;               // Raw face X for parallax (0-1)
        public float y;               // Raw face Y for parallax (0-1)
        public float servo_angle;     // Servo angle for vertical orbit
        public bool detected;
    }

    public FaceTrackingDownloadHandler(CameraOrbitController controller) : base()
    {
        this.controller = controller;
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
                    ProcessMessage(message);
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
            Debug.LogError($"❌ Error receiving face tracking data: {e.Message}");
            return false;
        }
    }

    private void ProcessMessage(string jsonMessage)
    {
        try
        {
            // Check if it's a face position message
            if (jsonMessage.Contains("\"type\":\"face_position\"") || jsonMessage.Contains("\"type\": \"face_position\""))
            {
                FaceMessage msg = JsonUtility.FromJson<FaceMessage>(jsonMessage);
                if (msg != null && msg.type == "face_position")
                {
                    controller.OnFacePositionReceived(msg.motor_position, msg.x, msg.y, msg.servo_angle, msg.detected);
                }
            }
            // Ignore other message types (audio, animation, etc.)
        }
        catch (Exception e)
        {
            // Silently ignore parse errors for non-face messages
            if (jsonMessage.Contains("face_position"))
            {
                Debug.LogWarning($"⚠️ Failed to parse face message: {e.Message}");
            }
        }
    }
}